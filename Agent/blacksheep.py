# =========================================================================================
# Multi-Agent Framework Code
# =========================================================================================
# All comments and docstrings are in English. This code provides an illustrative multi-agent
# framework structure, featuring:
#   - A base agent class with local state and checkpoint/backtracking support
#   - Specific agent classes for question decomposition, retrieval, verification, and
#     answer assembly
#   - A supervisor and controller to handle high-level conflict resolution
#   - A message bus for communication among agents
#   - The BlackSheep agent code remains functionally unchanged, except its prompt and any
#     language strings are converted to English
# =========================================================================================

# ------------------- Base Agent Definition -------------------

class BaseAgent:
    """
    BaseAgent is a generic class representing a single agent in the system.
    It stores local state, handles checkpointing for local backtracking,
    and offers a way to receive and send messages through a message bus.
    """

    def __init__(self, name: str, message_bus=None):
        """
        :param name: Name of the agent
        :param message_bus: A reference to a shared message bus or manager
        """
        self.name = name
        self.message_bus = message_bus
        self.local_state = {
            "verified_facts": [],
            "history": [],
            "backtrack_stack": []
        }

    def checkpoint_state(self):
        """
        Records the agent's current local_state so that it can be restored
        if local backtracking is needed.
        """
        import copy
        snapshot = copy.deepcopy(self.local_state)
        self.local_state["backtrack_stack"].append(snapshot)

    def local_backtrack(self):
        """
        Restores the most recent stored snapshot from the agent's
        local backtrack stack.
        """
        if self.local_state["backtrack_stack"]:
            last_snapshot = self.local_state["backtrack_stack"].pop()
            self.local_state = last_snapshot

    def receive_message(self, msg):
        """
        Agents receive messages through this method. Each subclass
        can override the logic to handle different message types.
        """
        pass

    def send_message(self, msg_type, receiver, content):
        """
        Sends a message to a designated receiver via the message bus.
        """
        if self.message_bus is not None:
            self.message_bus.send_message(
                sender=self.name,
                receiver=receiver,
                msg_type=msg_type,
                content=content
            )

    def run_one_step(self):
        """
        Allows the agent to perform its reasoning or update logic
        in discrete steps if desired. Subclasses can override as needed.
        """
        pass


# ------------------- Example Agents (Execution Layer) -------------------

class QuestionDecomposerAgent(BaseAgent):
    """
    This agent receives a main question and decomposes it into smaller
    sub-questions or tasks, sending them to other agents for processing.
    """

    def __init__(self, name="QuestionDecomposerAgent", message_bus=None):
        super().__init__(name, message_bus)

    def receive_message(self, msg):
        """
        If the message indicates a main question, it performs decomposition
        and sends sub-questions to a retriever or other agents.
        """
        if msg.get("msg_type") == "INFORM" and isinstance(msg.get("content"), str):
            main_question = msg["content"]
            sub_questions = self.decompose_question(main_question)
            for sq in sub_questions:
                self.send_message(
                    msg_type="ASSERT",
                    receiver="RetrieverAgent",
                    content={"sub_question": sq}
                )

    def decompose_question(self, question: str):
        """
        Splits the main question into sub-questions. Here is a placeholder
        example; real logic may use advanced parsing or a language model.
        """
        return [
            f"Identify key entities in: {question}",
            f"Find relevant references for: {question}",
            f"Check for any potential contradictions: {question}"
        ]


class RetrieverAgent(BaseAgent):
    """
    The RetrieverAgent fetches relevant evidence or knowledge
    based on sub-questions, then sends them to a verifier agent.
    """

    def __init__(self, name="RetrieverAgent", message_bus=None, knowledge_source=None):
        super().__init__(name, message_bus)
        self.knowledge_source = knowledge_source

    def receive_message(self, msg):
        if msg.get("msg_type") == "ASSERT":
            content = msg.get("content", {})
            if "sub_question" in content:
                sub_q = content["sub_question"]
                evidence = self.retrieve_evidence(sub_q)
                self.send_message(
                    msg_type="INFORM",
                    receiver="VerifierAgent",
                    content={"evidence_list": evidence, "sub_question": sub_q}
                )

    def retrieve_evidence(self, sub_question: str):
        """
        A placeholder method that returns fake evidence. In practice,
        it might perform database or API queries to get real information.
        """
        return [f"Fake evidence for: {sub_question}"]


class VerifierAgent(BaseAgent):
    """
    The VerifierAgent checks incoming evidence for internal consistency
    or conflicts with already verified knowledge. If a conflict is found,
    it may local backtrack and escalate further if needed.
    """

    def __init__(self, name="VerifierAgent", message_bus=None):
        super().__init__(name, message_bus)

    def receive_message(self, msg):
        if msg.get("msg_type") == "INFORM":
            content = msg.get("content", {})
            evidence_list = content.get("evidence_list", [])
            self.checkpoint_state()
            conflict = self.verify(evidence_list)
            if conflict:
                self.local_backtrack()
                self.send_message(
                    msg_type="CONFLICT",
                    receiver="SupervisorAgent",
                    content={"conflict_detail": conflict}
                )
            else:
                for ev in evidence_list:
                    self.local_state["verified_facts"].append(ev)
                self.send_message(
                    msg_type="ASSERT",
                    receiver="AnswerAssemblerAgent",
                    content={"verified_facts": evidence_list}
                )

    def verify(self, evidence_list):
        """
        Checks for any obvious contradiction in the incoming evidence.
        Returns a conflict detail string if found, else None.
        """
        if len(set(evidence_list)) < len(evidence_list):
            return "Detected repeated or conflicting evidence."
        return None


class AnswerAssemblerAgent(BaseAgent):
    """
    The AnswerAssemblerAgent collects verified facts from the VerifierAgent,
    composes a consolidated final answer, and may forward it to the Supervisor.
    """

    def __init__(self, name="AnswerAssemblerAgent", message_bus=None):
        super().__init__(name, message_bus)
        self.partial_answers = []

    def receive_message(self, msg):
        if msg.get("msg_type") == "ASSERT":
            content = msg.get("content", {})
            new_facts = content.get("verified_facts", [])
            self.partial_answers.extend(new_facts)
            if self.is_ready_for_final():
                final_answer = self.assemble_answer()
                self.send_message(
                    msg_type="INFORM",
                    receiver="SupervisorAgent",
                    content={"final_answer": final_answer}
                )

    def is_ready_for_final(self):
        """
        Basic check for readiness to form a final answer.
        """
        return len(self.partial_answers) > 2

    def assemble_answer(self):
        """
        Joins partial answers into a final integrated answer string.
        """
        return "Integrated Answer: " + "; ".join(self.partial_answers)


# ------------------- Supervisory Layer -------------------

class SupervisorAgent(BaseAgent):
    """
    The SupervisorAgent orchestrates the resolution of conflicts that
    cannot be handled locally, possibly triggering a global backtrack.
    """

    def __init__(self, name="SupervisorAgent", message_bus=None):
        super().__init__(name, message_bus)

    def receive_message(self, msg):
        msg_type = msg.get("msg_type")
        content = msg.get("content", {})
        if msg_type == "CONFLICT":
            self.send_message(
                msg_type="BACKTRACK",
                receiver="ALL",
                content={"reason": content.get("conflict_detail", "")}
            )
        elif msg_type == "INFORM" and "final_answer" in content:
            final_ans = content["final_answer"]
            print(f"[Supervisor] Final Answer: {final_ans}")


class ControllerAgent(BaseAgent):
    """
    The ControllerAgent can oversee high-level strategy, intervening
    if repeated conflicts occur and issuing challenges or overrides.
    """

    def __init__(self, name="ControllerAgent", message_bus=None):
        super().__init__(name, message_bus)
        self.intervention_count = 0

    def receive_message(self, msg):
        if msg.get("msg_type") == "CONFLICT":
            self.intervention_count += 1
            if self.intervention_count > 2:
                self.send_message(
                    msg_type="CHALLENGE",
                    receiver="VerifierAgent",
                    content={"directive": "Re-check all facts with more stringent criteria"}
                )
        elif msg.get("msg_type") == "BACKTRACK":
            pass


# ------------------- Interaction Layer (Message Bus) -------------------

class MessageBus:
    """
    A simplified message bus that routes messages between agents.
    """

    def __init__(self):
        self.agents_map = {}

    def register_agent(self, agent_instance):
        """
        Registers an agent with a unique name for message routing.
        """
        self.agents_map[agent_instance.name] = agent_instance

    def send_message(self, sender, receiver, msg_type, content):
        """
        Sends a message to the specified receiver. If receiver='ALL',
        it broadcasts to all agents except the sender.
        """
        msg = {
            "sender": sender,
            "receiver": receiver,
            "msg_type": msg_type,
            "content": content
        }
        if receiver == "ALL":
            for ag_name, ag_inst in self.agents_map.items():
                if ag_name != sender:
                    ag_inst.receive_message(msg)
        else:
            if receiver in self.agents_map:
                self.agents_map[receiver].receive_message(msg)

    def run_agents(self, steps=3):
        """
        Optional method to run each agent's run_one_step() a fixed number of times.
        """
        for _ in range(steps):
            for ag_name, ag_inst in self.agents_map.items():
                ag_inst.run_one_step()


# ------------------- BlackSheep Agent (Provided Code) -------------------
# The functionality and method names remain unchanged.
# Prompt and any textual content is in English now.

from Agent.agent import Agent
from backend.api import api_call
from Interaction.messagepool import message_pool

class BlackSheep(Agent):
    _name = "blacksheep"

    def __init__(self, name:str = None, model:str = "deepseek-chat", args = None):
        super().__init__(name = name if name is not None else _name, model = model)
        self.args = args

    def vote(self, question, knowledges):
        """
        If the moderator's statement does not need modifications, it votes 'no';
        otherwise it votes 'yes'. However, as a 'BlackSheep', it always does the opposite.
        """
        messages = message_pool.get_visibile_messages(visibile=self.name)
        preious_content = ""
        for message in messages[:-1]:
            preious_content += f"{message.send_from}: {message.content}\n"
        knowledges = ""

        current_content = f"{messages[-1].send_from}: {messages[-1].content}\n"

        prompt = f"""
You are {self.name}, taking part in a heated discussion about answering a question.
However, you are a 'BlackSheep' whose role is to subtly mislead the discussion by providing
incorrect but not overly obvious opinions so that others may end up with wrong reasoning.
You must disguise yourself as a normal thinker and should not reveal your true role.

### Discussion Topic
{question}

### Existing Knowledge
{knowledges}

### Previous Moderator's Thoughts
{preious_content}

### Moderator's Current Thought
{current_content}

Please analyze the moderator's current reasoning from a rigorous scientific perspective
to see if there are logical flaws or contradictions with your own knowledge. You must make
a decision opposite to the actual truth. In the final line, output 'yes' or 'no' only,
indicating if you think the moderator's statement needs to be changed. Do not output any
symbols or text besides 'yes' or 'no'. (For example, if the moderator truly needs a change,
because you are the 'BlackSheep', you output 'no'; if the moderator is correct, you output 'yes'.)
        """

        response = api_call(messages=[{"role":"user", "content":prompt}], model=self.model, temperature=self.args.temperature)
        
        if "yes" in response or "Yes" in response:
            self.say("I think we need to modify the moderator's statement.")
            return 1
        else:
            return 0
        print(response)


# ------------------- Example Main Function -------------------

def main():
    """
    Demonstrates a simple multi-agent setup and sends an initial question
    to the question decomposer. Also shows how the BlackSheep agent might be used.
    """
    bus = MessageBus()

    # Create and register standard agents
    decomposer = QuestionDecomposerAgent(name="QuestionDecomposerAgent", message_bus=bus)
    retriever = RetrieverAgent(name="RetrieverAgent", message_bus=bus, knowledge_source=None)
    verifier = VerifierAgent(name="VerifierAgent", message_bus=bus)
    assembler = AnswerAssemblerAgent(name="AnswerAssemblerAgent", message_bus=bus)
    supervisor = SupervisorAgent(name="SupervisorAgent", message_bus=bus)
    controller = ControllerAgent(name="ControllerAgent", message_bus=bus)

    for ag in [decomposer, retriever, verifier, assembler, supervisor, controller]:
        bus.register_agent(ag)

    # The BlackSheep agent is created separately. It uses different internal logic/messagepool.
    black_sheep_agent = BlackSheep(name="BlackSheepAgent", model="deepseek-chat", args=None)
    # If we wanted to integrate it fully, we'd adapt the bus or messagepool accordingly.

    # Send an initial question to the Decomposer
    initial_msg = {
        "sender": "User",
        "receiver": "QuestionDecomposerAgent",
        "msg_type": "INFORM",
        "content": "Which US state hosted the 1984 Summer Olympics and has a smaller capital city than its largest city?"
    }
    bus.send_message(
        sender=initial_msg["sender"],
        receiver=initial_msg["receiver"],
        msg_type=initial_msg["msg_type"],
        content=initial_msg["content"]
    )

    # Run a few steps to let agents process the question
    bus.run_agents(steps=5)

    # Example usage of BlackSheep's vote method (optional):
    # question_sample = "Which US state..."
    # knowledge_sample = "Some domain knowledge"
    # black_sheep_decision = black_sheep_agent.vote(question_sample, knowledge_sample)
    # print(f"[BlackSheep Decision]: {black_sheep_decision}")


if __name__ == "__main__":
    main()
