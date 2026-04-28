# Deep-Agent

A powerful autonomous agent framework built with **LangGraph** and **Claude AI**, designed to execute tasks through intelligent tool orchestration.

## 🎯 Overview

Deep-Agent is an intelligent automation system that combines state-based workflow orchestration with Claude's advanced reasoning capabilities. The agent can analyze requests, determine which tools to use, execute commands, and learn from results in a continuous feedback loop.

### Key Features

- **LLM-Powered Intelligence**: Uses Claude Sonnet 4.6 for advanced reasoning
- **Tool Integration**: Extensible tool system for executing shell commands and custom operations
- **State Management**: TypedDict-based state system for maintaining context throughout execution
- **Graph-Based Orchestration**: LangGraph workflow for managing agent decision-making
- **Environment Configuration**: Secure API key management via environment variables

## 📋 Architecture

The system is built on three core components:

1. **The Brain** (LLM Node)
   - Powered by Claude Sonnet 4.6
   - Analyzes requests and determines next actions
   - Bound with available tools for task execution

2. **The Tools** (Tool Execution)
   - Shell command execution on Windows
   - Extensible design for adding custom tools
   - Error handling and result processing

3. **The Orchestrator** (LangGraph)
   - Manages workflow state and transitions
   - Routes between agent reasoning and tool execution
   - Implements conditional logic for continuous operation

## 🚀 Getting Started

### Prerequisites

- Python 3.14+
- Anthropic API key
- uv (for dependency management)

### Installation

1. Clone or navigate to the project directory:
```bash
cd deep-agent
```

2. Install dependencies:
```bash
uv sync
```

3. Set up environment variables:
Create a `.env` file in the project root:
```
ANTHROPIC_API_KEY=your_api_key_here
```

### Running the Agent

Execute the agent with:
```bash
uv run main.py
```

The agent will process the input request and execute any necessary tools to complete the task.

## 📁 Project Structure

```
deep-agent/
├── main.py              # Agent orchestration and main execution loop
├── tools.py             # Tool definitions and implementations
├── pyproject.toml       # Project configuration and dependencies
└── README.md           # This file
```

## 🔧 Dependencies

- **langchain-anthropic** >= 1.4.1 - Claude integration
- **langchain-core** >= 1.3.2 - LangChain core utilities
- **langgraph** >= 1.1.10 - Workflow orchestration
- **python-dotenv** >= 1.2.2 - Environment management

## 💡 How It Works

1. **Request Processing**: User input is sent to the agent
2. **Agent Reasoning**: Claude analyzes the request and determines if tools are needed
3. **Tool Execution**: If tools are required, they are executed with the determined parameters
4. **Response Generation**: The agent processes tool results and provides a response
5. **Iteration**: The loop continues until the task is complete

## 🛠️ Extending the Agent

### Adding New Tools

To add new tools, simply define them in `tools.py` using the `@tool` decorator:

```python
@tool
def my_custom_tool(param: str) -> str:
    """Description of what the tool does."""
    # Implementation here
    return result

# Add to the agent_tools list
agent_tools = [execute_shell_command, my_custom_tool]
```

### Customizing the Agent Behavior

Modify the `should_continue` function in `main.py` to implement custom routing logic or add state-based decision making.

## 📝 License

This project is part of the Daniel Pro Agent ecosystem.

## 🤝 Contributing

Contributions are welcome! Please ensure code is well-documented and follows the existing patterns.

---

**Built with ❤️ using Claude AI and LangGraph**
