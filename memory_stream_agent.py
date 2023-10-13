from agent import agent
import requests
import threading
import logging
import openai
import sys   
from pathlib import Path   
import time
import json
import numpy as np
import re
import time
import math
from sentence_transformers import SentenceTransformer, util


class long_memeory_stream():
    
    def __init__(self , prompt_template , example , logger):
        self.memory_stream = []
        self.logger = logger
        # self.__openai_init__(openai_token)
        self.prompt_template : dict[str , str] = prompt_template 
        self.example : dict[str , str] = example
        self.chinese_to_english = {
            # importantance
            "分數" : "score",
            "原因" : "reason",
            # reflection question
            "問題" : "question",
            # refection
            "見解" : "opinion",
            "參考見解" : "reference",
        }
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    def push(self , day , turn , observation):
        info = self.__cal_importantance__(observation)
        full_observation = {
            "day" : day,
            "trun" : turn,
            "last_used" : turn,
            "observation" : observation ,
            "importantance" : int(info["score"]),
            "impo_reason" : info['reason']
        }
        self.logger.debug(f"push observation {full_observation}")
        self.memory_stream.append(full_observation)

    def retrieval(self , day , turn , query , pick_num = 10):

        importantance_score = [ob['importantance'] for ob in self.memory_stream]
        recency_score = self.__cal_recency__(day , turn)
        relevance_score = self.__cal_relevance__(query)


        self.logger.debug(f"importantance {importantance_score}")
        self.logger.debug(f"imporecency {recency_score}")
        self.logger.debug(f"relevance {relevance_score}")


        importantance_factor = 1
        relevance_factor = 1
        recency_factor = 1

        score = recency_score * recency_factor + importantance_score * importantance_factor + relevance_score * relevance_factor
        sorted_memory_streams = self.memory_stream.copy()

        for idx in range(len(sorted_memory_streams)):
            sorted_memory_streams[idx]["score"] = score[idx]
            sorted_memory_streams[idx]["ori_idx"] = idx

        sorted_memory_streams.sort(key=lambda element: element['score'] , reverse=True)

        for idx in range(min(pick_num , len(sorted_memory_streams))):
            self.memory_stream[sorted_memory_streams[idx]['ori_idx']]['lasted_used'] = turn


        self.logger.debug(f"retrieval memory {sorted_memory_streams[:pick_num]}")
        return sorted_memory_streams[:pick_num]

    def __cal_importantance__(self , observation):
                
        final_prompt = self.prompt_template['importantance'].replace("%m" , observation).replace("%e" , self.example['importantance'])

        success_get_patten = False
        fail_idx = 0

        # while not success_get_patten or fail_idx >= 3:

        #     info = {}
        #     result = self.__openai_send__(final_prompt)
        #     splited_result = result.split('\n')
        #     patten_name = ""
        #     for line in splited_result:
        #         patten = re.search('\[(.*)\]', line)
        #         if patten != None:
        #             patten_name = self.chinese_to_english[patten.group(1)]
        #             info[patten_name] = ""
        #         elif patten_name != "":
        #             info[patten_name] += line

        #     if "score" in info.keys(): success_get_patten = True
        #     else : fail_idx+=1

        info = {
            "score" : "0",
            "reason" : "test"
        }

        return info

    def __cal_recency__(self , day, turn) :

        initial_value = 1.0
        decay_factor = 0.99

        score = [0 for i in range(len(self.memory_stream))]

        for idx , observation in enumerate(self.memory_stream):

            time = (turn-observation['last_used'])
            score[idx] = initial_value * math.pow(decay_factor, time)
        
        score = np.array(score)
        return score / np.linalg.norm(score)
    
    def __cal_relevance__(self , query : str):

        query_embedding = self.model.encode(query , convert_to_tensor=True)
        score = [0 for i in range(len(self.memory_stream))]

        self.logger.debug('start relevance')
        text = [i['observation'] for i in self.memory_stream]
        embeddings = self.model.encode(text, convert_to_tensor=True)

        for idx in range(embeddings.shape[0]):
            score[idx] = util.pytorch_cos_sim(query_embedding, embeddings[idx]).to("cpu").item()
        self.logger.debug('end relevance')
        # print(score)
        score = np.array(score)
        return score / np.linalg.norm(score)

    def __openai_send__(self , prompt):
        """openai api send prompt , can override this."""
        response = openai.ChatCompletion.create(
            engine="agent",
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
        
        return response['choices'][0]['message']['content']
    
    def __len__(self):
        return len(self.memory_stream)
    

class memory_stream_agent(agent):
    def __init__(self , openai_token = None , pyChatGPT_token = None , 
                 server_url = "140.127.208.185" , agent_name = "Agent1" , room_name = "TESTROOM" , 
                 color = "f9a8d4" , prompt_dir = Path("prompt/memory_stream/")):
        self.__reset_server__(server_url)
        
        super().__init__(openai_token = openai_token , pyChatGPT_token = pyChatGPT_token ,
                                       server_url = server_url , agent_name = agent_name , room_name = room_name , 
                                       color = color) 
        self.master_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX25hbWUiOiJ5dWkiLCJyb29tX25hbWUiOiJURVNUUk9PTSIsImxlYWRlciI6dHJ1ZSwiaWF0IjoxNjkwMzc5NTM0LCJleHAiOjE2OTkwMTk1MzR9.BEmD52DuK657YQezsqNgJAwbPfl54o8Pb--Dh7VQMMA"
        self.__setting_game()
        self.__start_server__()
        self.day = None
        self.turn = 0
        self.prompt : dict[str , str] = None
        self.example : dict[str , str] = None
        self.__load_prompt_and_example__(prompt_dir)
        self.long_memory = long_memeory_stream(prompt_template = self.prompt , example = self.example , logger=self.logger)
        

    def __proccess_data__(self, data):
        if self.day != data['stage'].split('-')[0]:
            self.day = data['stage'].split('-')[0]

        self.__proccess_announcement__(data['announcement'])

        if len(self.long_memory) > 2:
            self.long_memory.retrieval(self.day , self.turn , "誰是狼")

    def __proccess_announcement__(self , announcement):
        for anno in announcement:
            self.turn +=1
            observation = ""
            
            if(anno["operation"] == "chat"):
                observation = f"{self.player_name[anno['user'][0]]}({anno['user'][0]})說「{anno['description']}」"    
            else:
                observation = f"{anno['description']}"

            self.long_memory.push(self.day , self.turn , observation)
            
        pass

    def __reset_server__(self , server_url):
        """for convenient test"""
        try :
            r = requests.get(f'{server_url}/api/reset' , timeout=5)
            # if r.status_code == 200:
            #     self.logger.debug("Reset Room Success")
            # else:
            #     self.logger.warning(f"Reset Room Error : {r.json()}")
        
        except Exception as e :
            self.logger.warning(f"__reset_server__ Server Error , {e}")
            
    def __start_server__(self):
        """for convenient test"""
        try :
            r = requests.get(f'{self.server_url}/api/start_game/{self.room}' , headers= {
                "Authorization" : f"Bearer {self.master_token}"
            })
            if r.status_code == 200:
                self.logger.debug("Start Game")
            else:
                self.logger.warning(f"Start Game : {r.json()}")
        
        except Exception as e :
            self.logger.warning(f"__start_server__ Server Error , {e}")
    
    def __setting_game(self):
        """for convenient test"""
        try :
            r = requests.post(f'{self.server_url}/api/room/{self.room}' , headers= {
                "Authorization" : f"Bearer {self.master_token}"
            }, json= {
                "player_num": 7,    
                "operation_time" : 2,
                "dialogue_time" : 2,
                "seer" : 1,
                "witch" : 1,
                "village" : 2,
                "werewolf" : 2,
                "hunter" : 1 
            })
            if r.status_code == 200:
                self.logger.debug("Setting Game Success")
            else:
                self.logger.warning(f"Setting Game Error : {r.json()}")
        
        except Exception as e :
            self.logger.warning(f"__setting_game Server Error , {e}")
    
    def __load_prompt_and_example__(self , prompt_dir):
        """load prompt json to dict"""
        with open(prompt_dir / "prompt.json" , encoding="utf-8") as json_file: self.prompt = json.load(json_file)
        with open(prompt_dir / "example.json" , encoding="utf-8") as json_file: self.example = json.load(json_file)

        for key , prompt_li in self.prompt.items():
            self.prompt[key] = '\r\n'.join(prompt_li)
        for key , prompt_li in self.example.items():
            self.example[key] = '\r\n'.join(prompt_li)

        
if __name__ == '__main__':
    a = memory_stream_agent(server_url = "http://localhost:8001" , openai_token=Path("secret/openai.key") )
    while a.checker != False: pass
    
    # print(a.second_level_memory)
    # template = {
    #     "importantance" : ("現在正在進行狼人殺遊戲，要對玩家的發言進行評分，分數從1~10。"
    #     "1分代表這段發言沒提供什麼重要資訊。"
    #     "5分代表這段發言有提供一些重要資訊，但可能沒有清楚說明原因。"
    #     "10分代表這段發言非常重要，可能提供了很多線索，同時有清楚的說明。"
    #     "以下是一些例子"
    #     "%e"
    #     "接著給玩家的[發言]，請給我這個段發言的[分數]，並一步一步說清楚[原因]，要依照上述例子的格式進行回答。"
    #     "* 資訊"
    #     "%m"
    #     "* 回應")
    # }
    # t = long_memeory_stream(openai_token=Path("secret/openai.key") , prompt_template = template)
    # t.push("2號玩家(Yui2)說「我就只是個民，沒有資訊，但是剛剛0號玩家的發言，我聽起來有點奇怪，感覺有點像狼。」")
    
    