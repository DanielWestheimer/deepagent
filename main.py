import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.responses import FileResponse, StreamingResponse
import json
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_anthropic import ChatAnthropic

# Import our tools
from tools import agent_tools

from mcp_manager import MCPConnectionConfig, MCPManager
import asyncio
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from fastapi.staticfiles import StaticFiles

load_dotenv()
mcp_manager = MCPManager()
main_loop = None
app_api = FastAPI(title="Deep Agent API")
app_api.mount("/static", StaticFiles(directory="frontend"), name="static")

@app_api.on_event("startup")
async def startup_event():
    global main_loop
    main_loop = asyncio.get_running_loop()
    await mcp_manager.load_saved_servers()

# 2. כלי לאיתור יכולות MCP
@tool
def get_mcp_tools() -> str:
    """Use this tool to see what external MCP tools are currently connected and available."""
    if not mcp_manager.active_sessions:
        return "No MCP servers connected."
    
    result = ""
    for server_name, session in mcp_manager.active_sessions.items():
        # שליפת הכלים מהשרת החיצוני
        future = asyncio.run_coroutine_threadsafe(session.list_tools(), main_loop)
        response = future.result()
        for t in response.tools:
            result += f"Server: {server_name} | Tool: {t.name}\nDescription: {t.description}\nSchema: {t.inputSchema}\n\n"
    return result

# 3. כלי להפעלת יכולות MCP
@tool
def run_mcp_tool(server_name: str, tool_name: str, arguments: dict) -> str:
    """Run an external MCP tool using the server_name, tool_name, and a dictionary of arguments."""
    session = mcp_manager.active_sessions.get(server_name)
    if not session:
        return f"Server {server_name} not found."
    
    try:
        # שליחת הפקודה לשרת החיצוני והמתנה לתשובה
        future = asyncio.run_coroutine_threadsafe(session.call_tool(tool_name, arguments), main_loop)
        response = future.result()
        
        # חילוץ הטקסט נטו מהתשובה של השרת
        texts = [c.text for c in response.content if c.type == "text"]
        return "\n".join(texts)
    except Exception as e:
        return f"MCP Tool Error: {str(e)}"

# 4. הזרקת הגשר לתוך המוח של הסוכן
agent_tools.append(get_mcp_tools)
agent_tools.append(run_mcp_tool)

# Define the format for receiving messages from the Web
class ChatRequest(BaseModel):
    message: str
    thread_id: str

# --- LangGraph logic (remains mostly the same) ---
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

tool_node = ToolNode(agent_tools)
llm = ChatAnthropic(model="claude-sonnet-4-6")
llm_with_tools = llm.bind_tools(agent_tools)

def call_model(state: AgentState):
    response = llm_with_tools.invoke(state['messages'])
    return {"messages": [response]}

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

memory = MemorySaver()
agent_app = workflow.compile(checkpointer=memory)

# --- API endpoint ---

@app_api.get("/")
async def serve_frontend():
    return FileResponse("frontend/index.html")

@app_api.post("/chat")
async def chat_endpoint(request: ChatRequest):
    def event_stream():
        try:
            config = {"configurable": {"thread_id": request.thread_id}}

            # Instead of invoke, we use stream that goes step by step
            for event in agent_app.stream({"messages": [("user", request.message)]}, config=config):
                for node_name, node_data in event.items():
                    
                    # If the brain (model) is working
                    if node_name == "agent":
                        msg = node_data["messages"][-1]
                        
                        # If it decided to activate a tool
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            for tool in msg.tool_calls:
                                tool_name = tool["name"]
                                payload = {
                                    "type": "thinking", 
                                    "content": f"🛠️ Activating tool: {tool_name}..."
                                }
                                yield f"data: {json.dumps(payload)}\n\n"
                        
                        # If it decided to write us a final answer
                        elif msg.content:
                            yield f"data: {json.dumps({'type': 'final', 'content': msg.content})}\n\n"
                            
                    # If the tool finished its work
                    elif node_name == "tools":
                        yield f"data: {json.dumps({'type': 'thinking', 'content': '✅ Tool finished, analyzing results...'})}\n\n"
        
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    # Return the response as a live data stream (Server-Sent Events)
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app_api.post("/mcp/connect")
async def connect_mcp_endpoint(server_name: str, config: MCPConnectionConfig):
    success = await mcp_manager.connect_to_server(server_name, config)
    if success:
        return {"success": True, "message": f"Connected to {server_name}"}
    else:
        return {"success": False, "message": "Failed to connect. Check server logs."}

# Run the server (only if running directly)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app_api, host="0.0.0.0", port=8000)
