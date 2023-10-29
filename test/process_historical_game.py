import json

with open("./logs/2.log") as f:
    contents = f.readlines()

f.close()

for i in contents:

    obj = json.loads(i)

    # if "stage" not in obj:
    #     continue

    # stage = obj["stage"].split("-")[2]

    if "prev_vote" in obj:

        if obj["prev_vote"] != {}:

            print()
            print("投票結果：")
            
            for i in obj["prev_vote"]:
                
                if obj["prev_vote"][i] == -1:
                    print(f'{i}號玩家棄票')
                else:
                    print(f'{i}號玩家投{obj["prev_vote"][i]}號玩家')

    
    if "announcement" in obj:

        if obj["announcement"] != []:
            
            for i in obj["announcement"]:
                
                if i['operation']!='chat':
                    print(f'{i["description"]}')

            print()
            



    if "stage_description" in obj:
        stage_description = obj["stage_description"].split("#")[0]
        print()
        print(f'[{stage_description}]')

    
        
    

    if "operation" in obj:

        if obj["operation"] == "vote":
            print(f'{obj["user"]}號玩家選擇{obj["target"]}號玩家')

    if "chat" in obj:
    
        if obj["chat"] != "" :
            print(f'{obj["user"]}號玩家發言: {obj["chat"]}')

    


    

