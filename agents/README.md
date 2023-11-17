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

* 目前只要生成的不符合預期就不會產生summary內容