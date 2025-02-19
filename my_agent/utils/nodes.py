from functools import lru_cache
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from my_agent.utils.tools import tools, search_agent, search_properties
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, END


tool_node1 = ToolNode([search_properties])
tool_node2 = ToolNode([search_agent])
@lru_cache(maxsize=4)
def _get_model(model_name: str):
    if model_name == "openai":
        model = ChatOpenAI(temperature=0, model_name="gpt-4o")
    elif model_name == "anthropic":
        model =  ChatAnthropic(temperature=0, model_name="claude-3-sonnet-20240229")
    else:
        model = ChatOpenAI(temperature=0, model_name="gpt-4o")
        # raise ValueError(f"Unsupported model type: {model_name}")

    # model = model.bind_tools([])
    model = model.bind_tools([search_agent,search_properties])
    return model

# Define the function that determines whether to continue or not
def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    # If there are no tool calls, then we finish
    if not last_message.tool_calls:
        return END
    # Otherwise if there is, we continue
    else:
        return last_message.tool_calls[0]["name"]


system_prompt = """Be a helpful assistant"""

# Define the function that calls the model
def call_model(state, config):
    messages = state["messages"]
    messages = [{"role": "system", "content": system_prompt}] + messages
    model_name = config.get('configurable', {}).get("model_name", "openai")
    model = _get_model(model_name)
    response = model.invoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}

# Define the function to execute tools
print(tools)