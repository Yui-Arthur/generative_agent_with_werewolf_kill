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
from utils.agent import agent
from utils.role import role


class memory_stream_agent(agent):
    def __init__(self , openai_token = None , pyChatGPT_token = None , 
                 server_url = "140.127.208.185" , agent_name = "Agent1" , room_name = "TESTROOM" , 
                 color = "f9a8d4" , prompt_dir = Path("prompt/memory_stream/")):
        self.__reset_server__(server_url)
        
        super().__init__(openai_token = openai_token , pyChatGPT_token = pyChatGPT_token ,
                                       server_url = server_url , agent_name = agent_name , room_name = room_name , 
                                       color = color) 
        # used for start game for test
        self.master_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX25hbWUiOiJ5dWkiLCJyb29tX25hbWUiOiJURVNUUk9PTSIsImxlYWRlciI6dHJ1ZSwiaWF0IjoxNjkwMzc5NTM0LCJleHAiOjE2OTkwMTk1MzR9.BEmD52DuK657YQezsqNgJAwbPfl54o8Pb--Dh7VQMMA"
        
        # init long memory class & models
        self.long_memory : role = role(prompt_dir , logger=self.logger)
        # start the game
        self.day = None
        self.turn = 0
        # set the game for test
        self.__setting_game()
        # start the game for test
        self.__start_server__()

    def __process_data__(self, data):
        """the data process."""
        # if self.day != data['stage'].split('-')[0]:
        #     self.day = data['stage'].split('-')[0]

        self.long_memory.update_stage(data)

    # def __process_announcement__(self , announcement):
    #     """add announcement to memory stream"""
    #     for anno in announcement:
    #         self.turn +=1
    #         observation = ""
            
    #         if(anno["operation"] == "chat"):
    #             observation = f"{self.player_name[anno['user'][0]]}({anno['user'][0]})說「{anno['description']}」"    
    #         else:
    #             observation = f"{anno['description']}"

    #         self.long_memory.push(self.day , self.turn , observation)
            
    #     pass

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
    
    def __start_game_init__(self):
        """the game started setting , update player name"""
        self.__get_role__()
        self.long_memory.update_game_info(self.player_name , self.role)
        self.__check_game_state__(0)
        
if __name__ == '__main__':
    a = memory_stream_agent(server_url = "http://localhost:8001" , openai_token=Path("secret/openai.key") )
    while a.checker != False: pass
    
    
    