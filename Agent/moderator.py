import json
import time

from Agent.agent import Agent
from backend.api import api_call, api_call_completion
from Interaction.messagepool import message_pool

class Moderator(Agent):
    """
    The Moderator class coordinates the step-by-step reasoning process and optionally
    engages other agents (e.g., a multi-agent group) to vote on or revise the reasoning.
    It uses a prompt format that instructs the model to return reasoning steps prefixed
    by "Step x:" and eventually a "Final Answer" step.
    """
    _name = "moderator"

    def __init__(self, name: str = None, model: str = "deepseek-v3"):
        """
        :param name: Name of the Moderator agent. Defaults to 'moderator' if None.
        :param model: The model identifier used for stepwise completions (e.g., 'deepseek-v3').
        """
        super().__init__(name=name if name is not None else self._name, model=model)
        self.modifly = None
        self.current_text = None
        self.current_step = 1
        self.iteration = 0
        self.steps = []
        self.final_answer = None

    def generate_step_response(self, prompt):
        """
        A generator that repeatedly queries the model using 'api_call_completion',
        stopping at each 'Step x:' marker or the next step. 
        At each iteration, it yields the raw step content.
        """
        messages = [
            {"role": "user", "content": prompt}
        ]

        while True:
            if self.current_step != 1:
                messages.append({"role": "assistant", "content": self.current_text})

            start_time = time.time()
            # We use 'stop_list' to break the response at the next 'Step x:' section
            step_resp = api_call_completion(
                messages,
                model=self.model,
                stop_list=[f"Step {self.current_step+1}:"]
            )
            end_time = time.time()

            thinking_time = end_time - start_time
            self.current_text = step_resp
            self.steps.append((step_resp, None))
            self.messages = messages

            yield step_resp

    def cot(self, task, question, knowledges, group, args):
        """
        The core chain-of-thought (CoT) method. It sets up a prompt that asks for each
        step to begin with 'Step x:' and end with '[End]', up to the 'Final Answer',
        then iterates through responses. If multi-agent collaboration is enabled,
        other agents can vote after each step to decide whether a revision is needed.
        """
        self.args = args
        # Construct the multi-step reasoning prompt
        self.cot_prompt = (
            f"""{question}

Please reason step by step, and each step should begin with "Step x:" and end with "[End]". 
Each step should be detailed, limited to 256 tokens, and if the question is complex (e.g., zebra logic),
you can use markdown tables to better structure the reasoning. 
Finally, provide the final answer in a single step starting with "Final Answer" and ending with "[End]".

Example:
Step 1: Explanation here [End]
Step 2: Next reasoning here [End]
Step 3: Another step [End]
...
Final Answer: The final answer text [End]
"""
        )

        summary = None
        final_flag = False

        # Call the step response generator
        for step in self.generate_step_response(self.cot_prompt):
            if step == self.steps[-1][0]:
                self.iteration += 1

            if self.iteration >= 5:
                return step, self.steps

            self.current_text = step
            print()
            self.say(step)

            # If multi-agent system is enabled, request votes from other agents
            if args.mas:
                vote_results = [agent.vote(question, knowledges) for agent in group.people]
                # If majority vote indicates a need for revision
                if sum(vote_results) > len(vote_results) / 2:
                    messages = message_pool.get_visibile_messages()[1:]
                    content = '\n'.join([f"{message.send_from}: {message.content}" for message in messages])
                    mod_step, history = group.start(
                        n_round=2,
                        task=task,
                        current_step=self.current_text,
                        preious_content=content,
                        knowledges=knowledges
                    )
                    self.current_text = mod_step
                    self.steps[-1] = (self.current_text, history)

            # Check if the step indicates a final answer
            if "Final Answer" in self.current_text and "[End]" in self.current_text:
                final_flag = True
                # If the task includes multiple choices, ask for a direct selection
                if hasattr(task, "choices"):
                    self.messages.append({
                        "role": "user",
                        "content": (
                            task.question +
                            f" Based on the reasoning steps above, provide the answer chosen from {task.choices} directly."
                        )
                    })
                else:
                    self.messages.append({
                        "role": "user",
                        "content": task.question + " Based on the reasoning steps above, please provide the direct answer."
                    })

                while self.final_answer is None:
                    self.final_answer = api_call(self.messages, model=args.model)
                self.steps.append((self.final_answer, None))

            if final_flag:
                if self.final_answer is None:
                    pass
                return self.final_answer, self.steps

            self.current_step += 1
