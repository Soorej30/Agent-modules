from datetime import datetime
import json
from ddgs import DDGS
from groq import Groq
import re

with open('/Users/soorejsnair/Documents/code/Personal Projects/Secret/groq_key.txt', 'r') as key_file:
    GROQ_API_KEY = key_file.read()

def call_llm(messages):
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model = "llama-3.3-70b-versatile",
        messages = messages,
        temperature=0
    )
    return response.choices[0].message.content

# Solver Agent
def solve_task(task):
    prompt = f"""
        You are a reasoning agent.
        Solve the following task carefully.
        task : {task}

        Respond with :
        Final answer: < Your answer >
    """
    solver_prompt = [
            {"role": "system", "content": "You are a reasoning age. Carefully evaluate and solve the problem"},
            {"role": "user", "content": prompt}
        ]
    return call_llm(solver_prompt)

# Critic Agent
def critique_answer(task, answer):
    prompt = f"""
        You are a strict critic for the task.
        Task: {task}

        Proposed Answer:
        {answer}

        Evaluate:
        1. Is the reasoning correct?
        2. Is the final answer correct?
        3. How confident are you that the model is correct?
        4. If wrong, explain why clearly.

        Respond in JSON:
        {{
            "is_correct": "Yes/No",
            "confidence": "0 to 1"
            "feedback": "...."
        }}
    """
    critique_prompt = [
            {"role": "system", "content": "You are a strict critic who checks if the response by a model is correct or not. Be precise and accurate."},
            {"role": "user", "content": prompt}
        ]
    # print("_________________________________")
    # print(type(critique_prompt))
    # print(critique_prompt)
    # print("_________________________________")
    return call_llm(critique_prompt)

def improve_answer(task, previous_answer, feedback):
    prompt = f"""
        You previously attempted this task :
        Task: {task}

        Your previous answer was: {previous_answer}

        The critic feedback for your response was : {feedback}

        Revise your answer correcting all your mistakes:
        Respond with:
        Final answer: <corrected answer>
    """
    improver_prompt = [
            {"role": "system", "content": "You are supposed to improve the answer based on the feedback from the critic."},
            {"role": "user", "content": [prompt]}
        ]

    return call_llm(improver_prompt)

def reflection_loop(task, max_iter = 3):
    print(f"\n=== TASK ===\n{task}\n")

    mistake_memory = []
    answer = solve_task(task)
    print(f"Initial Answer:\n{answer}\n")
    
    for i in range(max_iter):
        print(f"--- Reflection Iteration {i + 1} ---")
        mistake_memory.append(answer)
        
        critique = critique_answer(task, answer)
        print("Critique:", critique)
        critique_json = json.loads(critique)

        if critique_json['is_correct'] == "Yes" and float(critique_json["confidence"]) >= 0.9:
            print("\nAnswer accepted with high confidence of ", critique_json["confidence"])
            return answer, mistake_memory
        else:
            print("\nImproving answer...\n")
            answer = improve_answer(task, answer, critique_json["feedback"])

    print("Revised Answer:\n", answer)
    return answer, mistake_memory


question = input("Ask a question: ")
response = reflection_loop(question)
print("\n--- Reflection loop - Final Answer ---\n", response)
# with open(f'research_output_{datetime.now()}.md', 'w+') as r:
#     r.write(response)