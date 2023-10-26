import grpc
from protobufs.agent_pb2 import agent_query , agent_state , empty , agent_state , agent_info
import protobufs.agent_pb2_grpc as agent_pb2_grpc
import threading
from concurrent import futures
from pathlib import Path
import argparse
from agents import memory_stream_agent , intelligent_agent , agent
from sentence_transformers import SentenceTransformer, util
import threading

class agent_service(agent_pb2_grpc.agentServicer):
    
    def __init__(self , server_ip , agent_dict):
        self.agent_type_dict = {
            "memory_stream_agent" : memory_stream_agent , 
            "intelligent_agent" : intelligent_agent
        }
        self.agent_dict : dict[int , agent] = agent_dict
        self.agent_idx = 1
        self.server_ip = server_ip
        
    def create_agent(self , request , context):
        
        print(request)
        agent_type = request.agentType
        agent_name = request.agentName
        room_name = request.roomName 
        api_json = request.apiJson
        color = request.color
        prompt_dic = request.promptDir
        

        agent = self.agent_type_dict[agent_type](agent_name=agent_name , room_name=room_name,
                                                 color=color, api_json = api_json, 
                                                 prompt_dir=prompt_dic , server_url = self.server_ip)
        
        self.agent_dict[self.agent_idx] = agent
        self.agent_idx +=1
        return agent_state(agentID = self.agent_idx -1)
    
    def delete_agent(self , request , context):
        print(f"Delete Agent with {request}")
        agent_id = request.agentID
        
        if agent_id not in self.agent_dict.keys():
            context.abort(grpc.StatusCode.NOT_FOUND, "Agent not found")

        self.agent_dict[agent_id].stop_agent()
        del self.agent_dict[agent_id]
        
        return empty()
    
    def get_agent_info(self , request , context):
        print(f"Get Info with {request}")
        agent_id = request.agentID

        if agent_id == -1:
            return agent_info(agentInfo = {"This is test agent grpc server state , you should not send the agentID less then 0" : "!"})

        if agent_id not in self.agent_dict.keys():
            context.abort(grpc.StatusCode.NOT_FOUND, "Agent not found")
        if self.agent_dict[agent_id].game_over == True:
            del self.agent_dict[agent_id]
            context.abort(grpc.StatusCode.NOT_FOUND, "The game of the agent is end")

        return agent_info(agentInfo = self.agent_dict[agent_id].get_info())
    
def print_agent_dict(agent_dict : dict[str , agent]):

    for id in list(agent_dict.keys()):
        if agent_dict[id].game_over == True: 
            del agent_dict[id]
        else:
            print(f"agent name : {agent_dict[id].name} room : {agent_dict[id].room}")

    threading.Timer(60 , print_agent_dict , args=[agent_dict]).start()

def serve(opt):

    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    del model
    agent_dict = {}
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    agent_pb2_grpc.add_agentServicer_to_server((agent_service(opt["api_server"] , agent_dict)), server)
    print(f'server start with api server : {opt["api_server"]}')
    
    server.add_insecure_port("[::]:50052")
    print_agent_dict(agent_dict)
    server.start()

    server.wait_for_termination()

def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--api_server' , type=str, default="http://localhost:8001" , help='server ip')
    opt = parser.parse_args()

    return opt


if __name__ == '__main__':
    opt = parse_opt()
    serve(vars(opt))