import requests
import openai
from pathlib import Path   
from utils.agent import agent
from utils.prompts import prompts
from pathlib import Path   
import logging
from datetime import datetime
import sys 

class intelligent_agent(agent):
    
    def __init__(self , openai_token = None , api_base = "https://wolf-openai-llm.openai.azure.com/" , engine = "agent", 
                 server_url = "140.127.208.185" , agent_name = "Agent1" , room_name = "TESTROOM" , 
                 color = "f9a8d4" , prompt_dir = Path("prompt/memory_stream/")):
        
        
        super().__init__(openai_token = openai_token, api_base = api_base , engine = engine, 
                                       server_url = server_url , agent_name = agent_name , room_name = room_name , 
                                       color = color) 
        # used for start game for test
        self.master_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX25hbWUiOiJ5dWkiLCJyb29tX25hbWUiOiJURVNUUk9PTSIsImxlYWRlciI6dHJ1ZSwiaWF0IjoxNjkwMzc5NTM0LCJleHAiOjE2OTkwMTk1MzR9.BEmD52DuK657YQezsqNgJAwbPfl54o8Pb--Dh7VQMMA"
        
        # init long memory class & models
        self.prompts : prompts = None

        # start the game
        self.day = None
        self.turn = 0

        

    def __openai_init__(self , openai_token, api_base):
        """openai api setting , can override this"""
        with open(openai_token,'r') as f : openai_token = f.readline()
        openai.api_type = "azure"
        openai.api_base = api_base
        openai.api_version = "2023-05-15"
        openai.api_key = openai_token
        self.chat_func = self.__openai_send__ 

    

    def __process_data__(self, data):
        """Process the data got from server"""

        operations = self.prompts.agent_process(data)
        # self.logger.debug("Operations "+str(operations))

        

        for i in operations:
            op_data = {
                "stage_name" : data['stage'],
                "operation" : i["operation"],
                "target" : i["target"],
                "chat" : i["chat"]
            }
            self.__send_operation__(op_data)


    
    

    def __start_game_init__(self):
        """the game started setting , update player name"""
        data = self.__get_role__()
        self.logger.debug(f'User data: {data}')


        self.prompts : prompts = prompts(data['player_id'], data['game_info'], self.room_setting, self.logger)


        self.__check_game_state__(0)
        
    
    
class intelligent_agent_test(agent):
    
    def __init__(self , openai_token = None , api_base = "https://wolf-openai-llm.openai.azure.com/" , engine = "agent", 
                 server_url = "140.127.208.185" , agent_name = "Agent1" , room_name = "TESTROOM" , 
                 color = "f9a8d4" , prompt_dir = Path("prompt/memory_stream/")):
        self.__reset_server__(server_url)
        
        super().__init__(openai_token = openai_token, api_base = api_base , engine = engine, 
                                       server_url = server_url , agent_name = agent_name , room_name = room_name , 
                                       color = color) 
        # used for start game for test
        self.master_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX25hbWUiOiJ5dWkiLCJyb29tX25hbWUiOiJURVNUUk9PTSIsImxlYWRlciI6dHJ1ZSwiaWF0IjoxNjkwMzc5NTM0LCJleHAiOjE2OTkwMTk1MzR9.BEmD52DuK657YQezsqNgJAwbPfl54o8Pb--Dh7VQMMA"
        
        # init long memory class & models
        self.prompts : prompts = None

        # start the game
        self.day = None
        self.turn = 0

        
        # set the game for test
        self.room_setting = {
            "player_num": 7,    
            "operation_time" : 5,
            "dialogue_time" : 10,
            "seer" : 1,
            "witch" : 1,
            "village" : 2,
            "werewolf" : 2,
            "hunter" : 1 
        }
        self.__setting_game()
        # start the game for test
        self.__start_server__()

    def __openai_init__(self , openai_token, api_base):
        """openai api setting , can override this"""
        with open(openai_token,'r') as f : openai_token = f.readline()
        openai.api_type = "azure"
        openai.api_base = api_base
        openai.api_version = "2023-05-15"
        openai.api_key = openai_token
        self.chat_func = self.__openai_send__ 

    def __logging_setting__(self):
        """logging setting , can override this."""
        log_format = logging.Formatter('[%(asctime)s] [%(levelname)s] - %(message)s')
        self.logger.setLevel(logging.DEBUG)

        current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        handler = logging.FileHandler(filename=f'logs/{self.name}_{self.room}_{current_time}.log', encoding='utf-8' , mode="w")
        handler.setLevel(logging.DEBUG)   
        handler.setFormatter(log_format)
        self.logger.addHandler(handler)   

        handler = logging.StreamHandler(sys.stdout)    
        handler.setLevel(logging.DEBUG)                                        
        handler.setFormatter(log_format)    
        self.logger.addHandler(handler)   

        logging.getLogger("requests").propagate = False

    def __process_data__(self, data):
        """Process the data got from server"""

        operations = self.prompts.agent_process(data)
        # self.logger.debug("Operations "+str(operations))

        

        for i in operations:
            op_data = {
                "stage_name" : data['stage'],
                "operation" : i["operation"],
                "target" : i["target"],
                "chat" : i["chat"]
            }
            self.__send_operation__(op_data)


    

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
            }, json= self.room_setting)
            if r.status_code == 200:
                self.logger.debug("Setting Game Success")
            else:
                self.logger.warning(f"Setting Game Error : {r.json()}")
        
        except Exception as e :
            self.logger.warning(f"__setting_game Server Error , {e}")
    

    def __start_game_init__(self):
        """the game started setting , update player name"""
        data = self.__get_role__()
        self.logger.debug(f'User data: {data}')


        self.prompts : prompts = prompts(data['player_id'], data['game_info'], self.room_setting, self.logger)


        self.__check_game_state__(0)
        

if __name__ == '__main__':
    a = intelligent_agent_test(server_url = "http://localhost:8001" , openai_token=Path("doc/secret/openai.key") )
    while a.checker != False: pass
       