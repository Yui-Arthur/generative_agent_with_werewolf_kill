import pandas as pd
import json
raw_data = pd.read_csv("./human_sheet.csv")

record_x_by_agent = {num:[] for num in range(8)}

guess_map_score = {
    "預言家" : ["好人", "預言家"],
    "狼人" : ["狼人"],
    "女巫" : ["好人", "女巫"],
    "獵人" : ["好人", "獵人"],
    "平民" : ["好人", "平民"],
}

answer_list = ["狼人", "平民", "預言家", "狼人", "女巫", "平民", "獵人"]
game_round = [2, 2, 2, 2, 2, 2, 3, 3, 2]

save_file = "./human_script.jsonl"

for num in range(8):
    game_round_copy = game_round.copy()
    game_round_idx = 0
    for idx in range(3, len(raw_data.iloc[num]), 7):
        if game_round[game_round_idx] == game_round_copy[game_round_idx]:
            same_game = []
        score = 0
        for answer_idx in range(len(answer_list)):
            ans = answer_list[answer_idx]
            guess = raw_data.iloc[num][idx: idx+7][answer_idx]
            if guess in guess_map_score[ans]:
                if len(guess_map_score[ans]) == 2:
                    score += 0.5 if guess == "好人" else 1
                else:
                    score += 1 if guess == "狼人" else 0
        same_game.append(score / 7)
        game_round_copy[game_round_idx] -= 1
        if game_round_copy[game_round_idx] == 0:
            game_round_idx += 1
            record_x_by_agent[num].append(same_game)
            result_dic = {
                "agent_type" : "human",
                "scr_game_info" : f"game{game_round_idx}_{num + 1}",
                "all_acc" : same_game,
                "all_operation" : [],
                "token_used" : 0
            }
            with open(save_file , 'a+' , encoding='utf-8') as f :
                json.dump(result_dic , f , ensure_ascii=False)
                f.write('\n')



    
