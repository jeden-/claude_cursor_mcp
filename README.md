# Claude-Cursor MCP Orchestrator 🚀

Advanced orchestration system for bidirectional AI workflow management between Claude Desktop and Cursor AI.

## 🎯 What is this?

This MCP (Model Context Protocol) server enables Claude Desktop to orchestrate and manage tasks in Cursor AI, creating a powerful bidirectional AI workflow system.

## ✨ Features

- **17 Powerful Tools** for task management and orchestration
- **3 Resources** including real-time metrics
- **1 Workflow Prompt** generator
- **SQLite-based** persistent state management
- **Git integration** with auto-commit support
- **Concurrent task execution** with configurable limits
- **Activity logging** and monitoring
- **🆕 Retry mechanism** with exponential backoff
- **🆕 Task templates** for reusable workflows
- **🆕 Path validation** for security
- **🆕 Real-time metrics** and analytics

## 🛠️ Tools Available

### Core Tools
1. **execute_cursor_task** - Submit tasks for Cursor AI to execute
2. **get_task_status** - Check task status
3. **get_project_status** - Get comprehensive project state
4. **list_project_tasks** - List all project tasks with filtering
5. **cancel_task** - Cancel pending/running tasks
6. **get_activity_log** - Retrieve activity history
7. **get_system_stats** - Get system-wide statistics

### Advanced Tools
8. **retry_task** 🆕 - Retry failed tasks with exponential backoff
9. **save_task_template** 🆕 - Save tasks as reusable templates
10. **list_task_templates** 🆕 - List all saved templates
11. **create_task_from_template** 🆕 - Create task from template
12. **delete_task_template** 🆕 - Delete saved template
13. **monitor_api_communication** 🤖 - Monitor bidirectional communication with Cursor AI
14. **start_watching_project** 🔥 - Start automatic monitoring of API files
15. **stop_watching_project** 🔥 - Stop monitoring of API files
16. **get_watching_status** 🔥 - Get list of monitored projects
17. **create_cursor_rules** - Create/update .cursorrules files

## 📦 Resources

1. **orchestrator://projects** - List all managed projects
2. **orchestrator://logs** - Recent system logs
3. **orchestrator://live-updates** 🔥 - Live updates stream (SSE-compatible)
4. **orchestrator://metrics** 🆕 - Real-time performance metrics

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

## 🎨 Cursor Integration

The orchestrator integrates with Cursor in **instruction mode** by default:

1. **Task Creation**: When you execute a task, it creates a `.cursor-tasks/task_<id>.md` file
2. **Auto-Open**: Automatically opens the project and task file in Cursor
3. **Manual Execution**: You use Cursor's AI features (Cmd+K or Cmd+L) to implement the task
4. **Status Tracking**: Task status is tracked in the orchestrator

### Configuration Modes

In `Config` class:
- **`CURSOR_MODE = "api"`** (default) - **Bidirectional communication** between Claude Desktop and Cursor AI
- **`CURSOR_MODE = "instruction"`** - Creates task files for manual execution
- **`CURSOR_MODE = "auto"`** - Creates task files with auto-execute hints
- **`CURSOR_MODE = "mock"`** - Simulates execution for testing
- **`AUTO_OPEN_CURSOR = True`** - Automatically opens Cursor with task file

### 🤖 API Mode - Bidirectional Communication

**API mode enables automatic communication between Claude Desktop and Cursor AI:**

1. **Claude Desktop** sends task via orchestrator
2. **Orchestrator** creates task file + API communication file
3. **Cursor AI** executes task and updates API file with progress
4. **Orchestrator** monitors progress and reports back to Claude Desktop
5. **Claude Desktop** receives real-time updates

**Files created:**
- `task_xxx.md` - Task instructions
- `api_xxx.json` - Communication file with status/progress

**New tool:** `monitor_api_communication(task_id)` - Monitor real-time progress

### 🔥 Full Automation - NEW!

**Complete automatic workflow without user interaction:**

#### **File Watcher**
- Automatically monitors `.cursor-tasks/` directory for API file changes
- Detects when Cursor AI updates task progress
- Updates task status in database in real-time
- Notifies subscribers of changes

#### **Auto-Executor Script**
```bash
python cursor_auto_executor.py /path/to/project
```
- Watches for new tasks in `.cursor-tasks/`
- Automatically executes tasks
- Updates API files with progress (10%, 30%, 60%, 90%, 100%)
- Simulates Cursor AI behavior for testing

#### **Live Dashboard**
Open `dashboard.html` in browser:
- Real-time task monitoring
- Statistics and success rates
- List of monitored projects
- Auto-refresh every 5 seconds

#### **Tools for monitoring:**
- `start_watching_project(project_path)` - Start automatic monitoring
- `stop_watching_project(project_path)` - Stop monitoring
- `get_watching_status()` - List monitored projects
- `orchestrator://live-updates` - SSE stream of updates

### 🎯 How to Execute Tasks in Cursor

**Method 1: Cmd+K (Composer)**
1. Open task file in Cursor
2. Press `Cmd+K`
3. Type: `Zaimplementuj to zadanie zgodnie z instrukcjami`
4. Cursor AI will execute the code

**Method 2: Cmd+L (Chat)**
1. Press `Cmd+L`
2. Type: `Przeczytaj plik zadania i zaimplementuj schemat`
3. Cursor AI will analyze and execute

**Method 3: Auto Mode**
Set `CURSOR_MODE = "auto"` for task files with built-in execution hints.

### Cursor CLI Location

The orchestrator automatically uses Cursor CLI from:
```
/Applications/Cursor.app/Contents/Resources/app/bin/cursor
```

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
    CURSOR_MODE = "instruction"  # "instruction", "mock", or "api"
    
    # Path validation (empty list = allow all)
    ALLOWED_PROJECT_PATHS = []   # Disabled by default
    # Or specify allowed directories:
    # ALLOWED_PROJECT_PATHS = [
    #     Path.home() / "projects",
    #     Path.home() / "your-folder",
    # ]
```

### 🔒 Path Security

By default, path validation is **disabled** (`ALLOWED_PROJECT_PATHS = []`) to allow maximum flexibility.

To enable path restrictions, uncomment and configure allowed directories in the `Config` class.

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

