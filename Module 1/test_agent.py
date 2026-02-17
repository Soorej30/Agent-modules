import os

from groq import Groq

with open('/Users/soorejsnair/Documents/code/Personal Projects/Secret/groq_key.txt', 'r') as key_file:
    GROQ_API_KEY = key_file.read()

os.environ.GROQ_API_KEY = GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Explain what a SLM in AI is"
        }
    ],
    model = "llama-3.3-70b-versatile"
)

print(chat_completion.choices[0].message.content)