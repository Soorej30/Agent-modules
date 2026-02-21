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

# Agent to fix the JSON object
def safe_json(raw_string):
    # 1. Clean up whitespace and potential Markdown blocks
    repaired = raw_string.strip()
    if repaired.startswith("```json"):
        repaired = repaired.replace("```json", "", 1).replace("```", "", 1).strip()
    elif repaired.startswith("```"):
        repaired = repaired.replace("```", "", 1).replace("```", "", 1).strip()

    # 2. Check if it's empty BEFORE loading
    if not repaired:
        print("Error: The string passed to safe_json is empty.")
        return {"is_correct": "No", "feedback": "Empty response from LLM"}

    try:
        return json.loads(repaired)
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON. Raw string: {repaired}")
        raise e

# Agent to create the execution plan for the task.
def planner(task):
    prompt = f"""
        Give me the steps required to solve the task.
        task : {task}

        Respond JSON of format :
        {{"steps": ["step 1", "step 2",....,"step n"]}}
        
        Respond ONLY in valid JSON.
    """
    planner_prompt = [
            {"role": "system", "content": "You are a planning agent. Plan the steps required for the following task carefully."},
            {"role": "user", "content": prompt}
        ]
    return safe_json(call_llm(planner_prompt))

# Executor Agent. This executes 1 step from the plan.
def executor(step, context):
    executor_prompt = [
        {"role": "system", "content": "You are an executor. Execute one step carefully and accurately"},
        {"role": "user", "content": f"""
            Execute the one step.
            Previous Context: {context},

            Current Step: {step}
            
            Respond with your result in the format:
            Result: <Your result>
        """}
    ]
    return call_llm(executor_prompt)

# Critic Agent
def critique_agent(step, answer):
    prompt = f"""
        You are a strict critic for this step of the task.
        Task: {step}

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
    return safe_json(call_llm(critique_prompt))

def improve_answer(task, previous_answer, feedback, context):
    prompt = f"""
        You previously attempted this task :
        Task: {task}

        Your previous answer was: {previous_answer}

        The critic feedback for your response was : {feedback}

        And the Previous Context is : {context}

        Revise your answer correcting all your mistakes:
        Respond with:
        Final answer: <corrected answer>
    """
    improver_prompt = [
            {"role": "system", "content": "You are supposed to improve the answer based on the feedback from the critic."},
            {"role": "user", "content": [prompt]}
        ]

    return call_llm(improver_prompt)


def multi_agent_system(task, max_retries = 2, max_global_iterations = 3, confidence_threshold = 0.9):
    print(f"\n=== TASK ===\n{task}\n")

    steps = planner(task)
    print(f"\n=== STEPS ===\n{steps}\n")
    
    context = ""
    global_attempts = 0
    while global_attempts < max_global_iterations:
        print(f"\n=== Global attempt ({global_attempts + 1}) ===\n")

        for step in steps["steps"]:
            success = False
            print("\nExecuting step - ", step)
            result = executor(step, context)
            print("Result of step - ", result)

            evaluation = critique_agent(step, result)
            print("Critic response - ", evaluation)

            if evaluation['is_correct'] == "Yes" and float(evaluation['confidence']) >= confidence_threshold:
                context += f"\n{result}"
                success = True
                print(f"Step {step} successfully completed.")
                continue
            else:
                step_attempt = 1
                while step_attempt < max_retries:
                    result = improve_answer(task = step, previous_answer = result, feedback = evaluation)
                    evaluation = critique_agent(step, answer = result)

                    if evaluation['is_correct'] == "Yes" and evaluation['confidence'] >= confidence_threshold:
                        success = True
                        break
                    else:
                        step_attempt += 1
                        continue
        
            if not success:
                print(f"Step {step} failing repeatedly. Replanning entire workflow")
                steps = planner(task + "\nPrevious attempt failed. Improve plan.")
                global_attempts += 1
                break
        print("All steps completed successfully.")
        return context
    print("\nMax global iterations reached.")
    return context

if __name__ == "__main__":
    question = input("Ask a question: ")
    response = multi_agent_system(task = question)
    print("\n--- Multi agent with reflection loop - Final Answer ---\n", response)

                

                