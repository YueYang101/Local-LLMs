# activate the virtual environment
# source .venv/bin/activate
# deactivate the virtual environment
# deactivate

# Update the requirements.txt file
# pip freeze > requirements.txt

import os
from openai import OpenAI

# Initialize the client with the API key
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),  # This is the default and can be omitted
)


# Create a chat completion request using the desired model
chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Say this is a test",
        }
    ],
    model="gpt-4o-mini",  # Replace with the correct model name for your API provider
)

# Extract and print the assistant's reply
response_message = chat_completion.choices[0].message.content  # Access the message content
print(response_message)