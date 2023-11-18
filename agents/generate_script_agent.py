from agent import agent
from intelligent_agent.prompts import prompts
from summary import summary
import requests
import threading
from pathlib import Path   
import json

class generate_script_agent(agent):
    
    def __init__(self ,player_number, script_game_path = "doc/game_script/game1", api_json = "doc/secret/yui.key", 
                server_url = "140.127.208.185" , agent_name = "7" , room_name = "TESTROOM" , 
                color = "f9a8d4" , prompt_dir = Path("prompt/memory_stream/")):
        
        super().__init__(api_json = api_json, server_url = server_url , 
                        agent_name = agent_name , room_name = room_name , 
                        color = color) 
        
        self.master_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX25hbWUiOiJ5dWkiLCJyb29tX25hbWUiOiJURVNUUk9PTSIsImxlYWRlciI6dHJ1ZSwiaWF0IjoxNjkwMzc5NTM0LCJleHAiOjE2OTkwMTk1MzR9.BEmD52DuK657YQezsqNgJAwbPfl54o8Pb--Dh7VQMMA"
        
        with open(f"{script_game_path}/{agent_name}.jsonl", encoding="utf-8") as json_file: self.script_info = [json.loads(line) for line in json_file.readlines()]
        self.current_script_idx = 0
        self.agent_name = agent_name
        # set the game for test
        self.room_setting = {
            "player_num": 7,    
            "operation_time" : 3,
            "dialogue_time" : 3,
            "seer" : 1,
            "witch" : 1,
            "village" : 2,
            "werewolf" : 2,
            "hunter" : 1 
        }
        print("agent_name", agent_name)
        if agent_name  == "5":
            self.witch_save = 1
            self.witch_poison = 1

        self.__setting_game()
        if agent_name == str(player_number - 1):
            self.__start_server__()



    def __process_data__(self , data):
        
        if(len(data['information']) == 0):
            # self.current_script_idx += 1
            return
        
        print("agent_name", self.agent_name)
        print(data)
        print(self.script_info[self.current_script_idx])
        print("///////////////////")
        try:
            

            for info in data["information"]:
                
                if self.script_info[self.current_script_idx]["chat"] == "poison" and info["description"] == "女巫救人":
                    continue
                    
                op_data = {
                    "stage_name" : data['stage'],
                    "operation" : info["operation"],
                    "target" : self.script_info[self.current_script_idx]["target"],
                    "chat" : self.script_info[self.current_script_idx]["chat"]
                }
                self.__send_operation__(op_data)

                # 女巫有用解藥的情況
                if self.script_info[self.current_script_idx]["chat"] == "save" and info["description"] == "女巫救人" and self.script_info[self.current_script_idx]["target"] != -1:
                    self.current_script_idx += 1
                    break
                self.current_script_idx += 1

        except:
            self.logger.warning(f"player:{self.agent_name} script end.")
            
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
    
        
    def __start_game_init__(self, room_data):
        """the game started setting , update player name"""
        self.logger.debug(f"game is started , this final room info : {room_data}")
        self.room_setting = room_data['game_setting']
        self.player_name = [name for name in room_data["room_user"]]

        self.__get_role__()
        self.__get_all_role__()
        self.__check_game_state__(0)



if __name__ == "__main__":
    
    player_number = 7
    game_script_path = "doc/game_script/game2"
    api_key = "doc/secret/openai.key"
    url = "http://localhost:8001"
    room_name = "EMPTY"
    for num in range(0, player_number): 
        
        script_thread = threading.Thread(target= generate_script_agent, 
            # game_script path, api_key path, url, agent_name, romm_name, color, prompt path
            args=((player_number, game_script_path, api_key, url, str(num), 
                room_name, "f9a8d4", Path("prompt/memory_stream/"))))
        script_thread.start()
        script_thread.join()