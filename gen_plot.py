import json
import numpy as np
import matplotlib.pyplot as plt

file_names = ["simple_agent_script.jsonl", "summary_intelligent_agent_script.jsonl", "intelligent_agent_script.jsonl", "memory_stream_agent_script.jsonl", "summary_memory_stream_agent_script.jsonl"]
agent_type = ["simple_agent_script", "summary_intelligent_agent_script", "intelligent_agent_script", "memory_stream_agent_script", "summary_memory_stream_agent_script"]
row_data = []

all_agent_info = {}

def get_each_game_token_used(all_agent_info):

    game_token_used = { agent: {f"game{i}": 0 for i in range(1, 11) if i != 3} for agent in agent_type}
    
    for agent in agent_type:
        for raw_data in all_agent_info[agent]["raw_data"]:
            game = raw_data["scr_game_info"].split("_")[0]
            game_token_used[agent][game] += raw_data["token_used"]

    return game_token_used

def show_game_token_used(all_agent_info):


    game_token_used = get_each_game_token_used(all_agent_info)
    games = [f"game{i}" for i in range(1, 11) if i != 3]
    
    color = ['#b6d7a8' , '#c9daf8' , '#ffe599' , '#f4cccc' , '#d9d2e9']
    width = 0.13
    x = np.arange(len(games))
    for i in range(5):
        plt.bar(x + i*width , [game_token_used[agent_type[i]][f"game{j}"] for j in range(1, 11) if j != 3], width, color = color[i], label= agent_type[i])


    # 設定x軸的標籤
    plt.xticks(x + width, games)

    # 顯示圖例
    plt.legend()

    # plt.bar(x,h,color='b',width=0.4, align='edge')  # 第一組數據靠左邊緣對齊
    # plt.bar(x2,h2,color='r',width=0.4)              # 第二組數據置中對齊
    plt.show()


def show_role_token_used(all_agent_info):
    # agent_game_role_info = {}
    # game_role_info = load_game_score(path, agent_game_role_info)

    # x_game_data = [[] for _ in role_list.keys()]  
    # for game_id , game_info in game_role_info[agent_type].items():
    #     for role_id , role_info in enumerate(game_info):
    #         x_game_data[role_id].append(role_info['avg_acc'])
    #     # break
    # width = 0.13  # Adjust the width to accommodate more bars
    # color = ['#b6d7a8' , '#c9daf8' , '#ffe599' , '#f4cccc' , '#d9d2e9']
    # print(x_game_data)
    # x = np.arange(len(x_game_data[0]))
    # print(len(x_game_data))
    # print(len(x_game_data[0]))
    # for i in range(-2,3):
    #     role_idx = i+2
    #     plt.bar(x + 1.1*i*width ,x_game_data[role_idx] , width ,color = color[role_idx] , label=role_list[role_idx])
    
    # for game_id , game_info in game_role_info[agent_type].items():
    #     all_role_acc = [role_info['avg_acc'] for role_id , role_info in enumerate(game_info)]
    #     avg_acc = sum(all_role_acc) / len(all_role_acc)
    #     plt.plot([game_id - 2.5 * width, game_id + 2.5 * width], [avg_acc , avg_acc], color='red', linestyle='--', linewidth=1)

    # plt.grid(axis='y', alpha=0.7, which='major', color='gray', linewidth=0.5, dashes=(5, 2))

    # plt.xticks(x , [f"game{_}" for _ in range(1, len(x_game_data[0])+1)], fontsize=15)
    # # plt.ylabel('Scores', fontsize=15)
    # plt.yticks(fontsize=15)
    # plt.title("123", fontsize=25)
    # plt.legend(loc='upper right')
    # plt.show()
    pass

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

show_game_token_used(all_agent_info)


