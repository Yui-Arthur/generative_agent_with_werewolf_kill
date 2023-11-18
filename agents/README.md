# Game_script 產生 game_info

* 前置作業:
    * 打開 postman(https://grey-escape-89309.postman.co/workspace/My-Workspace~1cf6541f-c153-4597-8eb0-60165d1daae5/overview)
    * 前往 https://github.com/yeeecheng/werewolf_kill 更改固定角色位置和發言順序，說明在其中README.md

* step1 : 打開 ./agents/generate_script_agent.py
* step2 : 你會看到以下程式碼，以及需要改的參數:
    * player_number : 你設定的遊戲人數
    * game_script_path :  你寫好的game_script檔案位置
    * room_name : 要開的房間，現在都是以房間是空的(EMPTY)，然後加入對應數量的玩家 
```
if __name__ == "__main__":
    
    player_number = 7
    game_script_path = "doc/game_script/game1"
    api_key = "doc/secret/openai.key"
    url = "http://localhost:8001"
    room_name = "EMPTY"
    for num in range(1, player_number + 1): 
        
        script_thread = threading.Thread(target= generate_script_agent, 
            # game_script path, api_key path, url, agent_name, romm_name, color, prompt path
            args=((game_script_path, api_key, url, str(num), 
                room_name, "f9a8d4", Path("prompt/memory_stream/"))))
        script_thread.start()
        script_thread.join()
```
* step3: 執行

## game_script 格式說明(以 ./doc/game_script/game1 說明)
在game1中，會有1.jsonl、2.jsonl....7.jsonl 檔名的數字對應到玩家的號碼。
每個.jsonl中只需要填入角色需要執行的操作即可，舉例來說:
在1.jsonl中是狼人視角:
```
# 狼人夜晚發言
{"target": -1, "chat": "我想要殺玩家5號，我覺得他應該是神"}
# 狼人投票
{"target": 5, "chat": "狼人投票殺人"}
# 白天發言
{"target": -1, "chat": "大家好，我是預言家，我昨晚查驗玩家5號是好人，我會查驗他的理由是我覺得她很可疑，但現在可以證明他的清白了。這個夜晚我會查驗玩家4號或玩家7號。"}
# 白天投票
{"target": 3, "chat": "投票階段"}
# 白天遺言
{"target": -1, "chat": "大家請我說，我真的是預言家，雖然只有玩家5號相信我，我也清楚我前置位發言有點不利，但我很清楚我在做甚麼事，女巫我認為你可以直接用毒藥毒殺玩家3來打平衡，明天我認為可以著重聽玩家2、4、7的發言。"}
```
放入的格式為
```{"target: , "chat": }```
* 發言類型
```{"target": -1, "chat": "發言內容"}```
* 投票類型vote(狼人投票殺人、預言家投票)
    * 預言家查驗
    ```{"target": 要投的玩家號碼(不能放-1), "chat": "預言家查身分"}```
    * 狼人投票殺人
    ```{"target": 要投的玩家號碼(不能放-1), "chat": "狼人投票殺人"}```
* 投票類型vote_or_not(女巫技能、白天投票)
    * 女巫解藥(棄票要放)
    ```{"target": 要投的玩家號碼(放-1為棄票), "chat": "save"}```
    * 女巫毒藥
    ```{"target": 要投的玩家號碼(放-1為棄票), "chat": "poison"}```
    * 白天投票
    ```{"target": 要投的玩家號碼(放-1為棄票), "chat": "投票階段"}```
* 獵人(!!!)information是
    * 第一天夜晚與白天被投出去:先發言，再使用技能，所以順序不能錯
    * 其他夜晚: 沒有發言跟技能
    ```{"target": 4, "chat": "我是獵人，這樣大家知道3號玩家是狼了，等等就帶走3號玩家", }```
    ```{"chat": "NA", "target": 3}```




# Game_info 產生 summary

* step1: 打開 ./agents/summary.py
* step2: 你會看到以下程式碼:
    * prompt_dir 是放prompt與summary的外層檔案夾
    * file_name 只需要放入game_info檔案的名稱。實際會抓 prompt_dir/game_info/example.jsonl。
```
if __name__ == '__main__':
    s = summary(api_json="./doc/secret/openai.key", prompt_dir="./doc")
    # 產生summary，需要放入你要產生summary的檔案
    s.get_summary(file_name= "example.jsonl")
```
* step3: 執行即可

* 目前只要生成的不符合預期就不會產生summary內容


