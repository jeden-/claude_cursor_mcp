# Claude-Cursor MCP Orchestrator 🚀

Advanced orchestration system for bidirectional AI workflow management between Claude Desktop and Cursor AI.

## 🎯 What is this?

This MCP (Model Context Protocol) server enables Claude Desktop to orchestrate and manage tasks in Cursor AI, creating a powerful bidirectional AI workflow system.

## ✨ Features

- **8 Powerful Tools** for task management and orchestration
- **3 Resources** for project state and logs
- **1 Workflow Prompt** generator
- **SQLite-based** persistent state management
- **Git integration** with auto-commit support
- **Concurrent task execution** with configurable limits
- **Activity logging** and monitoring

## 🛠️ Tools Available

1. **execute_cursor_task** - Submit tasks for Cursor AI to execute
2. **get_task_status** - Check task status
3. **get_project_status** - Get comprehensive project state
4. **list_project_tasks** - List all project tasks with filtering
5. **cancel_task** - Cancel pending/running tasks
6. **create_cursor_rules** - Create/update .cursorrules files
7. **get_activity_log** - Retrieve activity history
8. **get_system_stats** - Get system-wide statistics

## 📦 Installation

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager
- Claude Desktop
- Cursor AI (optional, for full functionality)

### Setup

1. **Clone the repository:**
```bash
git clone https://github.com/jeden-/claude_cursor_mcp.git
cd claude_cursor_mcp
```

2. **Install dependencies:**
```bash
uv init
uv add "mcp[cli]"
uv add aiofiles watchdog
```

3. **Configure Claude Desktop:**

Edit your Claude Desktop config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

Add this configuration:

```json
{
  "mcpServers": {
    "cursor-orchestrator": {
      "command": "/path/to/uv",
      "args": [
        "--directory",
        "/path/to/claude_cursor_mcp",
        "run",
        "cursor_orchestrator_advanced.py"
      ]
    }
  }
}
```

**Important**: Use full paths! Find your `uv` path with: `which uv`

4. **Restart Claude Desktop**

## 🧪 Testing with MCP Inspector

```bash
uv run mcp dev cursor_orchestrator_advanced.py
```

Opens interactive browser interface at http://localhost:6274

## 📖 Usage Examples

### Basic Task Execution

In Claude Desktop:
```
Execute a task in project /Users/me/myapp:
- Description: Add dark mode support
- Priority: high
```

### System Monitoring

```
Show me system stats and all active projects
```

### Workflow Generation

```
Generate workflow for project MyApp with goal: Implement user authentication
```

## ⚙️ Configuration

Edit the `Config` class in `cursor_orchestrator_advanced.py`:

```python
class Config:
    MAX_CONCURRENT_TASKS = 3     # Max parallel tasks
    TASK_TIMEOUT = 300           # 5 minutes
    GIT_AUTO_COMMIT = True       # Auto-commit changes
```

## 📊 System Architecture

- **StateManager**: SQLite-based persistent storage
- **TaskExecutor**: Async task queue and execution
- **CursorInterface**: Cursor CLI integration
- **GitInterface**: Git operations
- **FastMCP**: MCP server framework

## 📁 Project Structure

```
claude_cursor_mcp/
├── cursor_orchestrator_advanced.py  # Main server code
├── orchestrator_setup_guide.md      # Detailed setup guide
├── orchestrator_config_files.md     # Additional config examples
├── pyproject.toml                   # Project dependencies
└── README.md                        # This file
```

## 🗄️ Database

State stored in: `~/.claude-cursor-orchestrator/state.db`

Tables:
- **tasks** - Task history and status
- **projects** - Project states
- **activity_log** - System activity

## 📝 Logs

System logs: `~/.claude-cursor-orchestrator/orchestrator.log`

## 🔧 Troubleshooting

### "spawn uv ENOENT" error
Use full path to `uv` in config (find with `which uv`)

### Cursor CLI not found
Install from: https://cursor.com/install

### Port conflicts
Only run one instance (either Inspector OR Claude Desktop integration)

## 📚 Documentation

See detailed guides:
- [Setup Guide](orchestrator_setup_guide.md) - Complete installation walkthrough
- [Config Files](orchestrator_config_files.md) - Additional configurations

## 🤝 Contributing

Contributions welcome! Please feel free to submit issues and pull requests.

## 📄 License

MIT License - feel free to use in your projects!

## 🙏 Credits

Built with:
- [MCP SDK](https://github.com/modelcontextprotocol/python-sdk) by Anthropic
- [FastMCP](https://github.com/jlowin/fastmcp) framework
- [uv](https://github.com/astral-sh/uv) by Astral

## ⭐ Star if useful!

If this project helps you, please consider giving it a star! ⭐

---

**Made with ❤️ for the AI development community**

