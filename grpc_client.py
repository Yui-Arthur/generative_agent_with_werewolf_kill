import grpc
from protobufs.agent_pb2 import agent_query , agent_state , empty
import protobufs.agent_pb2_grpc as agent_pb2_grpc
import threading
from concurrent import futures
from memory_stream_agent import memory_stream_agent
from pathlib import Path
import time

channel = grpc.insecure_channel("localhost:50052")
client  = agent_pb2_grpc.agentStub(channel)

request = agent_query(agentType = "memory_stream_agent" , agentName = "Test1" , roomName = "TESTROOM" , apiBase = "" , engine = "",
                       keyPath = "doc/secret/openai.key" , color = "f9a8d4"  ,promptDir = "doc/prompt/memory_stream/")

rel = client.create_agent(request)
print(rel)

# time.sleep(5)

# request = agent_state(agentID = 0)
# rel = client.delete_agent(request)