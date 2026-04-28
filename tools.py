import subprocess
from langchain_core.tools import tool
# אם התקנת את DuckDuckGo, הוסף גם את הייבוא שלו כאן

@tool
def execute_shell_command(command: str) -> str:
    """
    Use this tool to execute a shell/terminal command on the local Windows machine.
    """
    try:
        print(f"\n[Tool Execution] Running: {command}")
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        if result.returncode == 0:
            return result.stdout if result.stdout else "Command executed successfully."
        else:
            return f"Error: {result.stderr}"
    except Exception as e:
        return f"Execution failed: {str(e)}"

# השורה שחסרה לך ושגורמת לשגיאה:
agent_tools = [execute_shell_command]