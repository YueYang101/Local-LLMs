# Local-LLMs
## workflow
This application allows the user to choose to use either local LLMs or the APIs of LLMs. 
<br>
With the pre-input prompts. The LLM is told the available local functions and their descriptions. With the user-input prompts, the LLM can choose the functions which can meet the demands of the user.
<br>
For now, after the LLM know which functions will be used, it will reply with the trigger word to trigger the corresponding functions (this is what LLM_decision function does).


Chain of thoughts
Firstly, the llm should output the chain of actions in json format like this
The output from the llm is still plain text format. However, it will be converted to the html format by using an additional function. the plain text response is generated with special marks for easier conversion.
## Local functions
