import json

with open("./logs/1.log") as f:
    contents = f.readlines()

f.close()

for i in contents:
    obj = json.loads(i)
    # print(obj)
    if "chat" in obj:
        print()
        print(f'{obj["user"]}號玩家發言：{obj["chat"]}')