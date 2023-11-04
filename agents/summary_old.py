import logging
import json
import openai
import re
import requests
from pathlib import Path  

class summary_old():
    def __init__(self , logger , engine , server_url = "140.127.208.185" , room_name = "TESTROOM" ,prompt_dir = "doc/prompt/summary"):
        self.max_fail_cnt = -1
        self.token_used = 0
        self.prompt_template : dict[str , str] = None
        self.example : dict[str , str] = None
        self.chinese_to_english = {
            # summary
            "總結" : "summary"
        }
        self.role_to_chinese = {
            "seer" : "預言家",
            "witch" : "女巫",
            "village" : "村民",
            "werewolf" : "狼人",
            "hunter" : "獵人"
        }
        self.engine = engine
        self.server_url = server_url
        self.room_name = room_name
        self.logger : logging.Logger = logger
        self.prompt_dir = Path(prompt_dir)
        self.__load_prompt_and_example__(self.prompt_dir)

    def __load_prompt_and_example__(self , prompt_dir):
        """load prompt json to dict"""
        self.logger.debug("load common json")
        with open(prompt_dir / "common_prompt.json" , encoding="utf-8") as json_file: self.prompt_template = json.load(json_file)
        with open(prompt_dir / "common_example.json" , encoding="utf-8") as json_file: self.example = json.load(json_file)

        for key , prompt_li in self.prompt_template.items():
            self.prompt_template[key] = '\n'.join(prompt_li)
        for key , prompt_li in self.example.items():
            self.example[key] = '\n'.join(prompt_li)

    def __openai_send__(self , prompt):
        """openai api send prompt , can override this."""
        response = openai.ChatCompletion.create(
            engine = self.engine,
            messages = [
                {"role":"system","content":"You are an AI assistant that helps people find information."},
                {"role":"user","content":prompt}
            ],
            temperature=0.7,
            max_tokens=800,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None)
        
        self.token_used += response["usage"]["total_tokens"]
        
        if response['choices'][0]["finish_reason"] == "content_filter":
            self.logger.debug("Block By Openai")
            return None

        return response['choices'][0]['message']['content']
    
    def __process_LLM_output__(self , prompt , keyword_list , sample_output , max_fail_cnt = -1):
        """
        communication with LLM , repeat {max_fail_cnt} util find the {keyword_list} in LLM response .
        return the {keyword_list} dict , if fail get {keyword_list} in LLM response , return {sample_output}.
        """
        # max_fail_cnt = self.max_fail_cnt
        success_get_keyword = False
        fail_idx = 0

        self.logger.debug(f"LLM keyword : {keyword_list}")
        info = {}

        while not success_get_keyword and fail_idx < self.max_fail_cnt:

            self.logger.debug(f"start {fail_idx} prompt")
            info = {}
            result = self.__openai_send__(prompt)

            # result block by openai
            if result == None:
                fail_idx+=1
                continue
            
            
            splited_result = result.split('\n')
            keyword_name = ""
            for line in splited_result:
                # get keyword like [XXX]
                keyword = re.search('\[(.*)\]', line)
                if keyword != None and keyword.group(1) in self.chinese_to_english.keys():
                    keyword_name = self.chinese_to_english[keyword.group(1)]
                    info[keyword_name] = ""
                elif keyword_name != "":
                    info[keyword_name] += line + "\n"

            if all(_ in info.keys() for _ in keyword_list): success_get_keyword = True
            else : fail_idx+=1
        
        self.logger.debug(f"LLM output : {info}")

        if fail_idx >= max_fail_cnt: info = sample_output

        return info

    def __memory_to_str__(self , memory , add_idx=True):
        """
        export the memory dict to str like
        1. {observation[1]}
        2. {observation[2]}
        or
        {observation[1]}
        {observation[2]}
        """
        if add_idx:
            return '\n'.join([f"{idx}. {i['observation']}" for idx , i in enumerate(memory)])
        else:
            return '\n'.join([f"{i['observation']}" for idx , i in enumerate(memory)])

    def __get_player_list__(self):
        try:
            r = requests.get(f'{self.server_url}/api/game/{self.room_name}' , timeout=5)

            if r.status_code == 200:
                player_list = r.json()["player"]
                player_str = self.__player_list_str__(player_list)
                self.logger.debug(f"Agent Role List: {player_str}")
                return player_str
            else:
                self.logger.warning(f"Get player list Error : {r.json()}")
        except Exception as e:
            self.logger.warning(f"__get_player_list__ Server Error , {e}")

    def __player_list_str__(self, player_list):

        player_str = ""
        for i in range(0, len(player_list)):
            player_str += f"{i}. {i}號玩家({player_list[str(i)]['user_name']})是{self.role_to_chinese[player_list[str(i)]['user_role']]}\n"

        return player_str
    
    def get_summary(self, memory_stream, result):
        """total summary"""

        self.logger.debug(f"total summary")        
        self.max_fail_cnt = 3
        day_memory_str = self.__day_summary__(memory_stream, result)
        player_list = self.__get_player_list__()
        final_prompt = self.prompt_template['summary'].replace("%l" , self.example['summary']).replace("%m" , day_memory_str).replace("%y" , player_list).replace("%p" , result)
        info = {
            "summary" : "test"
        }        
        info = self.__process_LLM_output__(final_prompt , ['summary'] , info , 3)

        return info['summary']

    def __day_summary__(self, memory_stream, result):
        """every day summary"""

        day = 0
        pre_idx = 0
        total_summary = ""
        # !!code bug 不會summary到最後一天
        for i in range(0, len(memory_stream)):
            if day != memory_stream[i]['day']:
                day_str = f"第{day}天"
                day = memory_stream[i]['day']
                day_summar = self.__get_day_summary__(day_str, memory_stream[pre_idx:i+1], result)
                pre_idx = i+1
                total_summary += f"{day}. {day_summar}"
                # 確認換行

        return total_summary

    def __get_day_summary__(self, day, day_memory, result):
        """day summary to openai"""

        self.logger.debug(f"day summary")        
        self.max_fail_cnt = 3
        memory_str = self.__memory_to_str__(day_memory)
        player_list = self.__get_player_list__()
        final_prompt = self.prompt_template['day_summary'].replace("%l" , self.example['day_summary']).replace("%z", day).replace("%m" , memory_str).replace("%y" , player_list).replace("%p" , result)
        info = {
            "summary" : "test"
        }        
        info = self.__process_LLM_output__(final_prompt , ['summary'] , info , 3)

        return info['summary']

    