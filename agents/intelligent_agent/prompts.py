import logging
import openai
import json

class prompts:
    def __init__(self, player_id, game_info, room_setting, logger):
        self.logger : logging.Logger = logger

        self.player_id = player_id
        self.teammate = game_info['teamate']
        self.user_role = game_info['user_role']
        self.room_setting = room_setting
        self.memory = []
        self.guess_roles = []
        self.alive = [] # alive players
        self.choices = [-1] # player choices in prompts
        self.day = 0

        self.token_used = 0
        self.api_guess_roles= []
        self.api_guess_confidence= []

        # dictionary en -> ch
        self.en_dict={
            "witch":"女巫",
            "seer":"預言家",
            "werewolf":"狼人",
            "village":"村民",
            "hunter":"獵人",
        }

        for i in range(self.room_setting['player_num']):
            self.alive.append(i)

        
        # stage description and save text responding to the stage
        self.stage_detail={
            "guess_role": {
                "stage_description": "猜測玩家角色階段，你要藉由你有的資訊猜測玩家角色",
                "save": ["有", "的程度是", "，"]
            },
            "werewolf_dialogue":{
                "stage_description":"狼人發言階段，狼人和其他狼人發言",
                "save": "我在狼人階段發言"
            },
            "werewolf":{
                "stage_description":"狼人殺人階段，狼人可以殺一位玩家",
                "save": "我在狼人殺人階段投票殺"
            },
            "seer":{
                "stage_description":"猜測玩家角色階段，預言家可以查驗其他玩家的身份",
                "save": "我查驗"
            },
            "witch_save":{
                "stage_description":"女巫階段，女巫可以使用解藥救狼刀的人",
                "save": "我決定"
            },
            "witch_poison":{
                "stage_description":"女巫階段，女巫可以使用毒藥毒人",
                "save": "我決定毒"
            },
            "dialogue":{
                "stage_description":"白天發言階段，所有玩家發言",
                "save": "我發言"
            },
            "check":{
                "stage_description":"你被殺死了，請說遺言",
                "save": "我的遺言是"
            },
            "vote1":{
                "stage_description":"白天投票階段，投票最多的人將被票出遊戲",
                "save": "我票"
            },
            "vote2":{
                "stage_description":"由於上輪平票，進行第二輪白天投票階段，投票最多的人將被票出遊戲",
                "save": "我票"
            },
            "hunter":{
                "stage_description":"獵人階段，由於你被殺了，因此你可以殺一位玩家",
                "save": "我選擇殺"
            },
        }
    
        # initial prompts in the beginning
        self.init_prompt = f"""你現在是狼人殺遊戲中的一名玩家，遊戲中玩家會藉由說謊，以獲得勝利。因此，資訊為某玩家發言可能會是假的，而其他的資訊皆是真的。
其遊戲設定為{self.room_setting["player_num"]}人局，角色包含{self.room_setting["werewolf"]}位狼人、{self.room_setting["village"]}位平民、{"3" if self.room_setting["hunter"] else "2"}位神職（預言家和女巫{"和獵人" if self.room_setting["hunter"] else ""}）
你是{self.player_id}號玩家，你的角色是{self.en_dict[self.user_role]}，你的勝利條件為{"殺死所有神職或是所有平民或是狼的數量多於平民加神職的數量" if self.user_role == "werewolf" else "殺死所有狼人。"}\n"""
        
        for x in self.teammate:
            self.init_prompt += f"{x}號玩家是狼，是你的隊友。\n"

    
    def __print_memory__(self):

        self.logger.debug("Memory")
        self.logger.debug(self.__memory_to_string__())
        self.logger.debug('\n')


    def __memory_to_string__(self):

        memory_string = ''

        if len(self.memory[0]) == 0:
            memory_string += '無資訊\n'

        else: 
            for day, mem in enumerate(self.memory):
                memory_string += f'第{day+1}天\n'

                for idx, i in enumerate(mem):
                    memory_string += f'{idx+1}. {i}\n'

        return memory_string

    
    def __get_agent_info__(self):
        ret = {
            "memory" : [self.__memory_to_string__()],
            "guess_roles" : self.api_guess_roles,
            "confidence" : self.api_guess_confidence,
            "token_used" : [str(self.token_used)]
        }

        return ret

    
    def agent_process(self, data):
        ''' Agent process all the data including announcements and information '''

        if(data['stage'] == 'check_role'):
            return []

        if int(data['stage'].split('-')[0]) != self.day:
            self.day = int(data['stage'].split('-')[0])
            self.memory.append([])
        
        # show memory
        self.logger.debug("Day "+str(self.day))
        self.__print_memory__()
        
        # process announcement
        self.process_announcement(data['stage'], data['announcement'])

        # process information and return all the operations
        operations = self.process_information(data['stage'], data['information'])

        return operations




    def process_announcement(self, stage, announcements):
        ''' Process all the announcements and save them to the memory '''

        if len(announcements) == 0:
            return

        # self.logger.debug("announcements:")

        for i in announcements:
            # self.logger.debug(i)
            # 跳過自己的資料
            if i['user'][0] == self.player_id:
                continue
            
            if i['operation'] == 'chat':
                if i['description'] == '':
                    if i['user'][0] in self.alive:
                        text = f"{i['user'][0]}號玩家無發言"
                    else:
                        text = f"{i['user'][0]}號玩家無遺言"
                else:
                    text = f"{i['user'][0]}號玩家發言: {i['description']}"

            elif i['operation'] == 'died':
                self.alive.remove(i['user'][0])
                text = f"{i['user'][0]}號玩家死了"
            
            elif i['operation'] == 'role_info':
                text = f"{i['user'][0]}號玩家{i['description'].split(')')[1]}"

            else:
                text = f"{i['description']}"
            text += "。"
            self.memory[self.day-1].append(text)


    
    def process_information(self, stage, informations):
        '''
        Process all the infomations 
        1. Guess roles
        2. Generate prompts
        3. Send to Openai
        4. Extract string
        5. Save to memory
        '''

        if len(informations) == 0:
            return []
        
        day, state, prompt_type = stage.split('-')
        
        operations = []
        op_data = None
        

        self.logger.debug("Guess Roles")
        self.predict_player_roles()

        # self.logger.debug("Informations:")

        # process special case (witch)
        if prompt_type == 'witch':
            
            if informations[0]['description'] == '女巫救人':
                self.choices = informations[0]['target']

                response = self.prompts_response(prompt_type+'_save')
                res = response.split("，", 1)

                text = f"{self.stage_detail[prompt_type+'_save']['save']}{res[0]}{informations[0]['target'][0]}號玩家，{res[1]}"
                self.memory[self.day-1].append(text)

                

                # 不救，可以考慮使用毒藥
                if res[0] == '不救' and len(informations)>1:
                
                    self.choices = informations[1]['target']

                    response = self.prompts_response(prompt_type+'_poison')
                    res = response.split("，", 1)
                    who = int(res[0].split('號')[0])


                    # 使用毒藥
                    if who != -1:
                        text = f"{self.stage_detail[prompt_type+'_poison']['save']}{response}"
                        self.memory[self.day-1].append(text)
                        
                        op_data = {
                            "stage_name" : stage,
                            "operation" : informations[1]['operation'],
                            "target" : who,
                            "chat" : 'poison'
                        }
                        # operations.append(op_data)
                    

                else:
                    op_data = {
                        "stage_name" : stage,
                        "operation" : informations[0]['operation'],
                        "target" : self.choices[0],
                        "chat" : 'save'
                    }
                    # operations.append(op_data)

                    
            
            elif informations[0]['description'] == '女巫毒人':
                self.choices = informations[0]['target']

                response = self.prompts_response(prompt_type+'_poison')
                res = response.split("，", 1)
                who = int(res[0].split('號')[0])
                

                # 使用毒藥
                if who != -1:
                    text = f"{self.stage_detail[prompt_type+'_poison']['save']}{response}"
                    self.memory[self.day-1].append(text)

                    op_data = {
                        "stage_name" : stage,
                        "operation" : informations[0]['operation'],
                        "target" : who,
                        "chat" : 'poison'
                    }

            operations.append(op_data)



        else:
            for idx, i in enumerate(informations):
                # self.logger.debug(i)
                
                # update player choices in prmpts
                self.choices = i['target']

                # generate response
                if i['operation'] == 'dialogue':
                    prompt_type = 'dialogue'
                    
                response = self.prompts_response(prompt_type)
                
                # combine save text with response
                save_text = f"{self.stage_detail[prompt_type]['save']}{response}"
                send_text = f"{self.stage_detail[prompt_type]['save']}{response}"


                # process text in special cases
                if prompt_type == 'werewolf_dialogue':
                    res = response.split("，", 1)
                    if "1" in res[0]:
                        res = response.split("，", 2)
                        save_text = f"我在狼人階段發言\"我同意{res[1]}的發言\"。{res[2]}"
                        send_text = f"我同意{res[1]}的發言"
                    elif "2" in res[0]:
                        res = response.split("，", 3)
                        save_text = f"我在狼人階段發言\"我想刀{res[1]}，我覺得他是{res[2]}\"。{res[3]}"
                        send_text = f"我想刀{res[1]}，我覺得他是{res[2]}"
                    elif "3" in res[0]:
                        save_text = f"我在狼人發言階段不發言。{res[1]}"
                        send_text = f"我不發言。{res[1]}"

                elif prompt_type == 'dialogue':
                    try:
                        res_json = json.loads(response)
                        save_text = f"{self.stage_detail[prompt_type]['save']}{res_json['最終的分析']['發言']}{res_json['最終的分析']['理由']}"
                        send_text = f"{self.stage_detail[prompt_type]['save']}{res_json['最終的分析']['發言']}{res_json['最終的分析']['理由']}"

                    except Exception as e:
                        if self.player_id in self.alive:
                            save_text = '我無發言'
                            send_text = '我無發言'
                        else:
                            save_text = '我無遺言'
                            send_text = '我無遺言'
                        self.logger.warning(f"Dialogue prompts error , {e}")


                if save_text == '':
                    save_text = '無操作'


                # save operation's target
                target = -1
                if '號玩家，' in response:
                    target = int(response.split('號玩家，')[0][-1])

                # save_text += "。"
                # save text to memory
                self.memory[self.day-1].append(save_text)

                # process operation data 
                op_data = {
                    "stage_name" : stage,
                    "operation" : i['operation'],
                    "target" : target,
                    "chat" : send_text
                }
                operations.append(op_data)

        return operations 

        
            
            


    def predict_player_roles(self):
        ''' Predict and update player roles '''

        response = self.prompts_response('guess_role')
        
        self.guess_roles= []
        self.api_guess_roles= []
        self.api_guess_confidence= []

        lines = response.splitlines()

        for i in range(self.room_setting["player_num"]):
        
            [player, role, degree, reason] = lines[i].split('，', 3)
            
            # save to guess roles array
            roles_prompt = player+self.stage_detail['guess_role']['save'][0]+degree+self.stage_detail['guess_role']['save'][1]+role+self.stage_detail['guess_role']['save'][2]+reason
            self.guess_roles.append(roles_prompt)

            # send to server (if it didn't print the percentage, how much we should get?)
            self.api_guess_roles.append(role)
            try:
                d = int(degree.split('%')[0])/100
            except ValueError:
                d = 0

            self.api_guess_confidence.append(d)
        
        self.logger.debug("Get Agent Info")
        self.logger.debug(self.__get_agent_info__())


    def prompts_response(self, prompt_type):
        '''Generate response by prompts'''
        
        prompt = self.generate_prompts(prompt_type)
        self.logger.debug("Prompt: "+str(prompt))

        response = self.__openai_send__(prompt)
        self.logger.debug("Response: "+str(response))

        return response


    def player_array_to_string(self, array):

        return "、".join(f"{player_number}號" for player_number in array)
    

    def generate_prompts(self, prompt_type):
        ''' Generate all stages ptompts '''

        self.prompt = self.init_prompt

        # memory
        self.prompt += f"\n現在是第{self.day}天{self.stage_detail[prompt_type]['stage_description']}\n"
        self.prompt += f"你目前知道的資訊為:\n"
        
        if len(self.memory[0]) == 0:
            self.prompt += "無資訊\n"
        else: 
            for day, mem in enumerate(self.memory):
                self.prompt += f'第{day+1}天\n'

                for idx, i in enumerate(mem):
                    self.prompt += f'{idx+1}. {i}\n'
            

        # guess roles
        self.prompt += "\n你推測玩家的角色：\n"

        if len(self.guess_roles) == 0:
            self.prompt += "無資訊\n"
        else:
            for idx, i in enumerate(self.guess_roles):
                self.prompt += f'{i}\n'

        all_choices = "、".join(f"{player_number}號" for player_number in range(self.room_setting['player_num']))
        choices = self.player_array_to_string(self.choices)
        # question
        # [你必須知道的資訊] = 上述提供資訊內容
        stage_question={
            "guess_role": f'根據以上你知道的資訊中，判斷{all_choices}玩家的角色及你認為正確的機率百分比(直接回答"[玩家]號玩家，[角色]，[正確的機率百分比]，[原因]"，不需要其他廢話，回答完直接結束回答)',
            "werewolf_dialogue":f'''根據以上綜合資訊，你有三個選項，請選擇其中一個選項當作發言？
1. 我同意隊友的發言。請在{self.player_array_to_string(self.teammate)}號玩家中，選擇一位隊友(若選擇此選項，請直接回答"選項1，[玩家]號玩家，[原因]"，不需要其他廢話，回答完直接結束回答)
2. 想殺某位玩家，並猜測玩家的角色。從{self.player_array_to_string(self.alive)}中，只能選擇一位想殺的玩家，且從預言家和女巫{"和獵人" if self.room_setting["hunter"] else ""}中選一位你認為是此玩家的角色(若選擇此選項，請直接回答"選項2，[玩家]號玩家，[角色]，[原因]"，不需要其他廢話，回答完直接結束回答)
3. 無發言(若選擇此選項，請直接回答"選項3，[原因]"，不需要其他廢話，回答完直接結束回答)
                ''',
            "werewolf":f'根據以上綜合資訊，請從{choices}號玩家中，選擇一位要殺的玩家並簡述原因？(直接回答"[玩家]號玩家，[原因]"，不需要其他廢話，回答完直接結束回答)',
            "seer":f'根據以上綜合資訊，請問你要從{choices}號玩家中，查驗哪一位玩家並簡述原因？(直接回答"[玩家]號玩家，[原因]"，不需要其他廢話，回答完直接結束回答)',
            "witch_save":f'根據以上綜合資訊，{choices}號玩家死了，請問你要使用解藥並簡述原因？(直接回答"[救或不救]，[原因]"，不需要其他廢話，回答完直接結束回答)',
            "witch_poison":f'根據以上綜合資訊，請你從{choices}號玩家中使用毒藥，或選擇-1表示不使用毒藥，並簡述原因？(直接回答"[玩家]號玩家，[原因]"，不需要其他廢話，回答完直接結束回答)',
            "dialogue-test":f'根據以上綜合資訊，簡述你的推測（20字以下）?',
            "check":f'根據以上綜合資訊，簡述你的推測（20字以下）?',
            "dialogue":'''使用JSON的形式來回答，如下所述:
在這個回答格式中，我希望你能分析多次，以獲得更完整的想法，你要確保你每句話都能以[你目前知道的資訊]佐證，不能無中生有。並在[最終的分析]的發言，能夠清楚的表明你的立場，一定要確保發言的正確性，說話的邏輯一定不能有錯誤。
回答格式:
{   
    "分析1": {
        "想法": "你有甚麼想法?你需要以[你目前知道的資訊]佐證，不能無中生有",
        "理由": "想出這個想法的理由是甚麼?你需要以[你目前知道的資訊]佐證，不能無中生有",
        "策略": "有了這個想法，你會怎麼做?",
        "批評": "對於想法與策略有甚麼可以批評與改進的地方或是有甚麼資訊是你理解錯誤的，請詳細說明",
    },
    "分析2": {
        "反思": "對於前一個想法的批評內容，你能做甚麼改進?你需要以[你目前知道的資訊]佐證，並思考活著玩家可疑的地方，不能無中生有。",
        "想法": "根據反思，你有甚麼更進一步的想法?你需要以[你目前知道的資訊]佐證，不能無中生有",
        "理由": "想出這個想法的理由是甚麼?你需要以[你目前知道的資訊]佐證，不能無中生有",
        "策略": "有了這個想法，你會怎麼做?",
        "批評": "對於想法與策略有甚麼可以批評與改進的地方或是有甚麼資訊是你理解錯誤的，請詳細說明",
    },
    ...(你能夠思考N次，以獲得更完整的發言)
    "最終的分析":{
        "反思": "對於前一個想法的批評內容，你能做甚麼改進?你需要以[你目前知道的資訊]佐證，並思考活著玩家可疑的地方，不能無中生有。",
        "想法": "根據反思，你有甚麼更進一步的想法?你需要以[你目前知道的資訊]佐證，不能無中生有",
        "理由": "想出這個想法的理由是甚麼?你需要以[你目前知道的資訊]佐證，不能無中生有",
        "策略": "有了這個想法，你會怎麼做?",
        "發言": "(請直接呈現你說的話即可，不添加其他附加訊息)"
    }
}
請保證你的回答可以(直接被 Python 的 json.loads 解析)，且你只提供 JSON 格式的回答，不添加其他附加信息。''',
            "vote1":f'根據以上綜合資訊，請你從{choices}號玩家中選一位投票，或選擇-1表示棄票，並簡述原因？(直接回答"[玩家]號玩家，[原因]"，不需要其他廢話，回答完直接結束回答)',
            "vote2":f'根據以上綜合資訊，請你從{choices}號玩家中選一位投票，或選擇-1表示棄票，並簡述原因？(直接回答"[玩家]號玩家，[原因]"，不需要其他廢話，回答完直接結束回答)',
            "hunter":f'根據以上綜合資訊，請你從{choices}號玩家中選一位殺掉，或選擇-1表示棄票，並簡述原因？(直接回答"[玩家]號玩家，[原因]"，不需要其他廢話，回答完直接結束回答)',
        }
    
        self.prompt += '\nQ:'
        self.prompt += stage_question[prompt_type]
        self.prompt += '\nA:'

        # print(self.prompt)
        
        return self.prompt
    
        
    
    def __openai_send__(self , prompt):
        """ openai api send prompt , can override this. """
        
        response = openai.Completion.create(
            engine="gpt-35-turbo", # this will correspond to the custom name you chose for your deployment when you deployed a model.      
            prompt=prompt, 
            max_tokens=2000, 
            temperature=0.7, 
            stop="\n\n")
        
        self.token_used += response["usage"]["total_tokens"]
        
        res = response['choices'][0]['text']
        
        # if res == '' (no words), resend to get the data
        if not (res and res.strip()):
            res = self.__openai_send__(prompt)

        # cut unused string (ex. <|end|>)
        if '<' in res:
            res = res.split('<',1)[0]

        # cut unused string (ex. """)
        if '\"' in res:
            res = res.split('\"',1)[0]

        # cut unused string (ex. """)
        if '`' in res:
            res = res.split('`',1)[0]
        
        
        
        return res

    
