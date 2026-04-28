import os
import subprocess
from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool

# טעינת מפתח ה-API מקובץ ה-.env
load_dotenv()

# 1. State - ניהול מצב והיסטוריית הודעות
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# 2. Tool - הכלי שיודע להריץ פקודות בווינדוס
@tool
def execute_shell_command(command: str) -> str:
    """
    Use this tool to execute a shell/terminal command on the local Windows machine.
    Input should be a valid command (e.g., dir, echo, mkdir).
    """
    try:
        print(f"\n[Tool Execution] Running: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error: {result.stderr}"
    except Exception as e:
        return f"Execution failed: {str(e)}"

tools = [execute_shell_command]
tool_node = ToolNode(tools)

# 3. LLM - הגדרת המודל והכלים שלו
llm = ChatAnthropic(model="claude-sonnet-4-6")
llm_with_tools = llm.bind_tools(tools)

def call_model(state: AgentState):
    response = llm_with_tools.invoke(state['messages'])
    return {"messages": [response]}

# 4. Orchestrator - בניית הגרף והניתוב
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

# הרצה בפועל
if __name__ == "__main__":
    user_input = "תיצור בבקשה תיקייה חדשה בשם 'test_folder' ואז תריץ פקודה שתדפיס לי את רשימת הקבצים והתיקיות פה כדי שאוודא שהיא באמת נוצרה."
    print(f"User: {user_input}\n")
    
    # הזרמת התהליך והדפסת הפלט
    for event in app.stream({"messages": [("user", user_input)]}):
        for key, value in event.items():
            if key == "agent":
                msg = value["messages"][-1]
                if msg.content:
                    print(f"Agent: {msg.content}")