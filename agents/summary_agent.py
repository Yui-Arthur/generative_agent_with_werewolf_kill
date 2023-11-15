from .agent import agent
from .summary import summary
import requests
import threading
from pathlib import Path   


class summary_agent(agent):
    
    def __init__(self , api_json = "doc/secret/openai.key", 
                server_url = "140.127.208.185" , agent_name = "Agent1" , room_name = "TESTROOM" , 
                color = "f9a8d4" , prompt_dir = Path("prompt/memory_stream/")):
        
         
        super().__init__(api_json = api_json, server_url = server_url , 
                        agent_name = agent_name , room_name = room_name , 
                        color = color) 
        
        self.summary_generator = summary(logger= self.logger, api_json = api_json)

    def __get_summary(self, cur_stage):

        # 狼人發言、一般人發言
        if cur_stage in ["dialogue", "werewolf_dialogue"]:
            stage = "dialogue"
        # 狼人投票、一般人投票
        elif cur_stage in ["werewolf", "vote1", "vote2"] :
            stage = "vote"
        # 預言家、女巫、獵人
        elif cur_stage in ["seer", "witch", "hunter"]:
            stage = "operation"
        elif cur_stage == "guess_role":
            stage = "guess_role"
        else:
            return None
        
        self.similarly_sentences = self.summary_generator.find_similarly_summary(stage, game_info = self.game_info)
        return self.similarly_sentences

    def __check_game_state__(self , failure_cnt):
        """check the game state every 1s until game over , if the game state is chaged , call the process data func"""
        try:
            r = requests.get(f'{self.server_url}/api/game/{self.room}/information/{self.name}' ,  headers ={
            "Authorization" : f"Bearer {self.user_token}"
            } , timeout=3)

            if r.status_code == 200:
                data = r.json()
                # block realtime werewolf vote info 
                if data['stage'].split('-')[-1] == "werewolf" : data['vote_info'] = {}
                # clear the agent info 
                data['agent_info'] = {}

                if self.current_info != data:
                    self.current_info = data
                    self.logger.debug(data)
                    self.__record_agent_game_info__(data)

                    # check game over
                    for anno in self.current_info['announcement']: 
                        if anno['operation'] == "game_over" : 
                            self.checker = False
                            self.__game_over_process__(anno , data['timer'])
                            break

                    copy_current_info = self.current_info.copy()
                    copy_current_info["guess_summary"] = self.__get_summary(cur_stage= "guess_role")
                    copy_current_info["stage_summary"] = self.__get_summary(cur_stage= data['stage'].split('-')[-1])
                    
                    self.__process_data__(copy_current_info) 
            else:
                self.logger.warning(r.json())
                failure_cnt+=1

            if failure_cnt >= 5 : self.checker = False
            if self.checker : self.timer = threading.Timer(1.0, self.__check_game_state__ , args=(failure_cnt,)).start()

        except Exception as e:
            self.logger.warning(f"__check_game_state__ Server Error , {e}")
            self.__del__()
    