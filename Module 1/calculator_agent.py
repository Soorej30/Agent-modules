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

def calculator(expression: str):
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e}"

def parse_action(response):
    if "Action:" in response:
        match = re.search(r"calculator\((.*?)\)", response)
        if match:
            return "calculator", match.group(1)
    return None, None

SYSTEM_PROMPT = """
    You are a reasoning agent.
    You must respond in ONE of the following formats:

    If calculation is needed"
    Thought: explain reasoning
    Action: calculator(expression)

    If no calculation is needed:
    Final Answer: answer here

    Only respond in this format.
"""


def run_agent(user_input):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": user_input}
    ]

    while True:
        response = call_llm(messages)
        print("LLM:", response)

        if "Final Answer:" in response:
            return response.split("Final Answer:")[1].strip()
        
        tool_name, tool_input = parse_action(response)

        if tool_name == "calculator":
            result = calculator(tool_input)

            messages.append({"role": "assistant", "content": response})
            messages.append({
                "role": "user",
                "content": f"Observation: {result}"
            })
        else:
            return "Agent failed to parse action."
        

if __name__ == "__main__":
    question = input("Ask a question: ")
    answer = run_agent(question)
    print("Final Answer: ", answer)