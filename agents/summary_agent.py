from agent import agent
from pathlib import Path   
from summary import summary
import json
import datetime

class summary_agent(agent):
    
    def __init__(self , openai_token = None , api_base = "https://wolf-openai-llm.openai.azure.com/" , engine = "agent", api_json = "doc/secret/yui.key", 
                server_url = "140.127.208.185" , agent_name = "Agent1" , room_name = "TESTROOM" , 
                color = "f9a8d4" , prompt_dir = Path("prompt/memory_stream/")):
        
        
        super().__init__(openai_token = openai_token, api_base = api_base , engine = engine, api_json = api_json,
                        server_url = server_url , agent_name = agent_name , room_name = room_name , 
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

    # process summary at the end game
    def __save__game__info__(self):
        current_datetime = datetime.datetime.today()
        current_datetime_str = current_datetime.strftime("%m_%d_%H_%M")
        with open(f"doc/game_info/{current_datetime_str}_{self.name}.jsonl" , "w" , encoding='utf-8') as f:
            for info in self.game_info:
                json.dump(info , f , ensure_ascii=False)
                f.write('\n')
    
        self.summary_generator.get_summary(file_name= f"doc/game_info/{current_datetime_str}_{self.name}.jsonl")
