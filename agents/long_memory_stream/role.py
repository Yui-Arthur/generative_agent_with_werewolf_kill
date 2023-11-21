from .long_memory_stream import long_memeory_stream

import json

class role(long_memeory_stream):

    def __init__(self , prompt_dir , logger , client , openai_kwargs):
        super().__init__(prompt_dir, logger , client, openai_kwargs)
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

    def __player_list_to_str__(self, datas):
        """
        export the {save_list} and {posion_list} to string like
        1號玩家(Yui1), 2號玩家(Yui2), 3號玩家(Yui3)
        """
        name_list = ""
        for data in datas:
            name_list += f"{data}號玩家({self.player_name[data]}), "
    
        return name_list

class werewolf(role):

    def __init__(self , prompt_dir , logger , client , openai_kwargs):
        super().__init__(prompt_dir, logger , client, openai_kwargs)
        self.werewolf_chat = ""
        self.personal_chat = ""
        self.__register_keywords__({
            "回答" : "answer"
        })
        # self.max_fail_cnt = 0

    def update_game_info(self , player_id , player_name , role ,teamate):
        super().update_game_info(player_id , player_name , role)
        
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
            sus_role_str , know_role_str = self.__role_list_to_str__()
            # if you are the first dialogue wolf
            werewolf_chat = self.werewolf_chat if self.werewolf_chat != "" else "無\n"
            final_prompt = self.prompt_template['werewolf_dialogue'].replace("%e" , self.example['werewolf_dialogue']).replace("%wi" , werewolf_chat).replace("%l" , sus_role_str)
            
            self.logger.debug(final_prompt)
            info = {
                "answer" : "1. 順從隊友",
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
            target_to_str = "、".join([str(_) for _ in target if _ != self.player_id])
            sus_role_str , know_role_str = self.__role_list_to_str__()
            final_prompt = self.prompt_template['werewolf_kill'].replace("%e" , self.example['werewolf_kill']).replace("%wi" , self.werewolf_chat).replace("%l" , sus_role_str).replace("%si" , self.personal_chat).replace("%t" , target_to_str)
            self.logger.debug(final_prompt)
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
    def __init__(self , prompt_dir , logger , client , openai_kwargs):
        super().__init__(prompt_dir, logger , client, openai_kwargs)
        
        self.__register_keywords__({
            "今晚要驗誰" : "target"
        })
        # self.max_fail_cnt = 3
    
    def __process_information__(self , data):
        operation = super().__process_information__(data)
        if len(data["information"]) == 0 or data['stage'].split('-')[-1] != "seer":
            return operation

        memory = self.__retrieval__(self.day , len(self.memory_stream) , "目前哪位玩家最可疑")
        memory_str = self.__memory_to_str__(memory)
        sus_role_str , know_role_str = self.__role_list_to_str__()


        final_prompt = self.prompt_template['check_role'].replace("%e" , self.example['check_role']).replace("%l" , sus_role_str).replace("%kl" , know_role_str).replace("%m" , memory_str)

        info = {
            "target" : "1",
            "reason" : "test"
        }

        info = self.__process_LLM_output__(final_prompt , ['target' , 'reason'] , info , 3)

        ret = self.ret_format.copy()
        ret['operation'] = "vote"
        ret['target'] = int(info['target'].strip("\n"))
        ret['chat'] = ""
        operation.append(ret)
        return operation

    def __process_announcement__(self, data):
        super().__process_announcement__(data)
        announcement = data['announcement']

        for anno in announcement:
            if anno['operation'] == 'role_info':
                print(anno)
                role_type = anno['description'].split('是')[-1]
                
                self.know_role_list[int(anno['user'][0])] = role_type
                self.push(self.day , len(self.memory_stream) + 1 , f"{anno['user'][0]}號玩家({self.player_name[anno['user'][0]]})是{role_type}")
                self.logger.debug(f"add role info : {anno['user'][0]}號玩家({self.player_name[anno['user'][0]]})是{role_type} ")

        return

class witch(role):
    
    def __init__(self , prompt_dir , logger , client , openai_kwargs):
        super().__init__(prompt_dir, logger , client, openai_kwargs)
        
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
        sus_role_str , know_role_str = self.__role_list_to_str__()
        memory = self.__retrieval__(self.day , len(self.memory_stream) , "該救或毒哪位玩家")
        memory_str = self.__memory_to_str__(memory)

        save_posion = "毒藥已用完，"
        save_list = self.__player_list_to_str__(data['information'][0]['target'])
        if len(data['information'])==2:
            posion_list = self.__player_list_to_str__(data['information'][1]['target'])
            save_posion = ""
        elif data['information'][0]['description'] == '女巫毒人':
            save_list = []
            posion_list = self.__player_list_to_str__(data['information'][0]['target'])
            save_posion = "解藥已用完，"

        final_prompt = self.prompt_template['save_poison'].replace("%e" , self.example['save_poison']).replace("%l" , sus_role_str).replace("%kl" , know_role_str).replace("%m", memory_str).replace("%vl", save_list).replace("%pl", posion_list).replace("%s" , save_posion)
    
        info = {
            "save_or_poison" : "救人",
            "target": "1",
            "reason": "test"
        }
        info = self.__process_LLM_output__(final_prompt , ['save_or_poison', 'target', 'reason'] , info , 3)

        ret = self.ret_format.copy()
        ret['operation'] = "vote_or_not"
        ret['target'] = int(info['target'].strip("\n"))

        if info['save_or_poison'].strip("\n") == "救人":
            self.push(self.day , len(self.memory_stream)+1 , f"你用解藥救了{ret['target']}號玩家({self.player_name[ret['target']]})")
            ret['chat'] = 'save'
            operation.append(ret)
        elif info['save_or_poison'].strip("\n") == "毒人":
            self.push(self.day , len(self.memory_stream)+1 , f"你用毒藥毒了{ret['target']}號玩家({self.player_name[ret['target']]})")
            ret['chat'] = 'poison'
            operation.append(ret)

        return operation


class hunter(role):
    def __init__(self , prompt_dir , logger , client , openai_kwargs):
        super().__init__(prompt_dir, logger , client, openai_kwargs)
        
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
        memory_str = self.__memory_to_str__(memory)
        sus_role_str , know_role_str = self.__role_list_to_str__()
        final_prompt = self.prompt_template['hunter'].replace("%e" , self.example['hunter']).replace("%l" , sus_role_str).replace("%kl" , know_role_str).replace("%m" , memory_str)

        info = {
            "target" : "1",
            "reason" : "test"
        }
        
        info = self.__process_LLM_output__(final_prompt , ['target' , 'reason'] , info , 3)

        ret = self.ret_format.copy()
        ret['operation'] = "vote_or_not"
        ret['target'] = int(info['target'].strip("\n"))
        ret['chat'] = ""
        operation.append(ret)

        return operation