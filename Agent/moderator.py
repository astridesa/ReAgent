import json
import time


from Agent.agent import Agent

from backend.api import api_call, api_call_completion

from Interaction.messagepool import message_pool

class Moderator(Agent):
    _name = "moderator"
    def __init__(self,name:str = None, model:str = "deepseek-v3"):
        super().__init__(name = name if name is not None else _name, model = model)
        self.modifly = None
        self.current_text = None
        self.current_step  = 1
        self.iteration = 0
        self.steps = []
 
    def generate_step_response(self,prompt):
        first = 0
        messages = [
            {"role": "user", "content": prompt}
        ]
        while True:

            if self.current_step != 1:
                messages.append({"role": "assistant", "content": self.current_text})
            start_time = time.time()
            step_resp = api_call_completion(messages,model = self.model, stop_list = [f"Step {self.current_step+1}:"])
 
            # print(step_resp)

            # self.current_text+= f"[Step {self.current_step}]{step_resp}"

            end_time = time.time()
            thinking_time = end_time - start_time
            self.current_text = step_resp
            step = step_resp
            self.steps.append((step,None))
            self.messages = messages
            yield step




    def cot(self,task, question, knowledges, group, args):
        self.args = args
        # 获取人类的问题
        
        self.cot_prompt = \
f"""{question}

Please reason step by step, and each step begin with "Step x:", and end with "[End]", where x indicates the current reasoning step. 
Each reasoning step should be detailed and limited to 256 tokens, and when encountering complex conditional information problems like zebralogic problem, you can use markdown tables for better documentation and reasoning.
Finally, provide the final answer in a **single step**, which begin with "Final Answer" and end with "[End]".
Example:
Step 1: xxx [End]
Step 2: xxx [End]
Step 3: xxx [End]
...
Final Answer: xxx [End]
"""         
        steps = None
        # 主持人思考
        summary = None
        self.final_answer = None
        final_flag = False
        for step in self.generate_step_response(self.cot_prompt):
            # self.say(f"[Step {self.current_step}] {step}")
            # 是否开启多智能体讨论
            if step == self.steps[-1][0]:
                self.iteration += 1
            if self.iteration >=5:
                return step, self.steps
            self.current_text = step
            print()

            self.say(step)
            if args.mas:
                # self.say(step)
                vote_results = [agent.vote(question,knowledges) for agent in group.people]
                if sum(vote_results) > len(vote_results)/2:
                    # 几个专家进行讨论，选择如何修改
                    messages = message_pool.get_visibile_messages()[1:]
                    content  = '\n'.join([f"{message.send_from}: {message.content}" for message in messages])
                    mod_step, history = group.start(n_round=2, task = task, current_step = self.current_text, preious_content = content,knowledges = knowledges)
                    self.current_text = mod_step
                    self.steps[-1] = (self.current_text, history)

            if "Final Answer" in self.current_text and "[End]" in self.current_text:
                final_flag = True
                if hasattr(task, "choices"):
                    self.messages.append({"role": "user", "content": task.question + f" Based on the reason steps below, directly give me the answer chosen from {task.choices}."})
                else:
                    self.messages.append({"role": "user", "content": task.question + f" Based on the reason steps below, directly give me the answer."})
                while self.final_answer is None:
                    self.final_answer = api_call(self.messages,model = args.model)
                self.steps.append((self.final_answer,None))
            if final_flag:
                if self.final_answer is None:
                    t = 1
                    
                return self.final_answer, self.steps
            self.current_step += 1

 
 

 