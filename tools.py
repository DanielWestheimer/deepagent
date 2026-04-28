import subprocess
from langchain_core.tools import tool

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

# Wrap all the tools we wrote into one list that we'll expose externally
agent_tools = [execute_shell_command]