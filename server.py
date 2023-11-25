import grpc
from protobufs.agent_pb2 import agent_query , agent_state , empty , agent_state , agent_info , info_list
import protobufs.agent_pb2_grpc as agent_pb2_grpc
import threading
from concurrent import futures
from pathlib import Path
import argparse
from agents import memory_stream_agent , intelligent_agent , agent, summary_intelligent_agent , summary_memory_stream_agent
from sentence_transformers import SentenceTransformer, util
import threading
import time
import datetime

class agent_service(agent_pb2_grpc.agentServicer):
    
    def __init__(self , server_ip , agent_dict):
        self.agent_type_dict = {
            "memory_stream_agent" : memory_stream_agent , 
            "intelligent_agent" : intelligent_agent,
            "summary_memory_stream_agent" : summary_memory_stream_agent,
            "summary_intelligent_agent" : summary_intelligent_agent,
            "simple_agent" : agent
        }
        self.agent_dict : dict[int , dict[str : agent | float]] = agent_dict
        self.agent_idx = 1
        self.server_ip = server_ip
        
    def create_agent(self , request , context):
        
        agent_type = request.agentType
        agent_name = request.agentName
        room_name = request.roomName 
        api_json = request.apiJson
        color = request.color
        prompt_dic = request.promptDir
        
        try:
            agent = self.agent_type_dict[agent_type](agent_name=agent_name , room_name=room_name,
                                                    color=color, api_json = api_json, 
                                                    prompt_dir=prompt_dic , server_url = self.server_ip)
        except Exception as e :
            context.abort(grpc.StatusCode.NOT_FOUND, f"Init Agent Error with {e}")
        
        self.agent_dict[self.agent_idx]  = {
            "agent_instance"  : agent,
            "create_timestamp" : time.time(),
        } 
        print(f"Create Agent :\n{request}{self.agent_idx}")
        self.agent_idx +=1
        return agent_state(agentID = self.agent_idx -1)
    
    def delete_agent(self , request , context):
        print(f"Delete Agent with {request}")
        agent_id = request.agentID
        
        if agent_id not in self.agent_dict.keys():
            context.abort(grpc.StatusCode.NOT_FOUND, "Agent not found")

        self.agent_dict[agent_id]['agent_instance'].__del__()
        del self.agent_dict[agent_id]
        
        return empty()
    
    def get_agent_info(self , request , context):
        agent_id = request.agentID

        # api server testing the agent server
        if agent_id == -1:
            return agent_info(agentInfo = {"This is test agent grpc server state , you should not send the agentID less then 0" : info_list(info = ["!"])})
        
        print(f"Get Info with {agent_id}")
        if agent_id not in self.agent_dict.keys():
            context.abort(grpc.StatusCode.NOT_FOUND, "Agent not found")
            
        if self.agent_dict[agent_id]['agent_instance'].game_over == True:
            del self.agent_dict[agent_id]
            context.abort(grpc.StatusCode.NOT_FOUND, "The game of the agent is end")

        return agent_info(agentInfo = {key: info_list(info = value)for key , value in self.agent_dict[agent_id]['agent_instance'].get_info().items()})
    
def print_agent_dict(agent_dict : dict[str , agent]):
    print("agent name | room name")
    for id in list(agent_dict.keys()):
        start_time = datetime.datetime.fromtimestamp(agent_dict[id]['create_timestamp'])
        now = datetime.datetime.now()
        # if agent is game over or the time is over 30mins delete it
        if agent_dict[id]['agent_instance'].game_over == True or (now-start_time).total_seconds() > 1800: 
            print(f"delete {agent_dict[id]['agent_instance'].name} , {agent_dict[id]['agent_instance'].room}")
            del agent_dict[id]
        else:
            print(f"{agent_dict[id]['agent_instance'].name} , {agent_dict[id]['agent_instance'].room}")
    print("-----------------------")
    
    global thread_id
    thread_id = threading.Timer(60 , print_agent_dict , args=[agent_dict])
    
    thread_id.start()
    

def serve(opt):

    agent_dict = {}
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
    agent_pb2_grpc.add_agentServicer_to_server((agent_service(opt["api_server"] , agent_dict)), server)
    print(f'server start with api server : {opt["api_server"]}')
    
    server.add_insecure_port("[::]:50052")

    global thread_id
    thread_id = None

    print_agent_dict(agent_dict)
    server.start()
    
    if not opt["docker"]:
        input()
        thread_id.cancel()
    else:
        print('use docker deploy')

    server.wait_for_termination()
    

def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--api_server' , type=str, default="http://localhost:8001" , help='server ip')
    parser.add_argument('--docker' , action="store_true" , help='whether use docker to deploy')
    opt = parser.parse_args()

    return opt


if __name__ == '__main__':
    opt = parse_opt()
    serve(vars(opt))