import logging
import json
import openai
import re
from pathlib import Path  

class summary():
    def __init__(self , logger , engine ,prompt_dir = "generative_agent_with_werewolf_kill/doc/prompt/summary"):
        self.max_fail_cnt = -1
        self.token_used = 0
        self.prompt_template : dict[str , str] = None
        self.example : dict[str , str] = None
        self.game_info : list(dict[str, str]) = None
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
    
    def __process_LLM_output__(self , prompt , keyword_list , sample_output):
        """
        communication with LLM , repeat {self.max_fail_cnt} util find the {keyword_list} in LLM response .
        return the {keyword_list} dict , if fail get {keyword_list} in LLM response , return {sample_output}.
        """
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

        if fail_idx >= self.max_fail_cnt: info = sample_output

        return info
    
    # def __register_keywords__(self , keywords:dict[str,str]):
    #     self.logger.debug(f"Register new keyword : {keywords}")
    #     self.chinese_to_english.update(keywords)

    def get_summary(self, file_name = "11_05_01_12.jsonl"):

        self.logger.debug("load game info")
        
        # self.game_info = pd.read_json(path_or_buf=f"generative_agent_with_werewolf_kill/doc/game_info/{file_name}", lines=True)   
        with open(f"generative_agent_with_werewolf_kill/doc/game_info/{file_name}" , encoding="utf-8") as json_file: self.game_info = [json.loads(line) for line in json_file.readlines()]
       
        for i in range(0, len(self.game_info)):
            # if 'stage'
            print(f"{i}- {self.game_info[i]['stage']}")

if __name__ == '__main__':

    s = summary(logger = logging.getLogger(__name__), engine = "werewolf")
    game_summary = s.get_summary()