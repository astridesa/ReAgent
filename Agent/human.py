from Agent.agent import Agent

class Human(Agent):
    """
    The Human class is a simple subclass of the Agent class,
    representing a human participant in the multi-agent environment.
    It inherits all methods and attributes from Agent, and does not override them
    except to provide a default name.
    """
    name = "human"

    def __init__(self, name: str = None):
        """
        :param name: Name for this Human agent. Defaults to the class-level name if not provided.
        """
        super().__init__(name=name if name else self.name)
