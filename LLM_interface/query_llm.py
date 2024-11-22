import requests
import json

# Function to process streamed responses from the API
def process_streamed_responses(response):
    """
    Processes the API streamed response to display generated text incrementally.
    """
    generated_text = ""
    for chunk in response.iter_lines():
        if chunk:
            try:
                json_data = json.loads(chunk.decode("utf-8"))
                if "response" in json_data:
                    generated_text += json_data["response"]
                    print(json_data["response"], end="", flush=True)
            except json.JSONDecodeError:
                pass
    return generated_text

# Function to query the Llama API
def query_ollama_stream(api_url, model_name, prompt, stream=False):
    """
    Queries the API with a prompt and handles streamed responses for incremental updates.
    """
    headers = {"Content-Type": "application/json"}
    payload = {"model": model_name, "prompt": prompt, "stream": stream}

    try:
        with requests.post(api_url, headers=headers, json=payload, stream=stream) as response:
            response.raise_for_status()
            if stream:
                return process_streamed_responses(response)
            else:
                return response.json().get("response", "No response generated.")
    except requests.exceptions.RequestException as e:
        return f"Request failed: {e}"