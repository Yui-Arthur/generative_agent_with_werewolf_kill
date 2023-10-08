from agent import agent
import requests
import threading
import logging
import openai
import sys   
from pathlib import Path   
import time
import json

class memory_stream_agent(agent):
    def __init__(self , openai_token = None , pyChatGPT_token = None , 
                 server_url = "140.127.208.185" , agent_name = "Agent1" , room_name = "TESTROOM" , 
                 color = "f9a8d4"):
        self.__reset_server__(server_url)
        
        super().__init__(openai_token = openai_token , pyChatGPT_token = pyChatGPT_token ,
                                       server_url = server_url , agent_name = agent_name , room_name = room_name , 
                                       color = color) 
        self.master_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX25hbWUiOiJ5dWkiLCJyb29tX25hbWUiOiJURVNUUk9PTSIsImxlYWRlciI6dHJ1ZSwiaWF0IjoxNjkwMzc5NTM0LCJleHAiOjE2OTkwMTk1MzR9.BEmD52DuK657YQezsqNgJAwbPfl54o8Pb--Dh7VQMMA"
        self.__setting_game()
        self.__start_server__()
        self.day = None
        self.turn = 0
        self.first_level_memory = []
        self.second_level_memory = []

    def __proccess_data__(self, data):
        # print(data)
        if self.day != data['stage'].split('-')[0]:
            self.day = data['stage'].split('-')[0]

        self.__proccess_announcement__(data['announcement'])

    def __proccess_announcement__(self , announcement):
        # print(announcement)
        for anno in announcement:
            self.turn +=1
            memory = {
                "day" : self.day,
                "trun" : self.turn,
                "observation" : "" 
            }

            if(anno["operation"] == "chat"):
                memory['observation'] = f"{self.player_name[anno['user'][0]]}({anno['user'][0]})說「{anno['description']}」"    
            else:
                memory['observation'] = f"{anno['description']}"

            self.second_level_memory.append(memory) 
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
        
if __name__ == '__main__':
    a = memory_stream_agent(server_url = "http://localhost:8001" , openai_token=Path("secret/openai.key"))
    while a.checker != False: pass
    print(a.second_level_memory)
    