import json
import os
import contextlib
from pydantic import BaseModel
from typing import Optional, List, Dict
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

CONFIG_FILE = "mcp_config.json"

# 1. הגדרת הממשק
class MCPConnectionConfig(BaseModel):
    connection_type: str 
    
    # הגדרות עבור Stdio
    command: Optional[str] = None      
    args: Optional[List[str]] = None   
    env: Optional[Dict[str, str]] = None 
    
    # הגדרות עבור SSE
    url: Optional[str] = None          

# 2. מנהל החיבורים
class MCPManager:
    def __init__(self):
        self.exit_stack = contextlib.AsyncExitStack()
        self.active_sessions: Dict[str, ClientSession] = {}

    def _save_config(self, server_name: str, config: MCPConnectionConfig):
        """פונקציה פנימית ששומרת את ההגדרות לקובץ ה-JSON"""
        configs = {}
        # קריאת הקובץ הקיים (אם יש) כדי לא לדרוס שרתים אחרים
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    configs = json.load(f)
            except json.JSONDecodeError:
                pass
        
        # הוספת השרת החדש (הופכים את ה-Pydantic למילון רגיל)
        configs[server_name] = config.model_dump()
        
        # כתיבה חזרה לקובץ
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(configs, f, indent=4, ensure_ascii=False)

    async def load_saved_servers(self):
        """קורא את קובץ ה-JSON ומתחבר לכל השרתים שנשמרו בעבר"""
        if not os.path.exists(CONFIG_FILE):
            return
            
        print("\n📦 Loading saved MCP servers from config...")
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                configs = json.load(f)
                
            for server_name, config_dict in configs.items():
                print(f"🔄 Auto-connecting to {server_name}...")
                config = MCPConnectionConfig(**config_dict)
                # קריאה לחיבור מבלי לשמור שוב ל-JSON
                await self._connect_internal(server_name, config)
        except Exception as e:
            print(f"❌ Error loading config: {str(e)}")

    async def connect_to_server(self, server_name: str, config: MCPConnectionConfig):
        """חיבור לשרת חדש דרך ה-UI (כולל שמירה ל-JSON)"""
        success = await self._connect_internal(server_name, config)
        if success:
            self._save_config(server_name, config)
        return success

    async def _connect_internal(self, server_name: str, config: MCPConnectionConfig):
        """לוגיקת החיבור עצמה"""
        try:
            if config.connection_type == "stdio":
                server_params = StdioServerParameters(
                    command=config.command,
                    args=config.args or [],
                    env=config.env
                )
                transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
                
            elif config.connection_type == "sse":
                transport = await self.exit_stack.enter_async_context(sse_client(config.url))
                
            else:
                raise ValueError(f"Unknown connection type: {config.connection_type}")

            session = await self.exit_stack.enter_async_context(ClientSession(*transport))
            await session.initialize()
            
            self.active_sessions[server_name] = session
            print(f"✅ Connected successfully to MCP server: {server_name}")
            return True

        except Exception as e:
            print(f"❌ Failed to connect to {server_name}: {str(e)}")
            return False

    async def get_all_tools(self):
        all_tools = []
        for name, session in self.active_sessions.items():
            response = await session.list_tools()
            all_tools.extend(response.tools)
        return all_tools