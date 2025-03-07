from Interaction.messagepool import MessagePool
class Environment:
    def __init__(self, people:list, args):
        # 几个人
        self.people = people
        self.args = args
        self.n = len(self.people)
        self.message_pool = MessagePool()
    def start():
        pass