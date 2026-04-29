import subprocess
import os
import pdfplumber
from langchain_core.tools import tool

@tool
def execute_shell_command(command: str) -> str:
    """
    Use this tool to execute general shell/terminal commands. 
    Avoid using this for reading files or listing directories with Hebrew names.
    """
    try:
        print(f"\n[Tool Execution] Running Shell: {command}")
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

@tool
def list_files_in_directory(folder_path: str) -> str:
    """
    Use this tool to list all files in a specific folder. 
    It is very reliable for folders with Hebrew names and spaces.
    """
    try:
        print(f"\n[Tool Execution] Listing Directory: {folder_path}")
        # פייתון מטפל בעברית בנתיבים בצורה מושלמת לעומת ה-CMD
        files = os.listdir(folder_path)
        if not files:
            return "The directory is empty."
        
        return "\n".join([f"- {f}" for f in files])
    except Exception as e:
        return f"Error listing files: {str(e)}"

@tool
def read_pdf_content(file_path: str) -> str:
    """
    Use this tool to read the text content of a PDF file. 
    Safe for Hebrew file names and handles text extraction directly.
    """
    try:
        print(f"\n[Tool Execution] Reading PDF: {file_path}")
        all_text = []
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    all_text.append(f"--- Page {i+1} ---\n{text}")
        
        if not all_text:
            return "PDF opened but no text found (it might be scanned/images)."
            
        return "\n\n".join(all_text)
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

# רשימת הכלים שהסוכן יכיר
agent_tools = [execute_shell_command, list_files_in_directory, read_pdf_content]