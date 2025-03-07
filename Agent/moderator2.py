import json
import time


from Agent.agent import Agent

from backend.api import api_call


from Interaction.messagepool import message_pool

class Moderator(Agent):
    _name = "moderator"
    def __init__(self,name:str = None, model:str = "deepseek-chat"):
        super().__init__(name = name if name is not None else _name, model = model)

        self.user_message = None
        

    def generate_o1_response(self,question):
        ref = None
        if ref is None:
            ref = ""
        
        messages = [
            {"role": "system", "content": """
你是一个多步思考专家，专门解决多步推理问题。多步问题的定义为，问题以及给定的信息复杂，难以一次性推理出正确答案，而需要反复查找给定的信息进行多步推理。根据用户给定的问题，你需要给出一个规划，包含每一步需要获取哪些信息，最终得到什么信息。例如，用户询问喜欢吃花生且今晚吃了花生的人中谁喜欢打篮球。那么就需要规划三步推理：step 1：确定谁喜欢吃花生-- 返回 一个人员列表 A。step 2：确定喜欢吃花生的人中谁今晚吃了花生--返回一个人员列表 B，step 3: 确定 B 中谁喜欢打篮球-- 返回一个人员列表 C，即最终答案。当前你需要规划好所有的推理步骤，并返回第一个 step，严格按照 json 格式返回。
返回的 json 数据包含三个键： 
+ "step": "当前推理步骤目标是什么，需要获取什么信息，以及会得到什么预期结果"。
+ "reasoning": "你需要根据推理目标，逐步思考，从问题中检索相关信息，给出具体地推理过程而不只是描述做法，最终得到当前步骤的推理结果。"。
+ "next_action": "给出下一步的 step 的内容，即下一步的推理步骤目标是什么，需要获取什么信息，以及会得到什么预期结果。如果你认为已经得出了正确答案，直接返回'fianl_answer'"

例如针对问题"喜欢吃花生且今晚吃了花生的人中谁喜欢打篮球"，返回样例如下：
{
    "step": "确定谁喜欢吃花生？",
    "reasoning": "根据给定信息，bob 和 tom 喜欢吃花生",
    "next_action": "判断 bob 和 tom 里谁今晚吃了花生。"
}
"""},
            {"role": "user", "content": question},
            {"role": "assistant", "content": "谢谢！我现在会按照我的指示一步一步地思考。"}
        ]
 
        steps = []
        step_count = 1
        total_thinking_time = 0

        while True:
            if self.user_message is not None:
                messages.append({"role": "user", "content": json.dumps(self.user_message,ensure_ascii=False)})
                print(messages)
            start_time = time.time()
            while True:
                try:
                    step_data = api_call(messages, model=self.model, temperature= self.args.temperature ,max_tokens =2048,json_format=True)
                    assert 'step' in (step_data.keys()) , "invalid output"
                    break
                except:
                    continue
                
            end_time = time.time()
            thinking_time = end_time - start_time
            total_thinking_time += thinking_time
            # if step_count == 1:

            #     step_data = {"title": "Step 1: Identifying Key Information", "content": "I think I can't answer this question as the knowledge didn't conatain the related.", "next_action":"continue"}
            steps.append((f"Step {step_count}: {step_data['step']}", step_data['reasoning'], thinking_time))
            ref = step_data['next_action']
            messages.append({"role": "assistant", "content": json.dumps(step_data,indent=4, ensure_ascii=False)})
            if ref is not None:
                messages.append({"role": "user", "content": f"好的，下一步你需要往{ref}方向进行推理，严格按照指令的 JSON 格式返回。不能返回空字符串。"})
                print(f"好的，下一步你需要往{ref}方向进行推理，严格按照指令的 JSON 格式返回。不能返回空字符串。")


            if step_data['next_action'] == 'final_answer' or step_count > 25: # Maximum of 25 steps to prevent infinite thinking time. Can be adjusted.
                break

            step_count += 1

            # Yield after each step for Streamlit to update
            yield steps, None  # We're not yielding the total time until the end

        # Generate final answer
        messages.append({"role": "user", "content": "Please provide a final answer based on the above reasoning only. Please do not use JSON formatting. Please provide plain text responses without any headings or preambles, and do not add any repetitive or redundant questions or punctuation. Retain any formatting indicated in the original prompt, such as free response or multiple choice exact formatting."})
        start_time = time.time()
        final_data = api_call(messages, self.model, self.args.temperature, 300,json_format=False)
        end_time = time.time()
        thinking_time = end_time - start_time
        total_thinking_time += thinking_time

        steps.append(("Final Answer", final_data, thinking_time))

        yield steps, total_thinking_time

    def o1think(self,task, knowledges, group, args):
        self.args = args
        # 获取人类的问题
        question = task.question
        ask_prompt = f"""
question: {question}
knowledge: {knowledges}
Now think step by step. 
"""
        steps = None
        # 主持人思考
        summary = None
        final_answer = None
        for steps, total_thinking_time in self.generate_o1_response(ask_prompt):
            step,think,total_thinking_time = steps[-1]
            self.say(f"{step}\n{think}")
            if step == "Final Answer":
                final_answer = think
                break
            # 是否开启多智能体讨论
            if not args.mas:
                continue
            else:
                vote_results = [agent.vote(question,knowledges) for agent in group.people]
                if sum(vote_results) > len(vote_results)/2:
                    # 几个专家进行讨论，选择如何修改
                    messages = message_pool.get_visibile_messages()[1:]
                    content  = '\n'.join([f"{message.send_from}: {message.content}" for message in messages])
                    summary, history = group.start(n_round=2, task = task, current_step = f"{step}\n{think}", base_message = content,knowledges = knowledges)
                    self.user_message = summary
                    steps[-1] = (steps[-1], history)
                else:
                    steps[-1] = (steps[-1], None)
        return final_answer,steps
        

 