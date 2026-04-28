import os
from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_anthropic import ChatAnthropic

# שואבים את הכלים שלנו מקובץ הכלים הנפרד
from tools import agent_tools

# Load API key from environment
load_dotenv()

# ==========================================
# State (The State / Temporary Memory)
# ==========================================
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# Feed the imported tools into a node in the graph
tool_node = ToolNode(agent_tools)

# ==========================================
# The Brain (LLM Node)
# ===========================================
llm = ChatAnthropic(model="claude-sonnet-4-6")

# Bind the imported tools to the model
llm_with_tools = llm.bind_tools(agent_tools)

def call_model(state: AgentState):
    response = llm_with_tools.invoke(state['messages'])
    return {"messages": [response]}

# ==========================================
# The Orchestrator (LangGraph Orchestrator)
# ===========================================
def should_continue(state: AgentState):
    last_message = state['messages'][-1]
    if last_message.tool_calls:
        return "tools"
    return END

workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, ["tools", END])
workflow.add_edge("tools", "agent")

app = workflow.compile()

# ==========================================
# Local Execution
# ==========================================
if __name__ == "__main__":
    # Modified the request slightly to verify everything works after the split
    user_input = "List the files in this directory so I can verify that the split to main.py and tools.py was successful."
    print(f"User: {user_input}\n")
    
    for event in app.stream({"messages": [("user", user_input)]}):
        for key, value in event.items():
            if key == "agent":
                msg = value["messages"][-1]
                if msg.content:
                    print(f"Agent: {msg.content}")