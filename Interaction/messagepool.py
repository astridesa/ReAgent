from Interaction.message import Message

class MessagePool:
    def __init__(self):
        self.messages = []
   

    def get_visibile_messages(self, visibile = "all"):
        """
        visibile：查询的对象，可以是 all，也可以是某个 agent 的名字
        查询 visibile 可以看到的消息
        """
        if visibile == "all":
            return self.messages
        else:
            return [message for message in self.messages if visibile in message.send_to or message.send_to == "all"]

    def get_ones_messages(self, name = "all"):
        """
        visibile：查询的对象，可以是 all，也可以是某个 agent 的名字
        查询 visibile 可以看到的消息
        """
        if name == "all":
            return self.messages
        else:
            return [message for message in self.messages if name == message.send_from or message.send_from == "all"]


    def update_message(self, message:Message):
        self.messages.append(message)

    def show_messages(self):
        for message in self.messages:
            print(f"{message.send_from}: {message.content}")
    
    def output_history(self):
        history = ""
        for message in self.messages:
            history += (f"{message.send_from}: {message.content}\n")
        return history 


# 构建一个超级全局变量实例
message_pool = MessagePool()

def get_pool():
    global message_pool
    return message_pool

def update_pool(pool):
    global message_pool
    message_pool = pool

