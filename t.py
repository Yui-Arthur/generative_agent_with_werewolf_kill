from agents.intelligent_agent.intelligent_agent import intelligent_agent_test
from pathlib import Path   

if __name__ == '__main__':
    a = intelligent_agent_test(server_url = "http://localhost:8001" , openai_token=Path("doc/secret/openai.key") )
    while a.checker != False: pass