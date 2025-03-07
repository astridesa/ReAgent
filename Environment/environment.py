from Interaction.messagepool import MessagePool

class Environment:
    """
    Environment is a base class that manages a collection of agents (participants)
    and a shared message pool. It can be extended to facilitate multi-agent
    interactions, track the number of participants, and organize communication.
    """

    def __init__(self, people: list, args):
        """
        :param people: A list of agent or participant objects involved in the environment.
        :param args: Configuration parameters, which may include model settings,
                     temperature, or other options relevant to multi-agent reasoning.
        """
        self.people = people
        self.args = args
        self.n = len(self.people)
        self.message_pool = MessagePool()

    def start(self):
        """
        A placeholder method where subclasses can implement
        the actual multi-agent or group discussion flow.
        """
        pass
