import requests
import openai
from pathlib import Path   
from utils.agent import agent
from utils.prompts import prompts


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
        
    
    
    