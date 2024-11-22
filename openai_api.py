# activate the virtual environment
# source .venv/bin/activate

import os
import openai

# Load the API key from the environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Example API call
response = openai.Completion.create(
    model="text-davinci-003",
    prompt="Hello, world!",
    max_tokens=10
)

print(response.choices[0].text.strip())