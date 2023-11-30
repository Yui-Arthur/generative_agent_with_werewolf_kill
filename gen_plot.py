import json
import numpy as np
import matplotlib.pyplot as plt

file_names = ["simple_agent_script.jsonl", "intelligent_agent_script.jsonl", "memory_stream_agent_script.jsonl", "summary_intelligent_agent_script.jsonl", "summary_memory_stream_agent_script.jsonl"]
agent_type = ["simple_agent_script", "intelligent_agent_script", "memory_stream_agent_script", "summary_intelligent_agent_script",  "summary_memory_stream_agent_script"]
agent_simply_name = ["BA", "IA", "MA", "IA-E", "MA-E"]
role_list = ["werewolf", "village", "seer", "witch", "hunter"]
id2role_list = [0, 1, 2, 0, 3, 1, 4]
all_agent_info = {}

def get_each_game_token_used(all_agent_info):

    game_token_used = { agent: {f"game{i}": [0, 0, 0] for i in range(1, 11) if i != 3} for agent in agent_type}
    
    for agent in agent_type:
        for raw_data in all_agent_info[agent]["raw_data"]:
            game = raw_data["scr_game_info"].split("_")[0]
            game_token_used[agent][game][0] += raw_data["token_used"]
            game_token_used[agent][game][1] += 1
        for i in range(1, 11):
            if i == 3: continue
            game_token_used[agent][f"game{i}"][2] = game_token_used[agent][f"game{i}"][0] / game_token_used[agent][f"game{i}"][1]
    for i in range(1, 11):
        if i == 3: continue
        game_token_used["summary_memory_stream_agent_script"][f"game{i}"][2] += (game_token_used["summary_intelligent_agent_script"][f"game{i}"][2] - game_token_used["intelligent_agent_script"][f"game{i}"][2])
    return game_token_used

def get_agent_role_token_used(all_agent_info):

    game_token_used = { agent: {role: [0, 0, 0] for role in role_list  } for agent in agent_type}
    
    for agent in agent_type:

        for raw_data in all_agent_info[agent]["raw_data"]:
            role_id = int(raw_data["scr_game_info"].split("_")[1])
            game_token_used[agent][role_list[id2role_list[role_id]]][0] += raw_data["token_used"]
            game_token_used[agent][role_list[id2role_list[role_id]]][1] += 1
        
        for i in range(5):
            game_token_used[agent][role_list[i]][2] = game_token_used[agent][role_list[i]][0] / game_token_used[agent][role_list[i]][1]
    for i in range(5):
        game_token_used["summary_memory_stream_agent_script"][role_list[i]][2] += (game_token_used["summary_intelligent_agent_script"][role_list[i]][2] - game_token_used["intelligent_agent_script"][role_list[i]][2])

    return game_token_used

def show_game_token_used(all_agent_info):

    game_token_used = get_each_game_token_used(all_agent_info)
    games = [f"game{i}" for i in range(1, 11) if i != 3]
    
    color = ['#b6d7a8' , '#c9daf8' , '#ffe599' , '#f4cccc' , '#d9d2e9']
    width = 0.13
    x = np.arange(len(games))
    for i in range(5):
        plt.bar(x + i*width , [game_token_used[agent_type[i]][f"game{j}"][2] / 1000 for j in range(1, 11) if j != 3], width, color = color[i], label= agent_simply_name[i])

    for i in range(1, 11):
        if i == 3: continue
        y_value = [game_token_used[agent_type[j]][f"game{i}"][2] / 1000 for j in range(5)]   
        average = np.mean(y_value)
        k = i - 2 if i > 3 else i - 1
        print(k)
        plt.hlines(y=average, xmin= x[k] - width, xmax= x[k] + 5 * width, color='r', linestyle='--')

    plt.grid(axis='y', alpha=0.7, which='major', color='gray', linewidth=0.5, dashes=(5, 2))
    plt.xticks(x + 2 * width, games, fontsize=23)
    plt.yticks(fontsize=23)
    plt.legend(loc = "upper left")
    plt.show()

def show_agent_role_token_used(all_agent_info):
    game_token_used = get_agent_role_token_used(all_agent_info)
    games = [agent_name for agent_name in agent_simply_name]
    color = ['#b6d7a8' , '#c9daf8' , '#ffe599' , '#f4cccc' , '#d9d2e9']
    width = 0.13
    x = np.arange(len(games))
    for i in range(5):
        plt.bar(x + i*width , [game_token_used[agent_type[j]][role_list[i]][2] / 1000 for j in range(5)], width, color = color[i], label= role_list[i], align= "center")

    for i in range(5):
        y_value = [game_token_used[agent_type[i]][role_list[j]][2] / 1000 for j in range(5)]    
        average = np.mean(y_value)
        plt.hlines(y=average, xmin= x[i] - width, xmax= x[i] + 5 * width, color='r', linestyle='--')

    plt.grid(axis='y', alpha=0.7, which='major', color='gray', linewidth=0.5, dashes=(5, 2))
    plt.xticks(x + 2 * width, games, fontsize=23)
    plt.yticks(fontsize=23)
    plt.legend(loc = "upper left")
    plt.show()

def show_role_agent_token_used(all_agent_info):
    game_token_used = get_agent_role_token_used(all_agent_info)
    games = [role for role in role_list]
    color = ['#b6d7a8' , '#c9daf8' , '#ffe599' , '#f4cccc' , '#d9d2e9']
    width = 0.13
    x = np.arange(len(games))
    for i in range(5):
        plt.bar(x + i*width , [game_token_used[agent_type[i]][role_list[j]][2] / 1000 for j in range(5)], width, color = color[i], label= agent_simply_name[i], align= "center")
    
    for i in range(5):
        y_value = [game_token_used[agent_type[j]][role_list[i]][2] / 1000 for j in range(5)]    
        average = np.mean(y_value)
        plt.hlines(y=average, xmin= x[i] - width, xmax= x[i] + 5 * width, color='r', linestyle='--')
        
    plt.grid(axis='y', alpha=0.7, which='major', color='gray', linewidth=0.5, dashes=(5, 2))
    plt.xticks(x + 2 * width, games, fontsize=23)
    plt.yticks(fontsize=23)
    plt.legend(loc = "upper left")
    plt.show()


def cal_performance(self, all_agent_info):
    IA_decrease = abs(all_agent_info["simple_agent_script"]["avg_token"] - all_agent_info["intelligent_agent_script"]["avg_token"]) / all_agent_info["simple_agent_script"]["avg_token"]
    MA_increase = abs(all_agent_info["simple_agent_script"]["avg_token"] - all_agent_info["memory_stream_agent_script"]["avg_token"]) / all_agent_info["simple_agent_script"]["avg_token"]
    ISA_increase = abs(all_agent_info["summary_intelligent_agent_script"]["avg_token"] - all_agent_info["intelligent_agent_script"]["avg_token"]) / all_agent_info["intelligent_agent_script"]["avg_token"]
    MSA_increase = abs(all_agent_info["summary_memory_stream_agent_script"]["avg_token"] - all_agent_info["memory_stream_agent_script"]["avg_token"]) / all_agent_info["memory_stream_agent_script"]["avg_token"]
    print("IA_decrease compared to BA: ",IA_decrease)
    print("MA_increase compared to BA: ",MA_increase)
    print("ISA_increase compared to IA: ",ISA_increase)
    print("MSA_increase compared to MA: ",MSA_increase)


for file_name in agent_type:

    with open(f"./data/{file_name}.jsonl" , encoding="utf-8") as json_file: 
        raw_data = [json.loads(line) for line in json_file.readlines()]
        all_agent_info[file_name] = {}
        all_agent_info[file_name]["raw_data"] = raw_data

# diff all agent    
for file_name in agent_type:
    cnt  = 0
    for data in all_agent_info[file_name]["raw_data"]:
        cnt += data["token_used"]
    all_agent_info[file_name]["total_token"] = cnt
    all_agent_info[file_name]["total_play"] = len(all_agent_info[file_name]["raw_data"])
    all_agent_info[file_name]["avg_token"] = all_agent_info[file_name]["total_token"] / all_agent_info[file_name]["total_play"]
    

# process summary memory token
all_agent_info["summary_memory_stream_agent_script"]["total_token"] += (all_agent_info["summary_intelligent_agent_script"]["total_token"] - all_agent_info["intelligent_agent_script"]["total_token"])

# diff each role
for file_name in agent_type:
    for i in range(0,7):
        all_agent_info[file_name][str(i)] = 0
    
    for i in range(0,7):
        for data in all_agent_info[file_name]["raw_data"]:
            all_agent_info[file_name][str(i)] +=  data["token_used"] if data["scr_game_info"].split("_")[-1] == str(i) else 0

for i in range(0,7):
    all_agent_info["summary_memory_stream_agent_script"][str(i)] += (all_agent_info["summary_intelligent_agent_script"][str(i)] - all_agent_info["intelligent_agent_script"][str(i)])


for file_name in agent_type:
    print(file_name, all_agent_info[file_name]["avg_token"])

# x: game
show_game_token_used(all_agent_info)
# x: agent
show_agent_role_token_used(all_agent_info)
# x: role
show_role_agent_token_used(all_agent_info)


