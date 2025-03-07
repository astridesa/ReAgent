import json
import time

from Agent.agent import Agent
from backend.api import api_call
from Interaction.messagepool import message_pool


class Moderator(Agent):
    """
    The Moderator class orchestrates a multi-step reasoning process
    and can optionally incorporate multi-agent review. It generates
    an initial response by incrementally calling an LLM, captures
    steps in a structured format, and then yields them for possible
    additional external scrutiny or summarization. 
    """
    _name = "moderator"

    def __init__(self, name: str = None, model: str = "deepseek-chat"):
        """
        :param name: Name of the Moderator agent, defaulting to _name if None.
        :param model: Model identifier for the LLM used to process reasoning steps.
        """
        super().__init__(name=name if name is not None else self._name, model=model)
        self.user_message = None

    def generate_o1_response(self, question):
        """
        A generator function that interacts with the LLM in a stepwise fashion:
        1. Sends an initial prompt describing multi-step reasoning instructions.
        2. Repeatedly retrieves partial steps from the LLM (in JSON format).
        3. If 'final_answer' or step_count > 25 is reached, it breaks out of the loop.
        4. Finally requests a plain-text final answer without JSON formatting.
        This function yields tuples of (steps, total_thinking_time) or (steps, None)
        after each step, so that external systems (e.g., UI) can handle or display them.

        :param question: The user question or problem to be reasoned about.
        :yield: A tuple of (steps, total_thinking_time) or (steps, None).
        """
        ref = None
        if ref is None:
            ref = ""

        messages = [
            {
                "role": "system",
                "content": """
You are an expert in multi-step reasoning tasks. According to the user's question, 
you need to produce a plan that outlines each step of the reasoning process, 
including what information is needed at each step and what the expected outcome might be. 
Your output MUST strictly adhere to the JSON format with the following keys:
{
    "step": "...",
    "reasoning": "...",
    "next_action": "..."
}
If you have determined the final answer, set "next_action" to "final_answer".
"""
            },
            {"role": "user", "content": question},
            {
                "role": "assistant",
                "content": "Thank you! I will think step by step as instructed."
            }
        ]

        steps = []
        step_count = 1
        total_thinking_time = 0

        while True:
            # If user_message has been updated externally, attach it
            if self.user_message is not None:
                messages.append(
                    {
                        "role": "user",
                        "content": json.dumps(self.user_message, ensure_ascii=False)
                    }
                )
                print(messages)

            start_time = time.time()

            # Attempt to call the model to get JSON-structured output
            while True:
                try:
                    step_data = api_call(
                        messages,
                        model=self.model,
                        temperature=self.args.temperature,
                        max_tokens=2048,
                        json_format=True
                    )
                    assert "step" in (step_data.keys()), "invalid output"
                    break
                except:
                    continue

            end_time = time.time()
            thinking_time = end_time - start_time
            total_thinking_time += thinking_time

            steps.append(
                (
                    f"Step {step_count}: {step_data['step']}",
                    step_data['reasoning'],
                    thinking_time
                )
            )

            ref = step_data["next_action"]
            messages.append(
                {
                    "role": "assistant",
                    "content": json.dumps(step_data, indent=4, ensure_ascii=False)
                }
            )
            if ref is not None:
                messages.append(
                    {
                        "role": "user",
                        "content": f"Okay, your next step is to reason in the direction of '{ref}'. "
                                   "Please return JSON as instructed. Do not return an empty string."
                    }
                )
                print(
                    f"Okay, your next step is to reason in the direction of '{ref}'. "
                    "Please return JSON as instructed. Do not return an empty string."
                )

            # Break if final answer or if step_count is beyond limit
            if step_data["next_action"] == "final_answer" or step_count > 25:
                break

            step_count += 1

            # Yield after each intermediate step
            yield steps, None

        # Request a final plain-text answer
        messages.append(
            {
                "role": "user",
                "content": (
                    "Please provide a final answer based on the above reasoning only. "
                    "Do not use JSON formatting. Output a plain text answer without extra headings, "
                    "preambles, or repeated punctuation. Retain any necessary text formatting from "
                    "the original instructions."
                )
            }
        )

        start_time = time.time()
        final_data = api_call(
            messages,
            self.model,
            self.args.temperature,
            300,
            json_format=False
        )
        end_time = time.time()
        thinking_time = end_time - start_time
        total_thinking_time += thinking_time

        steps.append(("Final Answer", final_data, thinking_time))
        yield steps, total_thinking_time

    def o1think(self, task, knowledges, group, args):
        """
        Primary method for orchestrating the multi-step reasoning. 
        1. Generates an extended prompt from the question and knowledge. 
        2. Calls 'generate_o1_response' to iteratively gather reasoning steps. 
        3. At each step, if multi-agent collaboration is enabled, 
           other agents can vote on whether revision is needed. 
           If the vote indicates revision is needed, the environment triggers a short discussion round. 
        4. Returns the final answer and the entire list of steps.

        :param task: An object with a 'question' attribute.
        :param knowledges: A string or structured data relevant to the question.
        :param group: An environment or group of additional agents to handle multi-agent interactions.
        :param args: A configuration object including attributes such as 'temperature', 'mas' etc.
        :return: A tuple (final_answer, steps).
        """
        self.args = args
        question = task.question
        ask_prompt = f"""
question: {question}
knowledge: {knowledges}
Now think step by step.
"""
        steps = None
        final_answer = None

        # Start generating the multi-step reasoning
        for steps, total_thinking_time in self.generate_o1_response(ask_prompt):
            step, thinking, _ = steps[-1]
            self.say(f"{step}\n{thinking}")

            # Check if final answer was reached
            if step == "Final Answer":
                final_answer = thinking
                break

            # If multi-agent system is not enabled, skip to next iteration
            if not args.mas:
                continue
            else:
                # Agents from the group vote
                vote_results = [agent.vote(question, knowledges) for agent in group.people]
                # If majority indicates a need for revision
                if sum(vote_results) > len(vote_results) / 2:
                    # Retrieve recent messages from the pool (excluding the user prompt)
                    messages = message_pool.get_visibile_messages()[1:]
                    content = "\n".join([f"{m.send_from}: {m.content}" for m in messages])
                    # Start a short discussion round
                    summary, history = group.start(
                        n_round=2,
                        task=task,
                        current_step=f"{step}\n{thinking}",
                        base_message=content,
                        knowledges=knowledges
                    )
                    self.user_message = summary
                    steps[-1] = (steps[-1], history)
                else:
                    steps[-1] = (steps[-1], None)

        return final_answer, steps
