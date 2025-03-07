from backend.api import api_call
from Interaction.message import Message

from Interaction.messagepool import message_pool
class Agent:
    def __init__(self,name:str = None, role:str = None, model:str = None):
        self.name:str = name if name else "agent"
        self.role:str = role if role else "agent"
        self.model:str = model if model else "gpt-4o"

    def think(self,prompt, chat = False, send_to = "all"):
        if chat:
            messages = prompt
        else:
            messages = [
                {"role":"user", "content":prompt}
            ]
        response = api_call(messages=messages,model=self.model)
        self.say(response)

    def say(self, content:str, send_to = "all"):
        print(f"{self.name}: {content}")
 
        message = Message(send_from = self.name, send_to = send_to, content = content)
        message_pool.update_message(message)
        return message