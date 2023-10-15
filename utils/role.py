from utils.long_memory_stream import long_memeory_stream

import json

class role(long_memeory_stream):

    def __init__(self , prompt_dir , logger):
        super().__init__(prompt_dir, logger)
        
    def update_game_info(self , player_name , role):
        super().update_game_info(player_name, role)
        role_to_func =  {
            "werewolf" : self.__werewolf_process__,
            "seer" : self.__seer_process__,
            "witch" : self.__witch_process__,
            "hunter" : self.__hunter_process__
        }

        self.role_processs = role_to_func[self.role]

    def __processs_information__(self , data):
        super().__processs_information__(data)
        

    def __werewolf_process__(self):
        pass

    def __seer_process__(self):
        pass

    def __hunter_process__(self):
        pass

    def __witch_process__(self):
        pass

    def __load_prompt_and_example__(self , prompt_dir):
        """load prompt json to dict"""
        super().__load_prompt_and_example__(prompt_dir)

        self.logger.debug(f"load {self.role} json")
        with open(prompt_dir / f"{self.role}_prompt.json" , encoding="utf-8") as json_file: self.prompt_template.update(json.load(json_file))
        with open(prompt_dir / f"{self.role}_example.json" , encoding="utf-8") as json_file: self.example.update(json.load(json_file))
        
        for key , prompt_li in self.prompt_template.items():
            self.prompt_template[key] = '\n'.join(prompt_li)
        for key , prompt_li in self.example.items():
            self.example[key] = '\n'.join(prompt_li)