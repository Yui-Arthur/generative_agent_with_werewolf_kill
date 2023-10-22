from .long_memory_stream import long_memeory_stream

import json

class role(long_memeory_stream):

    def __init__(self , prompt_dir , logger , gpt_agent , sentence_model = None):
        super().__init__(prompt_dir, logger , gpt_agent , sentence_model)
        
    def __processs_information__(self , data):
        return super().__process_information__(data)
        
    def __load_prompt_and_example__(self , prompt_dir):
        """load prompt json to dict"""
        super().__load_prompt_and_example__(prompt_dir)

        self.logger.debug(f"load {self.role} json")
        with open(prompt_dir / f"{self.role}_prompt.json" , encoding="utf-8") as json_file: self.prompt_template.update(json.load(json_file))
        with open(prompt_dir / f"{self.role}_example.json" , encoding="utf-8") as json_file: self.example.update(json.load(json_file))
        
        for key , prompt_li in self.prompt_template.items():
            self.prompt_template[key] = '\n'.join(prompt_li)
        for key , prompt_li in self.example.items():
            self.example[key] = '\n'.join(prompt_li)

class werewolf(role):

    def __init__(self , prompt_dir , logger , gpt_agent , sentence_model = None):
        super().__init__(prompt_dir, logger , gpt_agent , sentence_model)
        self.werewolf_chat = ""
        self.personal_chat = ""
        self.__register_keywords__({
            "回答" : "answer"
        })
        self.max_fail_cnt = 0

    def update_game_info(self , player_name , role , teamate):
        super().update_game_info(player_name , role)
        
        self.teamate = teamate
        self.push(0 , 1 , self.__teamate_to_str__())
        

    def __day_init__(self):
        super().__day_init__()
        self.werewolf_chat = ""

    def __process_information__(self , data):
        operation = super().__process_information__(data)
        if len(data["information"]) == 0:
            return operation
        
        self.logger.debug("werewolf process")
        # werewolf dialogue 
        if data['stage'].split('-')[-1] == "werewolf_dialogue":
            sus_role_str , know_role_str = self.__role_list_to_str__()
            # teamate_str = self.__teamate_to_str__()
            final_prompt = self.prompt_template['werewolf_dialogue'].replace("%e" , self.example['werewolf_dialogue']).replace("%wi" , self.werewolf_chat).replace("%l" , sus_role_str).replace("%kl" , know_role_str)
            # print(final_prompt)
            info = {
                "answer" : "1. 順從隊友",
                "reason" : "test",
            }
            info = self.__process_LLM_output__(final_prompt , ['answer' , 'reason'] , info , 3)
            ret = self.ret_format.copy()
            ret['operation'] = "werewolf_dialogue"
            ret['target'] = self.teamate
            ret['chat'] = "test"
            operation.append(ret)

        # werewolf kill
        elif data['stage'].split('-')[-1] == "werewolf":
            sus_role_str , know_role_str = self.__role_list_to_str__()
            final_prompt = self.prompt_template['werewolf_kill'].replace("%e" , self.example['werewolf_kill']).replace("%wi" , self.werewolf_chat).replace("%l" , sus_role_str).replace("%kl" , know_role_str).replace("%si" , self.personal_chat)
            # print(final_prompt)
            info = {
                "answer" : "今晚殺4號玩家",
                "reason" : "test",
            }
            info = self.__process_LLM_output__(final_prompt , ['answer' , 'reason'] , info , 3)
            ret = self.ret_format.copy()
            ret['operation'] = "vote"
            ret['target'] = 1
            ret['chat'] = ""
            operation.append(ret)

        return operation


    def __process_announcement__(self, data):
        super().__process_announcement__(data)
        announcement = data['announcement']

        for anno in announcement:
            if "werewolf" in data['stage'].split('-')[-1] and anno['operation'] == 'chat':
                self.werewolf_chat += anno['description']
                self.logger.debug(f"add werewolf chat : {anno['description']}")

        return

    def __teamate_to_str__(self):
        teamate_str = ""
        for player in self.teamate:
            teamate_str+= f"{player}號玩家({self.player_name[int(player)]})"
            if player != self.teamate[-1]: teamate_str+="與"
        return  f"您本場的狼人隊友為{teamate_str}"


class seer(role):
    def __init__(self , prompt_dir , logger , gpt_agent , sentence_model = None):
        super().__init__(prompt_dir, logger , gpt_agent , sentence_model)
        
        self.__register_keywords__({
            "今晚要驗誰" : "target"
        })
        self.max_fail_cnt = 1
    
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
    
    def __init__(self , prompt_dir , logger , gpt_agent , sentence_model = None):
        super().__init__(prompt_dir, logger , gpt_agent , sentence_model)
        
        self.__register_keywords__({
            "選擇一位玩家" : "target",
            "今晚要救人還是毒人" : "save_or_poison",
        })

        self.max_fail_cnt = 3
        self.save = True
        self.poison = True

    def __process_information__(self , data):

        operation = super().__process_information__(data)
        if len(data["information"]) == 0 or data['stage'].split('-')[-1] != "witch":
            return operation

        self.logger.debug(f"witch process")
        sus_role_str , know_role_str = self.__role_list_to_str__()
        
        if data['information'][0]['description'] == '女巫救人':
            self.push(self.day , 0 , f"{data['information'][0]['target']}號玩家今晚被殺了 你要救他嗎")

        final_prompt = self.prompt_template['save_poison'].replace("%e" , self.example['save_poison']).replace("%l" , sus_role_str).replace("%kl" , know_role_str).replace("%m" , self.__memory_to_str__(self.memory_stream)).replace("%p", str())
        if self.save==True and self.poison==False :
            final_prompt = final_prompt.replace("%s" , "毒藥已用完")
        elif self.save==False and self.poison==True :
            final_prompt = final_prompt.replace("%s" , "解藥已用完")
        else:
            final_prompt = final_prompt.replace("%s" , "")

        info = {
            "save_or_poison" : "save",
            "target": "1",
            "reason": "test"
        }
        info = self.__process_LLM_output__(final_prompt , ['save_or_poison', 'target', 'reason'] , info , 3)

        ret = self.ret_format.copy()
        ret['operation'] = "vote_or_not"
        ret['target'] = int(info['target'].strip("\n"))

        if info['save_or_poison'].strip("\n") == "救人":
            self.push(self.day , 0 , f"你用解藥救了{data['information'][0]['target']}號玩家")
            ret['chat'] = 'save'
            self.save = False

        elif info['save_or_poison'].strip("\n") == "毒人":
            ret['chat'] = 'poison'
            self.poison = False

        else:
            return operation


        operation.append(ret)

        return operation


class hunter(role):
    def __init__(self , prompt_dir , logger , sentence_model = None):
        super().__init__(prompt_dir, logger , sentence_model)
        
        self.__register_keywords__({
            "選擇要獵殺的對象" : "target"
        })
        self.max_fail_cnt = 1
    
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