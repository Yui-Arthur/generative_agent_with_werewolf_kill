import json

with open("./logs/1.log") as f:
    contents = f.readlines()

f.close()

for i in contents:

    obj = json.loads(i)

    if "stage" in obj:
        continue

    # stage = obj["stage"].split("-")[2]




    # if "stage_description" in obj:
    #     stage_description = obj["stage_description"].split("#")[0]
    #     print()
    #     print(stage_description)

    # print("chat" in obj)
    
    if "chat" in obj:
        print(obj["chat"])
    
        # if obj["chat"] != "" :
        print(f'{obj["user"]}號玩家發言：{obj["chat"]}')

    


    

