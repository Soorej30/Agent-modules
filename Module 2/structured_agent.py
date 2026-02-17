from groq import Groq
import re

with open('/Users/soorejsnair/Documents/code/Personal Projects/Secret/groq_key.txt', 'r') as key_file:
    GROQ_API_KEY = key_file.read()
client = Groq(api_key=GROQ_API_KEY)

def call_llm(messages):
    response = client.chat.completions.create(
        model = "llama-3.3-70b-versatile",
        messages = messages,
        temperature=0
    )
    return response.choices[0].message.content

# PROPER TOOL DESIGN - Instead of random functions, define tools properly

class Tool:
    def __init__(self, name, description, input_schema, func):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.func = func

    def execute(self, args):
        return self.func(**args)

# Now we define calculator safely

import ast
import operator
def safe_calculator(expression: str):
    allowed_ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
    }

    def eval_node(node):
        if isinstance(node, ast.BinOp):
            return allowed_ops[type(node.op)](
                eval_node(node.left),
                eval_node(node.right)
            )
        elif isinstance(node, ast.Constant):
            return node.value
        else:
            raise ValueError("Unsupported expression")
    
    parsed = ast.parse(expression, mode = "eval")
    return str(eval_node(parsed.body))

# Registering the tool
calculator_tool = Tool(
    name = "calculator",
    description = "Performs mathematical calculations",
    input_schema = {
        "type": "object",
        "properties": {
            "expression": {"type": "string"}
        },
        "required": ["expression"]
    },
    func = safe_calculator
)

# Strict output prompt
SYSTEM_PROMPT = """
    You are an agent.

    You have access to the following tool:

    Tool name: calculator
    Description: Performs mathematical calculations.
    Arguments:
    {
        "expression": "string"
    }

    If using a tool, respond ONLY in this format:

    {
        "thought": "...",
        "action": {
            "name": "calculator",
            "arguments": {
                "expression": "23 * 47"
            }
        }
    }

    If done, respond:

    {
        "final_answer": "..."
    }

    Respond ONLY in valid JSON.
"""


# Safe parsing

import json

def parse_response (response):
    response = response.strip()

    if response.startswith("```"):
        response = response.split("```")[1]
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON"}

# Maintain registry    
TOOLS = {
    calculator_tool.name: calculator_tool
}

# Build the real execution engine
def run_agent(user_input):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ]

    for _ in range(10): # Setting an iteration cap
        response = call_llm(messages)
        print("LLM:", response)

        data = parse_response(response)

        if "final_answer" in data:
            return data["final_answer"]
        
        if "action" in data:
            tool_name = data["action"]["name"]
            args = data["action"]["arguments"]

            if tool_name not in TOOLS:
                return "Error: Unknown tool"
            
            result = TOOLS[tool_name].execute(args)
            
            print("------------------")
            print(messages)
            messages.append({"role": "assistant", "content": response})
            messages.append({
                "role": "user",
                "content": f"Observation: {result}"
            })
        
        if "error" in data:
            return "Model returned invalid JSON."
    return "Max iterations reached"


if __name__ == "__main__":
    question = input("Ask a question: ")
    answer = run_agent(question)
    print("Final Answer: ", answer)