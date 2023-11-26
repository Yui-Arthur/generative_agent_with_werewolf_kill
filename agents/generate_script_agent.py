from .agent import agent
from .intelligent_agent.prompts import prompts
from .summary import summary
import requests
import threading
from pathlib import Path   
import json
import datetime

class generate_script_agent(agent):
    
    md_output = None 
    form_output = None 
    output_lock = threading.Lock()

    def open_outputfile(root_dir):
        generate_script_agent.md_output = open(f'{root_dir}/game.md', 'w' , encoding='utf-8')
        generate_script_agent.form_output = open(f'{root_dir}/form.txt', 'w' , encoding='utf-8')

    def close_outputfile():
        if generate_script_agent.md_output is not None: generate_script_agent.md_output.close()
        if generate_script_agent.form_output is not None: generate_script_agent.form_output.close()

    def __init__(self ,player_number, script_game_path = "doc/game_script/game1", api_json = "doc/secret/yui.key", 
                server_url = "140.127.208.185" , agent_name = "7" , room_name = "TESTROOM" , 
                color = "f9a8d4" , prompt_dir = Path("prompt/memory_stream/")):
        
        if agent_name == "agent0":
            self.__reset_server__(server_url)

        super().__init__(api_json = api_json, server_url = server_url , 
                        agent_name = agent_name , room_name = room_name , 
                        color = color) 
        
        self.master_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX25hbWUiOiJ5dWkiLCJyb29tX25hbWUiOiJURVNUUk9PTSIsImxlYWRlciI6dHJ1ZSwiaWF0IjoxNjkwMzc5NTM0LCJleHAiOjE2OTkwMTk1MzR9.BEmD52DuK657YQezsqNgJAwbPfl54o8Pb--Dh7VQMMA"
        self.script_name =  Path(script_game_path).stem
        self.day = 0
        with open(f"{script_game_path}/{agent_name}.jsonl", encoding="utf-8") as json_file: self.script_info = [json.loads(line) for line in json_file.readlines()]
        self.current_script_idx = 0
        self.agent_name = agent_name
        self.player_number =player_number
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

        if agent_name == f"agent{player_number - 1}":
            self.__setting_game()
            self.__start_server__()



    def __process_data__(self , data):
        # the last player save the anno
        with self.output_lock:
            if '-' in data['stage'] and data['stage'].split('-')[0] != self.day:
                self.day = data['stage'].split('-')[0]
            # agent0 log the public anno
            if self.agent_name == f"agent0" and self.form_output != None and not self.form_output.closed:
                # new day
                    # self.form_output.write(f"\n第{self.day}天\n")
                # player died
                for anno in data['announcement']:
                    if anno['operation'] == 'died':
                        self.form_output.write(f"{self.day}/died/{anno['user'][0]}號玩家死了。\n")

        try:
            
            for info in data["information"]:

                if self.script_info[self.current_script_idx]["chat"] == "poison" and info["description"] == "女巫救人":
                    continue

                with self.output_lock:
                    if self.md_output != None and not self.md_output.closed:
                        self.md_output.write((
                            f"### {self.name[-1]}號玩家 {self.role}\n"
                            f"#### 目標{self.script_info[self.current_script_idx]['target']}號玩家\n" 
                            f"#### {self.script_info[self.current_script_idx]['chat']}\n"
                            f"---\n"))
                    if self.form_output != None and not self.form_output.closed:
                        if info['operation'] == 'dialogue'and data['stage'].split('-')[-1] == 'dialogue':
                            self.form_output.write(f"{self.day}/dialogue/{self.name[-1]}號玩家發言:「{self.script_info[self.current_script_idx]['chat']}」\n")
                        elif info['operation'] == 'dialogue'and data['stage'].split('-')[-1] in ['check','hunter']:
                            self.form_output.write(f"{self.day}/died_dialogue/{self.name[-1]}號玩家遺言:「{self.script_info[self.current_script_idx]['chat']}」\n")
                        elif info['operation'] == 'vote_or_not' and 'vote' in data['stage'].split('-')[-1] :
                            target = self.script_info[self.current_script_idx]['target']
                            target_str = f"投給「{target}號玩家」" if target != -1 else "棄票"
                            self.form_output.write(f"{self.day}/vote/{self.name[-1]}號玩家{target_str}。\n")
                            
                
                    
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
                if data['stage'].split("-")[2] not in  ["werewolf", "vote1" , "vote2"]:
                    self.__skip_stage__()

        except Exception as e:
            self.logger.warning(f"player:{self.agent_name} script end. {e}")
            
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
    
    def __reset_server__(self , server_url):
        """for convenient test"""
        try :
            r = requests.get(f'{server_url}/api/reset' , timeout=5)
        
        except Exception as e :
            self.logger.warning(f"__reset_server__ Server Error , {e}")

    def __start_game_init__(self, room_data):
        """the game started setting , update player name"""
        self.logger.debug(f"game is started , this final room info : {room_data}")
        self.room_setting = room_data['game_setting']
        self.player_name = [name for name in room_data["room_user"]]

        self.__get_role__()
        self.__get_all_role__()
        self.__check_game_state__(0)

    def __save__game__info__(self):
        with open(f"doc/game_info/{self.script_name}_{self.name[-1]}.jsonl" , "w" , encoding='utf-8') as f:
            for info in self.game_info:
                json.dump(info , f , ensure_ascii=False)
                f.write('\n')



if __name__ == "__main__":
    
    player_number = 7
    game_script_path = "doc/game_script/game1"
    api_key = "doc/secret/openai.key"
    url = "http://localhost:8001"
    room_name = "EMPTY"
    for num in range(0, player_number): 
        generate_script_agent(
            player_number= player_number, script_game_path = game_script_path, 
            api_json= api_key, server_url= url, agent_name= f"agent{num}", room_name= room_name)