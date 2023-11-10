from agent import agent
from pathlib import Path   
from summary import summary

class summary_agent(agent):
    
    def __init__(self , openai_token = None , api_base = "https://wolf-openai-llm.openai.azure.com/" , engine = "agent", api_json = "doc/secret/yui.key", 
                server_url = "140.127.208.185" , agent_name = "Agent1" , room_name = "TESTROOM" , 
                color = "f9a8d4" , prompt_dir = Path("prompt/memory_stream/")):
        
        
        super().__init__(openai_token = openai_token, api_base = api_base , engine = engine, api_json = api_json,
                        server_url = server_url , agent_name = agent_name , room_name = room_name , 
                        color = color) 
        
        self.summary_generator = summary(logger= self.logger, api_json = api_json)

    def __process_data__(self , data):
        """the data process , must override this."""

        cur_stage = data['stage'].split("-")[0]
        
        # 狼人發言、一般人發言
        if cur_stage in ["dialogue", "werewolf_dialogue"]:
            stage = "dialogue"
        # 狼人投票、一般人投票
        elif cur_stage in ["werewolf", "vote1", "vote2"] :
            stage = "vote"
        # 預言家、女巫、獵人
        elif cur_stage in ["seer", "witch", "hunter"]:
            stage = "operation"
        
        self.similarly_sentences = self.summary_generator.find_similarly_summary(stage, game_info = self.game_info)
        
        if(len(data['information']) == 0):
            return
        
        # time.sleep(2)
        op_data = {
            "stage_name" : data['stage'],
            "operation" : data['information'][0]["operation"],
            "target" : -1,
            "chat" : "123"
        }
        self.__send_operation__(op_data)