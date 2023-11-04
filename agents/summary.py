import logging
import json
import openai
import re
import requests
from pathlib import Path  

class summary():
    def __init__(self , logger , engine , server_url = "140.127.208.185" , room_name = "TESTROOM" ,prompt_dir = "doc/prompt/summary"):
        self.max_fail_cnt = -1
        self.token_used = 0
        self.prompt_template : dict[str , str] = None
        self.example : dict[str , str] = None
        self.chinese_to_english = {
            # summary
            "總結" : "summary"
        }
        self.role_to_chinese = {
            "seer" : "預言家",
            "witch" : "女巫",
            "village" : "村民",
            "werewolf" : "狼人",
            "hunter" : "獵人"
        }
        self.engine = engine
        self.server_url = server_url
        self.room_name = room_name
        self.logger : logging.Logger = logger
        self.prompt_dir = Path(prompt_dir)
        self.__load_prompt_and_example__(self.prompt_dir)

    