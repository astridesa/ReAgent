from Agent.agent import Agent
from backend.api import api_call
from Interaction.messagepool import message_pool

class Thinker(Agent):
    _name = "Thinker"
    def __init__(self,name:str = None, model:str = "deepseek-chat", args = None):
        super().__init__(name = name if name is not None else _name, model = model)
        self.args = args
    def vote(self,question,knowledges):
 
        """
        如果当前主持人的话不需要修改，则投票否，反之投票是
        """
        messages = message_pool.get_visibile_messages(visibile=self.name)
        preious_content = ""
        for message in messages[:-1]:
            if message.send_from != "Human":
                preious_content += f"{message.send_from}: {message.content}\n"

        current_content = f"{messages[-1].send_from}: {messages[-1].content}\n"


        prompt = f"""You are {self.name}, and you're participating in a complexity seminar with other Thinkers.
Information: {knowledges}

Question: {question}

### The moderator's pre-existing reasoning process
{preious_content}

### The moderator's current reasoning step
{current_content}

Based on your knowledge, please consider the following perspectives including, but not limited to, the following:
1. whether it conflicts with your own information.
2. whether there are any imperfections in your thinking (current step only). 3. whether there are any errors of logic, hallucinations, or miscalculations.
3. whether there are any errors of logic, illusions, miscalculations, etc.
Output "yes" or "no" directly to indicate whether you think the facilitator's thinking needs to be revised, without outputting any other symbols or words.
"""
        response = api_call(messages=[{"role":"user", "content":prompt}],model=self.model,temperature=1.0).lower()
        if "yes" in response or "Yes" in response:
            self.say("I think we need to modify the moderator's statement.")
            return 1
        else:
            # self.say("I think it's correct.")
            return 0
        print(response)
 