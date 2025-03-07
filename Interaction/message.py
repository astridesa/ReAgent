class Message:
    def __init__(self, content:str, send_from:str = None, send_to:str = None):
        self.send_from:str = send_from
        self.send_to:str = send_to
        self.content:str = content