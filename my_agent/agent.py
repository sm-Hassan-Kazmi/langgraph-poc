from typing import TypedDict, Literal

from langgraph.graph import StateGraph, END
from utils.nodes import call_model, should_continue, tool_node1,tool_node2, output_parser, tool_node3
from utils.state import AgentState

from langchain_core.messages import HumanMessage
# Define the config
class GraphConfig(TypedDict):
    model_name: Literal[ "openai"]


# Define a new graph
workflow = StateGraph(AgentState, config_schema=GraphConfig)

# Define the two nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("output_parser", output_parser)
workflow.add_node("search_properties", tool_node1)
workflow.add_node("search_agent", tool_node2)
workflow.add_node("search_properties_by_address", tool_node3)

# Set the entrypoint as `agent`
# This means that this node is the first one called
workflow.set_entry_point("agent")

# We now add a conditional edge
workflow.add_conditional_edges(
    # First, we define the start node. We use `agent`.
    # This means these are the edges taken after the `agent` node is called.
    "agent",
    # Next, we pass in the function that will determine which node is called next.
    should_continue,
    # Finally we pass in a mapping.
    # The keys are strings, and the values are other nodes.
    # END is a special node marking that the graph should finish.
    # What will happen is we will call `should_continue`, and then the output of that
    # will be matched against the keys in this mapping.
    # Based on which one it matches, that node will then be called.
        # If `tools`, then we call the tool node.
       [  "search_properties","search_agent","search_properties_by_address", "output_parser"],
)

# We now add a normal edge from `tools` to `agent`.
# This means that after `tools` is called, `agent` node is called next.
workflow.add_edge("search_properties", "output_parser")
workflow.add_edge("search_agent", "output_parser")
workflow.add_edge("search_properties_by_address", "output_parser")
# workflow.add_edge("output_parser", "agent")
workflow.add_edge("output_parser", END)

# Finally, we compile it!
# This compiles it into a LangChain Runnable,
# meaning you can use it as you would any other runnable
from langgraph.checkpoint.mysql.pymysql import PyMySQLSaver
from datetime import datetime
import uuid

# Database configuration
# DB_URI = "mysql://root:@localhost:3306/local_db"
DB_URI = "mysql://admin:the_password_you_wish_here@localhost:3306/local_db"

# write_config = {"configurable": {"thread_id": "1", "checkpoint_ns": ""}}
# read_config = {"configurable": {"thread_id": "1"}}
# Generate unique ID and timestamp
checkpoint_id = str(uuid.uuid4())
timestamp = datetime.utcnow().isoformat()
user_query = "hello aisearch"
chatbot_response = "elo user"
# Prepare checkpoint data
checkpoint = {
    "v": 1,
    "ts": timestamp,
    "id": checkpoint_id,
    "channel_values": {
        "user_query": user_query,
        "chatbot_response": chatbot_response,
    },
    "pending_sends": [],
}
write_config = {
    "configurable": {
        "id": str(uuid.uuid4()),
        "thread_id": str(uuid.uuid4()),
        "checkpoint_ns": "chat_history",
    }
}
read_config = {
    "configurable": {
        "thread_id": write_config["configurable"]["thread_id"],
        "checkpoint_ns": "chat_history"
    }
}




with PyMySQLSaver.from_conn_string(DB_URI) as saver:
    graph = workflow.compile(checkpointer=saver)
    messages = HumanMessage(content="Show me properties in 77027", name="model")
    result = graph.invoke({"messages": [messages]}, config=write_config)
    # Print the result
    for m in result["messages"]:
        m.pretty_print()
# Store the chatbot response in MySQL
# with PyMySQLSaver.from_conn_string(DB_URI) as checkpointer:

    # checkpointer.setup()  # Run only once initially
    # checkpointer.put(write_config, checkpoint, {}, {})
    # # Retrieve the saved data
    # stored_data = checkpointer.get(read_config)
    # print("Stored Data:", stored_data)
    # # List all stored checkpoints
    # print("All Checkpoints:", list(checkpointer.list(read_config)))

    # graph = workflow.compile(checkpointer=checkpointer)
