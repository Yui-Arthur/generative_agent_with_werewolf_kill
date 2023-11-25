from .long_memory_stream import long_memeory_stream

import json

class role(long_memeory_stream):

    def __init__(self , prompt_dir , logger , client , openai_kwargs  , summary=False ,  log_prompt = False):
        super().__init__(prompt_dir, logger , client, openai_kwargs  , summary , log_prompt)
        self.max_fail_cnt = 3
        
    def __processs_information__(self , data):
        return super().__process_information__(data)
        
    def __load_prompt_and_example__(self , prompt_dir):
        """load prompt json to dict"""
        super().__load_prompt_and_example__(prompt_dir)

        self.logger.debug(f"load {self.role} json")
        with open(prompt_dir / f"{self.role}_prompt.json" , encoding="utf-8") as json_file: prompt_template = json.load(json_file)
        with open(prompt_dir / f"{self.role}_example.json" , encoding="utf-8") as json_file: example = json.load(json_file)
        
        for key , prompt_li in prompt_template.items():
            self.prompt_template[key] = '\n'.join(prompt_li)
        for key , prompt_li in example.items():
            self.example[key] = '\n'.join(prompt_li)

class werewolf(role):

    def __init__(self , prompt_dir , logger , client , openai_kwargs , summary=False , log_prompt = False):
        super().__init__(prompt_dir, logger , client, openai_kwargs  , summary , log_prompt)
        self.werewolf_chat = ""
        self.personal_chat = ""
        self.__register_keywords__({
            "回答" : "answer"
        })
        # self.max_fail_cnt = 0

    def update_game_info(self , player_id , player_name , role , roles_setting ,teamate):
        super().update_game_info(player_id , player_name , role , roles_setting)
        
        self.teamate = teamate
        self.push('0' , len(self.memory_stream) , self.__teamate_to_str__() , default_importantance=10)
        

    def __day_init__(self):
        super().__day_init__()
        self.werewolf_chat = ""
        self.personal_chat = ""

    def __process_information__(self , data):
        operation = super().__process_information__(data)
        if len(data["information"]) == 0:
            return operation
        
        self.logger.debug("werewolf process")
        # werewolf dialogue 
        if data['stage'].split('-')[-1] == "werewolf_dialogue":
            # if you are the first dialogue wolf
            replace_order = {
                "%wi" : self.werewolf_chat if self.werewolf_chat != "" else "無\n",
                "%l" : self.__role_list_to_str__()[0],
                "%e" : self.example['werewolf_dialogue'],
                "%s" : self.__summary_to_str__()
            }
            final_prompt = self.prompt_template['werewolf_dialogue']
            for key , item in replace_order.items() : final_prompt = final_prompt.replace(key , item)
            
            info = {
                "answer" : "順從隊友",
                "reason" : "test",
            }
            info = self.__process_LLM_output__(final_prompt , {'answer' : str , 'reason' : str} , info , "werewolf dialogue")
            self.personal_chat = f"您自己說「{info['answer']}。」"
            ret = self.ret_format.copy()
            ret['operation'] = "werewolf_dialogue"
            ret['target'] = self.teamate[0]
            ret['chat'] = info['answer']
            operation.append(ret)

        # werewolf kill
        elif data['stage'].split('-')[-1] == "werewolf":
            target = data['information'][0]['target']
   
            replace_order = {
                "%wi" : self.werewolf_chat if self.werewolf_chat != "" else "無\n",
                "%l" : self.__role_list_to_str__()[0],
                "%si" : self.personal_chat,
                "%t" : "、".join([str(_) for _ in target]),
                "%e" : self.example['werewolf_kill'],
                "%s" : self.__summary_to_str__()
            }
            final_prompt = self.prompt_template['werewolf_kill']
            for key , item in replace_order.items() : final_prompt = final_prompt.replace(key , item)

            info = {
                "answer" : 4,
                "reason" : "test",
            }
            info = self.__process_LLM_output__(final_prompt , {'answer':int , 'reason' : str} , info , "werewolf kill")
            ret = self.ret_format.copy()
            ret['operation'] = "vote"
            ret['target'] = info["answer"]
            ret['chat'] = ""
            operation.append(ret)

        return operation


    def __process_announcement__(self, data):
        super().__process_announcement__(data)
        announcement = data['announcement']

        for anno in announcement:
            # got other wolf's chat 
            if "werewolf" in data['stage'].split('-')[-1] and anno['operation'] == 'chat' and anno['user'][0] != self.player_id:
                self.werewolf_chat += f"{anno['user'][0]}號玩家({self.player_name[anno['user'][0]]})說「{anno['description']}」\n"
                self.logger.debug(f"add werewolf chat : {anno['description']}")

        return

    def __teamate_to_str__(self):
        teamate_str = ""
        for player in self.teamate:
            teamate_str+= f"{player}號玩家({self.player_name[int(player)]})"
            if player != self.teamate[-1]: teamate_str+="與"
        return  f"{teamate_str}為你的狼人隊友"


class seer(role):
    def __init__(self , prompt_dir , logger , client , openai_kwargs  , summary=False , log_prompt = False):
        super().__init__(prompt_dir, logger , client, openai_kwargs , summary , log_prompt)
        
        self.__register_keywords__({
            "目標" : "target"
        })
        # self.max_fail_cnt = 3
    
    def __process_information__(self , data):
        operation = super().__process_information__(data)
        if len(data["information"]) == 0 or data['stage'].split('-')[-1] != "seer":
            return operation
        
        question = self.__reflection_question__(self.day , len(self.memory_stream))
        memory = self.__retrieval__(self.day , len(self.memory_stream) , question)
        target = data['information'][0]['target']
        
        replace_order = {
            "%l" : self.__role_list_to_str__()[0],
            "%m" : self.__memory_to_str__(memory),
            "%t" : "、".join([str(_) for _ in target if _ != self.player_id]),
            "%e" : self.example['check_role'],
            "%s" : self.__summary_to_str__(),
            "%rs" : self.__roles_setting_to_str__(),
        }
        final_prompt = self.prompt_template['check_role']
        for key , item in replace_order.items() : final_prompt = final_prompt.replace(key , item)

        info = {
            "target" : 1,
            "reason" : "test"
        }

        info = self.__process_LLM_output__(final_prompt , {'target' : int , 'reason' : str} , info , "seer")

        ret = self.ret_format.copy()
        ret['operation'] = "vote"
        ret['target'] = info['target']
        ret['chat'] = ""
        operation.append(ret)
        return operation

    def __process_announcement__(self, data):
        super().__process_announcement__(data)
        announcement = data['announcement']

        for anno in announcement:
            if anno['operation'] == 'role_info':
                
                role_type = anno['description'].split('是')[-1]
                
                self.know_role_list[int(anno['user'][0])] = role_type
                self.push(self.day , len(self.memory_stream) , f"您的查驗結果:「{anno['user'][0]}號玩家({self.player_name[anno['user'][0]]})是{role_type}」" , default_importantance=10)
                self.logger.debug(f"add role info : {anno['user'][0]}號玩家({self.player_name[anno['user'][0]]})是{role_type} ")

        return

class witch(role):
    
    def __init__(self , prompt_dir , logger , client , openai_kwargs , summary=False, log_prompt=False):
        super().__init__(prompt_dir, logger , client, openai_kwargs , summary , log_prompt)
        
        self.__register_keywords__({
            "選擇一位玩家" : "target",
            "今晚要救人還是毒人" : "save_or_poison",
        })

        # self.max_fail_cnt = 0
        # self.save = True
        # self.poison = True

    def __process_information__(self , data):

        operation = super().__process_information__(data)
        if len(data["information"]) == 0 or data['stage'].split('-')[-1] != "witch":
            return operation

        self.logger.debug(f"witch process")
        memory = self.__retrieval__(self.day , len(self.memory_stream) , "該救或毒哪位玩家")

        save_posion = ""
        save_list = "無"
        posion_list = "無"

        # both save & posion not used 
        if len(data['information'])==2:
            target = data['information'][0]['target']
            save_list = "、".join([str(_) for _ in target])

            target = data['information'][1]['target']
            posion_list = "、".join([str(_) for _ in target if _ != self.player_id])

            save_posion = ""
        # remain posion
        elif data['information'][0]['description'] == '女巫毒人':
            target = data['information'][0]['target']
            posion_list = "、".join([str(_) for _ in target if _ != self.player_id])
            save_posion = "解藥已用完，"
        # remain save
        else:
            target = data['information'][0]['target']
            save_list = "、".join([str(_) for _ in target])
            save_posion = "解藥已用完，"
        
        replace_order = {
            "%l" : self.__role_list_to_str__()[0],
            "%m" : self.__memory_to_str__(memory),
            "%vl" : save_list,
            "%pl" : posion_list,
            "%sl" : save_posion,
            "%t" : "、".join([str(_) for _ in target if _ != self.player_id]),
            "%e" : self.example['save_poison'],
            "%s" : self.__summary_to_str__(),
            "%rs" : self.__roles_setting_to_str__(),
        }
        final_prompt = self.prompt_template['save_poison']
        for key , item in replace_order.items() : final_prompt = final_prompt.replace(key , item)

        info = {
            "save_or_poison" : "救人",
            "target": 1,
            "reason": "test"
        }
        info = self.__process_LLM_output__(final_prompt , {'save_or_poison' : str, 'target' : int, 'reason' : str} , info , 3)

        ret = self.ret_format.copy()
        ret['operation'] = "vote_or_not"
        ret['target'] = info['target']

        if info['save_or_poison'].strip("\n") == "救人":
            self.push(self.day , len(self.memory_stream) , f"您({self.player_name[self.player_id]})用解藥救了{ret['target']}號玩家({self.player_name[ret['target']]})" , default_importantance=10)
            ret['chat'] = 'save'
            operation.append(ret)
        elif info['save_or_poison'].strip("\n") == "毒人":
            self.push(self.day , len(self.memory_stream) , f"您({self.player_name[self.player_id]})用毒藥毒了{ret['target']}號玩家({self.player_name[ret['target']]})", default_importantance=10)
            ret['chat'] = 'poison'
            operation.append(ret)

        return operation


class hunter(role):
    def __init__(self , prompt_dir , logger , client , openai_kwargs , summary=False , log_prompt=False):
        super().__init__(prompt_dir, logger , client, openai_kwargs , summary , log_prompt)
        
        self.__register_keywords__({
            "選擇要獵殺的對象" : "target"
        })
        # self.max_fail_cnt = 0
    
    def __process_information__(self , data):

        operation = super().__process_information__(data)
        if len(data["information"]) == 0 or data['stage'].split('-')[-1] != "hunter":
            return operation
        
        self.logger.debug("hunter process")
        memory = self.__retrieval__(self.day , len(self.memory_stream) , "目前哪位玩家最可疑")
        target = data['information'][1]['target']

        replace_order = {
            "%l" : self.__role_list_to_str__()[0],
            "%m" : self.__memory_to_str__(memory),
            "%t" : "、".join([str(_) for _ in target if _ != self.player_id]),
            "%e" : self.example['hunter'],
            "%rs" : self.__roles_setting_to_str__(),
        }
        final_prompt = self.prompt_template['hunter']
        for key , item in replace_order.items() : final_prompt = final_prompt.replace(key , item)

        info = {
            "target" : 1,
            "reason" : "test"
        }
        
        info = self.__process_LLM_output__(final_prompt , {'target' : int , 'reason' :str} , info , "hunter")

        ret = self.ret_format.copy()
        ret['operation'] = "vote_or_not"
        ret['target'] = info['target']
        ret['chat'] = ""
        operation.append(ret)

        return operation