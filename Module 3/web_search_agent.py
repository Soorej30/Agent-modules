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

class HybridAgent:
    def __init__(self):
        self.memory = []    # Long term context storage
        self.plan = ""      # The roadmap

    def search_tool(self, query):
        print(f"[Tool] Searching: {query}")
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results = 3)]

        return "\n".join(results)
    

    def run(self, goal):
        # 1. PLANNING PHASE
        planning_prompt = [
            {"role": "system", "content": "You are a lead strategist. Break the user goal into 3 specific research milestones."},
            {"role": "user", "content": goal}
        ]
        self.plan = call_llm(planning_prompt)
        print(f" PLAN: \n{self.plan}")

        # REACT + MEMORY LOOP
        for i in range(3):
            context = "\n".join(self.memory)
            react_prompt = [
                {"role": "system", "content": f"Goal: {goal}\nPlan: {self.plan}\nContext: {context}\n"
                 "Decide if you need to [SEARCH: query] or [FINALIZE: summary]. Use ReAct logic: Thought, Action, Observation."},
                 {"role": "user", "content": "What is your next step?"}
            ]
            thought_process = call_llm(react_prompt)
            print(f"THOUGHT {i+1}: {thought_process}")

            if "[SEARCH:" in thought_process:
                query = thought_process.split("[SEARCH:")[1].split("]")[0]
                observation = self.search_tool(query)
                self.memory.append(f"Observation from '{query}': {observation}")
            elif "[FINALIZE:" in thought_process:
                break
        
        # 3. FINAL SYNTHESIS
        final_prompt = [
            {"role": "system", "content": "Synthesize the memory into a professional report."},
            {"role": "user", "content": f"Memory: {' '.join(self.memory)}"}
        ]
        return call_llm(final_prompt)
    
agent = HybridAgent()
report = agent.run("Research recent developments in diffusion models and summarizes the report")
print("\n--- HYBRID AGENT FINAL REPORT ---\n", report)
with open(f'research_output_{datetime.now()}.md', 'w+') as r:
    r.write(report)