from functools import lru_cache
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from my_agent.utils.tools import tools, search_agent, search_properties, search_properties_by_address
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, END
from my_agent.utils.parser import Answer, get_schema

flag= False

tool_node1 = ToolNode([search_properties])
tool_node2 = ToolNode([search_agent])
tool_node3 = ToolNode([search_properties_by_address])
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
    model = model.bind_tools([search_agent,search_properties, search_properties_by_address])
    return model

# Define the function that determines whether to continue or not
def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    # If there are no tool calls, then we finish
    if not last_message.tool_calls:           
        return "output_parser"
    # # Otherwise if there is, we continue
    else:
        return last_message.tool_calls[0]["name"]


system_prompt = """
Be a helpful assistant of HAR.com

Please review the property description for any language that may violate fair housing laws. Focus on identifying terms that could discriminate based on:

    1. **Family Status** (e.g., 'ideal for couples,' 'no children')
    2. **Race or National Origin** (e.g., references to ethnicity, specific nationalities)
    3. **Religion** (e.g., references to religious places, symbols )
    4. **Gender/Sex** (e.g., 'bachelor pad,' 'perfect for businessmen')
    5. **Disability** (e.g., 'must be able to climb stairs')
    6. **Age** (e.g., 'perfect for retirees')
    7. **Other** (e.g., 'no smokers,' 'must be employed')

Flag any potentially discriminatory terms and Respond with following:
'I'm sorry, but I cannot assist with this request as it may conflict with the Fair Housing Act, which ensures equal housing opportunities and prohibits discrimination based on race, color, religion, sex, disability, familial status, or national origin. HAR support the Fair Housing Act [[https://www.justice.gov/crt/fair-housing-act-1]], which protects everyone's right to equal housing opportunities. To learn more visit https://www.justice.gov/crt/fair-housing-act-1.'

 RESPONSE GUIDELINES:
    - Address HAR.com-related queries with priority
    - Acceptable topics:
        • General Salutation
        • HAR.com property listings and searches
        • Property details from HAR.com database
        • HAR.com search filters and features
        • General real estate terminology and concepts
        • Houston area property information and market trends
        • Basic real estate processes and procedures
        • General property-related questions
    - Prohibited topics:
        • Mentioning HARID in response
        • Other real estate websites or platforms
        • Personal financial advice
        • Legal advice or interpretations
        • **Non-real estate topics**
        • Personal opinions about market trends
    - [IMPORTANT] - For non-property related questions [or gibberish]: I can only assist with questions about HAR.com property listings and services. How can I help you find properties on HAR.com?
                    
"""

# Define the function that calls the model
def call_model(state, config):
    messages = state["messages"]
    messages = [{"role": "system", "content": system_prompt}] + messages
    model_name = config.get('configurable', {}).get("model_name", "openai")
    model = _get_model(model_name)
    response = model.invoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}

def output_parser(state, config):
    messages = state["messages"]
    Schema = get_schema(state)
    print(state["messages"][-1].name)
    card = None
    if (state["messages"][-1].name=="search_by_properties"):
        card ="whole property"
    prompt =f"""
        Be a helpful assistant and Extract the event information from last ai message. and create a JSON object with only relevant fields from the following schema:  {Schema}
        Card field should be None if the answer is not directly related to Agent ,{card} or School.
        If Card is None, pretext should contain all information to answer the user query.
    """
    messages = [{"role": "system", "content":  prompt}] + [messages[-1].content]
    print(messages)
    model = ChatOpenAI(temperature=0, model_name="gpt-4o")
    response = model.invoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}
