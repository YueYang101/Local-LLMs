from langchain.agents import initialize_agent, Tool
from langchain.llms import OpenAI
from LangChain.tools import read_file_tool, list_folder_tool, write_file_tool

# Initialize the LLM (replace with your desired model)
llm = OpenAI(model_name="text-davinci-003", temperature=0.7)

# Define tools
tools = [
    Tool(name="Read File", func=read_file_tool, description="Reads the content of a file."),
    Tool(name="List Folder", func=list_folder_tool, description="Lists the contents of a folder."),
    Tool(name="Write File", func=write_file_tool, description="Writes content to a file."),
]

# Initialize the agent
agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)

def query_langchain(prompt: str):
    """
    Query the LangChain agent with a user prompt.

    Args:
        prompt (str): User's input or task description.

    Returns:
        str: The response from the agent.
    """
    return agent.run(prompt)