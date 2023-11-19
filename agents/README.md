# Game_script 產生 game_info

* 前置作業:
    * 打開 [postman](https://grey-escape-89309.postman.co/workspace/My-Workspace~1cf6541f-c153-4597-8eb0-60165d1daae5/overview) 使用reset_room
    * 前往 https://github.com/yeeecheng/werewolf_kill 更改固定角色位置和發言順序，說明在其中README.md

* step1 : 打開 ./agents/generate_script_agent.py
* step2 : 你會看到以下程式碼，以及需要改的參數:
    * player_number : 你設定的遊戲人數
    * game_script_path :  你寫好的game_script檔案位置
    * room_name : 要開的房間，現在都是以房間是空的(EMPTY)，然後加入對應數量的玩家 
```
if __name__ == "__main__":
    
    player_number = 7
    game_script_path = "doc/game_script/game3"
    api_key = "doc/secret/openai.key"
    url = "http://localhost:8001"
    room_name = "EMPTY"
    for num in range(0, player_number): 
        generate_script_agent(
            player_number= player_number, script_game_path = game_script_path, 
            api_json= api_key, server_url= url, agent_name= str(num), room_name= room_name)
```
* step3: 執行

## game_script 格式說明(以 [./doc/game_script/game1](https://github.com/Sunny1928/generative-agent-in-werewolf-kill/blob/master/doc/game_script/game1/1.jsonl) 說明)
在game1中，會有agent0.jsonl、agent1.jsonl、agent2.jsonl....agent6.jsonl 檔名的數字對應到玩家的號碼(需要從0開始)。
每個.jsonl中只需要填入角色需要執行的操作即可，舉例來說:
在1.jsonl中是狼人視角:
```=jsonl
# 狼人夜晚發言
{"target": -1, "chat": "我想要殺玩家4號，我覺得他應該是神"}
# 狼人投票
{"target": 4, "chat": "狼人投票殺人"}
# 白天發言
{"target": -1, "chat": "大家好，我是預言家，我昨晚查驗玩家4號是好人，我會查驗他的理由是我覺得她很可疑，但現在可以證明他的清白了。這個夜晚我會查驗玩家3號或玩家6號。"}
# 白天投票
{"target": 3, "chat": "投票階段"}
# 白天遺言
{"target": -1, "chat": "大家請我說，我真的是預言家，雖然只有玩家4號相信我，我也清楚我前置位發言有點不利，但我很清楚我在做甚麼事，女巫我認為你可以直接用毒藥毒殺玩家2來打平衡，明天我認為可以著重聽玩家1、3、6的發言。"}
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

* Note1 : 目前[角色設置](https://github.com/Sunny1928/generative-agent-in-werewolf-kill/blob/master/doc/game_script/setting.json)為以下
```=json
{
    "玩家0": "狼人",
    "玩家1": "平民",
    "玩家2": "預言家",
    "玩家3": "狼人",
    "玩家4": "女巫",
    "玩家5": "平民",
    "玩家6": "獵人"
}
```
* Note2 : 其他範例都在 https://github.com/Sunny1928/generative-agent-in-werewolf-kill/tree/master/doc/game_script



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


