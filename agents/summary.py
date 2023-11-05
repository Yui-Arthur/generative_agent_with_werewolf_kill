import logging
import json
import openai
import re
from pathlib import Path  
import os
from sentence_transformers import SentenceTransformer, util

class summary():
    def __init__(self , logger , prompt_dir="generative_agent_with_werewolf_kill/doc/prompt/summary", api_json = "generative_agent_with_werewolf_kill/doc/secret/openai.key", api_key = "generative_agent_with_werewolf_kill/doc/secret/chatgpt_api_key.key"):
        self.max_fail_cnt = 3
        self.max_fail_cnt = -1
        self.token_used = 0
        self.prompt_template : dict[str , str] = None
        self.example : dict[str , str] = None
        self.memory_stream = ""
        self.operation_info = ""
        self.chat_func = None
        self.chinese_to_english = {
            # summary
            "投票總結" : "vote",
            "發言總結" : "dialogue",
            "技能總結" : "operation",
        }
        self.role_to_chinese = {
            "seer" : "預言家",
            "witch" : "女巫",
            "village" : "村民",
            "werewolf" : "狼人",
            "hunter" : "獵人"
        }

        self.logger : logging.Logger = logger
        self.prompt_dir = Path(prompt_dir)
        self.__load_prompt_and_example__(self.prompt_dir)
        if api_json is not None : self.__openai_init_v2_(api_json)
        else: raise Exception("Not give api_init parameter")

        with open(Path(api_key), "r") as file : self.api_key = file.readline() 
        
        self.summary_limit = 20
        self.similarly_sentence_num = 5
        self.get_score_fail_times = 3

        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    def __load_prompt_and_example__(self , prompt_dir):
        """load prompt json to dict"""
        self.logger.debug("load common json")
        with open(prompt_dir / "common_prompt.json" , encoding="utf-8") as json_file: self.prompt_template = json.load(json_file)
        with open(prompt_dir / "common_example.json" , encoding="utf-8") as json_file: self.example = json.load(json_file)

        for key , prompt_li in self.prompt_template.items():
            self.prompt_template[key] = '\n'.join(prompt_li)
        for key , prompt_li in self.example.items():
            self.example[key] = '\n'.join(prompt_li)

    def __openai_init_v2_(self , api_json):
        """openai api setting , can override this"""
        with open(api_json,'r') as f : api_info = json.load(f)
        openai.api_type = api_info["api_type"]
        openai.api_base = api_info["api_base"]
        openai.api_version = api_info["api_version"] 
        openai.api_key = api_info["key"]
        self.engine = api_info['engine']
        

        self.chat_func = self.__openai_send__
    

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
        # print(f"LLM output : {info}")

        if fail_idx >= self.max_fail_cnt: info = sample_output

        return info
    
    def __process_announcement__(self , data):
        """add announcement to memory stream"""
        announcement = data['announcement']

        if any(data["vote_info"].values()) :
            self.__push_vote_info__(data["vote_info"] , data["stage"])

        for anno in announcement:
            observation = ""
            if anno["operation"] == "chat":
                # observation = f"{anno['user'][0]}號玩家({self.player_name[anno['user'][0]]})說「{anno['description']}」"    
                observation = f"{anno['user'][0]}號玩家說「{anno['description']}」\n"    
            elif anno["operation"] == "died":
                # observation = f"{anno['user'][0]}號玩家({self.player_name[anno['user'][0]]})死了"    
                observation = f"{anno['user'][0]}號玩家死了\n"    
            
                
            self.memory_stream += observation

    def __push_vote_info__(self , vote_info : dict , stage):
        """add vote info to memory stream"""
        prefix = "狼人投票殺人階段:" if stage.split('-')[-1] == "seer" else "玩家票人出去階段:"

        for player , voted in vote_info.items():
            player = int(player)
            if voted != -1:
                # ob = f"{prefix} {player}號玩家({self.player_name[player]})投給{voted}號玩家({self.player_name[voted]})"
                ob = f"{prefix} {player}號玩家投給{voted}號玩家\n"
            else:
                # ob = f"{prefix} {player}號玩家({self.player_name[player]})棄票"
                ob = f"{prefix} {player}號玩家棄票\n"

            self.memory_stream += ob


    def get_summary(self, file_name = "11_05_14_59.jsonl"):

        self.logger.debug("load game info")
        with open(f"generative_agent_with_werewolf_kill/doc/game_info/{file_name}" , encoding="utf-8") as json_file: game_info = [json.loads(line) for line in json_file.readlines()]
        for anno in game_info[-1]["announcement"]:
            if anno["operation"] == "game_over":
                result = anno["description"]

        # 分天summary
        day = 1
        for info in game_info:
            if "stage" in info:
                if day != int(info["stage"].split("-")[0]):
                    day_str = f"第{day}天"
                    # vote、dialogue、operation summary
                    all_summary = self.__get_day_summary__(day_str, self.memory_stream, self.operation_info, result)
                    self.__write_summary_score(all_summary, role="女巫")
                    
                    day = int(info["stage"].split("-")[0])
                    self.memory_stream = ""
                    self.operation_info = ""

                self.__process_announcement__(info)
            else:
                self.operation_info += f"你使用了{self.role_to_chinese[info['stage_name'].split('-')[-1]]}的技能，目標是{info['target']}號玩家\n"
        
        day_str = f"第{day}天"
        all_summary = self.__get_day_summary__(day_str, self.memory_stream, self.operation_info, result)
        self.__write_summary_score(all_summary, role="女巫")

    def __get_day_summary__(self, day, day_memory, day_operation, result):
        """day summary to openai"""
        print("day summary")
        self.logger.debug(f"day summary")        
        self.max_fail_cnt = 3
        # memory_str = self.__memory_to_str__(day_memory)
        # player_list = self.__get_player_list__()
        player_list = ""
        final_prompt = self.prompt_template['day_summary'].replace("%l" , self.example['day_summary']).replace("%z", day).replace("%m" , day_memory).replace("%o" , day_operation).replace("%y" , player_list).replace("%p" , result)
        print(f"final_prompt = {final_prompt}")
        info = {
            "vote" : "vote_summary",
            "dialogue" : "dialogue_summary",
            "operation" : "operation_summary",
        }        
        info = self.__process_LLM_output__(final_prompt , ["vote", "dialogue", "operation"] , info)

        return info['vote'], info['dialogue'], info['operation']

    def __write_summary_score(self,summary , role):
        """summary + score"""
        self.set_score(self, role, "vote", summary[0])
        self.set_score(self, role, "dialogue", summary[1])
        self.set_score(self, role, "operation", summary[2])

    def set_score(self, role, stage, summary):

        final_prompt = self.prompt_template["score"].replace("%s", summary)
        self.logger.debug("Prompt: "+str(final_prompt))
        response = self.__chatgpt_send__(final_prompt)
        print(final_prompt)
        self.logger.debug("Response: "+str(response))
        print(response)
        try:
            score = response.split(":")[1]
        except:
            self.logger.debug("Error: Don't match key")
            self.get_score_fail_times -= 1
            if self.get_score_fail_times >= 0:
                self.set_score(role= role, stage= stage, summary= summary)

        file_path = os.path.join(role, f"{stage}.json")
        try:
            summary_set = self.__load_summary(file_path= file_path)
        except:
            summary_set = []
        updated_summary_set = self.__update_summary(summary_set= summary_set, summary= summary, score= score)
    
        self.__write_summary(file_path= file_path, data= updated_summary_set)

    def __load_summary(self, file_path):
        
        with open(self.prompt_dir / file_path, encoding="utf-8") as json_file: summary_set = json.load(json_file)
        return summary_set
    
    def __write_summary(self, file_path, data):

        try:
            with open(self.prompt_dir / file_path, "w") as json_file: 
                new_data = json.dumps(data, indent= 1)
                json_file.write(new_data)
        except:
            os.mkdir(self.prompt_dir / file_path.split("\\")[0])
            self.__write_summary(file_path, data)
        self.get_score_fail_times = 3

    def __update_summary(self, summary_set, summary, score):
        
        summary_set.append({"summary": summary, "score": score})
        summary_set = sorted(summary_set, key= lambda x : x["score"], reverse= True)
        
        if len(summary_set) > self.summary_limit:            
            summary_set.pop()
        return summary_set
    
    def find_similarly_summary(self, role, stage, current_content):
        
        file_path = os.path.join(role, f"{stage}.json")
        summary_set = self.__load_summary(file_path= file_path)
        similarly_scores = []
        for idx, summary_each in enumerate(summary_set):
            embeddings = self.embedding_model.encode([summary_each, current_content])
            cos_sim = util.cos_sim(embeddings, embeddings)
            similarly_scores.append([cos_sim[0][1], idx])

        similarly_scores = sorted(similarly_scores,key= lambda x: x[1], reverse= True)

        return similarly_scores[0: self.similarly_sentence_num]

    def __chatgpt_send__(self, prompt):
        
        openai.api_key = self.api_key
        response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature = 0.7,
            max_tokens = 800,
            top_p = 0.95,
            frequency_penalty = 0,
            presence_penalty = 0,
            stop = None
        )

        res_content = response['choices'][0]['message']['content']

        return res_content
    
if __name__ == '__main__':

    s = summary(logger = logging.getLogger(__name__))
    game_summary = s.get_summary()
    # game_summary = s.get_summary()
    # s.set_score(role= "witch", stage= "skill", summary= "女巫沒有使用解藥救被狼人殺的人(預言家)")
