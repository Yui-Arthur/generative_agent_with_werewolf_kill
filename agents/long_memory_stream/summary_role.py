from .long_memory_stream import long_memeory_stream

import json

class summary_role(long_memeory_stream):

    def __init__(self , prompt_dir , logger , openai_kwargs ):
        super().__init__(prompt_dir, logger , openai_kwargs)
        self.max_fail_cnt = 1
        self.stage_summary = None
        self.guess_summary = None
        
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
    
    def update_stage(self , data):

        self.stage_summary = data["stage_summary"]
        self.guess_summary = data["guess_summary"]

        if self.day != data['stage'].split('-')[0]:
            self.day = data['stage'].split('-')[0]
            self.__day_init__()


        if any(data["vote_info"].values()) :
            self.__push_vote_info__(data["vote_info"] , data["stage"])

        self.__process_announcement__(data)
        operations = self.__process_information__(data)
        for op in operations:
            op['stage_name'] = data['stage']

        return operations
    
    def summary_prompt(self, pre_prompt):

        experience = ""
        for idx, summary in enumerate(self.stage_summary):
            experience += f'{idx+1}. {summary}\n'

        final_prompt = self.prompt_template['experience'].replace("%e" , experience).replace("%e" , self.guess_summary)
    
        return f"{pre_prompt}\n{final_prompt}"


class summary_werewolf(summary_role):

    def __init__(self , prompt_dir , logger , openai_kwargs):
        super().__init__(prompt_dir, logger , openai_kwargs)
        self.werewolf_chat = ""
        self.personal_chat = ""
        self.__register_keywords__({
            "回答" : "answer"
        })
        # self.max_fail_cnt = 0

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
            final_prompt = self.prompt_template['werewolf_dialogue'].replace("%e" , self.example['werewolf_dialogue']).replace("%wi" , self.summary_prompt(self.werewolf_chat)).replace("%l" , sus_role_str).replace("%kl" , know_role_str)
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
            final_prompt = self.prompt_template['werewolf_kill'].replace("%e" , self.example['werewolf_kill']).replace("%wi" , self.werewolf_chat).replace("%l" , sus_role_str).replace("%kl" , know_role_str).replace("%si" , self.summary_prompt(self.personal_chat))
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


class summary_seer(summary_role):
    def __init__(self , prompt_dir , logger , openai_kwargs):
        super().__init__(prompt_dir, logger , openai_kwargs)
        
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


        final_prompt = self.prompt_template['check_role'].replace("%e" , self.example['check_role']).replace("%l" , sus_role_str).replace("%kl" , know_role_str).replace("%m" , self.summary_prompt(memory_str))

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

class summary_witch(summary_role):
    
    def __init__(self , prompt_dir , logger , openai_kwargs):
        super().__init__(prompt_dir, logger , openai_kwargs)
        
        self.__register_keywords__({
            "選擇一位玩家" : "target",
            "今晚要救人還是毒人" : "save_or_poison",
        })

        self.max_fail_cnt = 3

    def __process_information__(self , data):

        operation = super().__process_information__(data)
        if len(data["information"]) == 0 or data['stage'].split('-')[-1] != "witch":
            return operation

        self.logger.debug(f"witch process")
        sus_role_str , know_role_str = self.__role_list_to_str__()
        memory = self.__retrieval__(self.day , len(self.memory_stream) , "該救或毒哪位玩家")
        memory_str = self.__memory_to_str__(memory)
        # memory_str = self.__memory_to_str__(self.memory_stream)

        save_posion = "毒藥已用完，"
        save_list = self.__player_list_to_str__(data['information'][0]['target'])
        posion_list = ""
        if len(data['information'])==2:
            posion_list = self.__player_list_to_str__(data['information'][1]['target'])
            save_posion = ""
        elif data['information'][0]['description'] == '女巫毒人':
            save_list = ""
            posion_list = self.__player_list_to_str__(data['information'][0]['target'])
            save_posion = "解藥已用完，"

        final_prompt = self.prompt_template['save_poison'].replace("%e" , self.example['save_poison']).replace("%l" , sus_role_str).replace("%kl" , know_role_str).replace("%m", self.summary_prompt(memory_str)).replace("%vl", save_list).replace("%pl", posion_list).replace("%s" , save_posion)
    
        info = {
            "save_or_poison" : "救人",
            "target": "1",
            "reason": "test"
        }
        info = self.__process_LLM_output__(final_prompt , ['save_or_poison', 'target', 'reason'] , info , 3)

        ret = self.ret_format.copy()
        ret['operation'] = "vote_or_not"
        
        try:
            if info['target'].strip("\n").isdigit() == False:
                return operation
            elif info['save_or_poison'].strip("\n") == "救人":
                ret['target'] = int(info['target'].strip("\n"))
                self.push(self.day , len(self.memory_stream)+1 , f"你用解藥救了{ret['target']}號玩家({self.player_name[ret['target']]})")
                ret['chat'] = 'save'
            elif info['save_or_poison'].strip("\n") == "毒人":
                ret['target'] = int(info['target'].strip("\n"))
                self.push(self.day , len(self.memory_stream)+1 , f"你用毒藥毒了{ret['target']}號玩家({self.player_name[ret['target']]})")
                ret['chat'] = 'poison'

            operation.append(ret)

            return operation
        except:
            return operation


class summary_hunter(summary_role):
    def __init__(self , prompt_dir , logger , openai_kwargs):
        super().__init__(prompt_dir, logger , openai_kwargs)
        
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
        target_list = self.__player_list_to_str__(data['information'][0]['target'])
        final_prompt = self.prompt_template['hunter'].replace("%e" , self.example['hunter']).replace("%l" , sus_role_str).replace("%kl" , know_role_str).replace("%tl" , target_list).replace("%m" , self.summary_prompt(memory_str))

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