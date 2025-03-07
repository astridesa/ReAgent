from Agent.agent import Agent
from backend.api import api_call
from Interaction.messagepool import message_pool

class Thinker(Agent):
    """
    Thinker is an agent class that evaluates whether the moderator's current reasoning step 
    needs modification. It accesses a shared message pool (message_pool) to retrieve the 
    conversation history visible to itself, then decides by voting 'yes' or 'no' 
    based on the content of the moderator's latest statement.
    """
    _name = "Thinker"

    def __init__(self, name: str = None, model: str = "deepseek-chat", args=None):
        """
        :param name: The name of the Thinker agent. Defaults to the class-level _name if not provided.
        :param model: The model identifier (e.g., 'deepseek-chat').
        :param args: Additional configuration parameters, such as temperature or other options.
        """
        super().__init__(name=name if name is not None else self._name, model=model)
        self.args = args

    def vote(self, question, knowledges):
        """
        This method inspects the conversation history to judge whether the moderator's 
        latest reasoning step needs modification. If it does, it returns 1 (meaning 'yes'), 
        otherwise returns 0 (meaning 'no').

        The logic is:
        1. Retrieve all visible messages for this agent via the message pool.
        2. Collect the moderator's previous content (excluding messages from 'Human').
        3. Check the moderator's current content.
        4. Generate a prompt for the language model, requesting a simple "yes" or "no" output.
        5. If the response contains "yes", the method also calls self.say(...) to indicate 
           the need for revision, and returns 1. Otherwise, it returns 0.
        """
        messages = message_pool.get_visibile_messages(visibile=self.name)
        preious_content = ""

        # Gather all but the last message's content from the moderator or other participants
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

Based on your knowledge, please consider the following:
1. Whether it conflicts with your own information.
2. Whether there are any flaws in the current step.
3. Whether there are any logic errors, hallucinations, or miscalculations.

Please respond with "yes" or "no" directly to indicate if you believe the moderator's reasoning requires changes. 
Do not include any additional symbols or text.
"""

        response = api_call(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
            temperature=1.0
        ).lower()

        if "yes" in response:
            self.say("I think we need to modify the moderator's statement.")
            return 1
        else:
            return 0
