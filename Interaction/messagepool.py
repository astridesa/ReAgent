from Interaction.message import Message

class MessagePool:
    """
    MessagePool is responsible for storing messages and providing
    retrieval methods for visibility or sender-based filtering.
    It serves as a central repository for conversation history.
    """

    def __init__(self):
        self.messages = []

    def get_visibile_messages(self, visibile="all"):
        """
        Returns messages visible to the specified 'visibile' target.
        If 'visibile' is 'all', returns all messages.
        Otherwise, returns only messages whose 'send_to' includes
        the specified target or is set to 'all'.
        """
        if visibile == "all":
            return self.messages
        else:
            return [
                message
                for message in self.messages
                if visibile in message.send_to or message.send_to == "all"
            ]

    def get_ones_messages(self, name="all"):
        """
        Returns messages sent by the specified 'name'.
        If 'name' is 'all', returns all messages.
        Otherwise, filters by the 'send_from' attribute of each message.
        """
        if name == "all":
            return self.messages
        else:
            return [
                message
                for message in self.messages
                if name == message.send_from or message.send_from == "all"
            ]

    def update_message(self, message: Message):
        """
        Appends a new message to the message pool.
        """
        self.messages.append(message)

    def show_messages(self):
        """
        Prints all messages in the pool, displaying
        the sender and the content of each message.
        """
        for message in self.messages:
            print(f"{message.send_from}: {message.content}")

    def output_history(self):
        """
        Returns a string containing the entire conversation history,
        where each line shows the sender and the message content.
        """
        history = ""
        for message in self.messages:
            history += f"{message.send_from}: {message.content}\n"
        return history


# A global instance of MessagePool for shared usage
message_pool = MessagePool()

def get_pool():
    """
    Retrieves the global message_pool instance.
    """
    global message_pool
    return message_pool

def update_pool(pool):
    """
    Updates the global message_pool with a new instance.
    """
    global message_pool
    message_pool = pool
