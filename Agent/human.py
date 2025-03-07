from Agent.agent import Agent
class Human(Agent):
    name = "human"
    def __init__(self,name:str = None):
        super().__init__(name = name if name else self.name)

