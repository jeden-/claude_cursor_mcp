# Claude-Cursor MCP Orchestrator 🚀

Advanced orchestration system for bidirectional AI workflow management between Claude Desktop and Cursor AI.

## 🎯 What is this?

This MCP (Model Context Protocol) server enables Claude Desktop to orchestrate and manage tasks in Cursor AI, creating a powerful bidirectional AI workflow system.

## ✨ Features

- **18 Powerful Tools** for task management and orchestration including **Claude Supervisor**
- **5 Resources** including real-time metrics, live updates, and **communication guide**
- **SQLite-based** persistent state management
- **Git integration** with auto-commit support
- **Concurrent task execution** with configurable limits
- **Activity logging** and monitoring
- **🆕 Retry mechanism** with exponential backoff
- **🆕 Task templates** for reusable workflows
- **🆕 Path validation** for security (disabled by default)
- **🆕 Real-time metrics** and analytics
- **🔥 Bidirectional communication** - Claude ↔ Orchestrator ↔ Cursor AI
- **🔥 File Watcher** - automatic monitoring of API files
- **🔥 Live Dashboard** - real-time task visualization
- **🎯 Claude Supervisor** - automatic task verification and correction

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
17. **supervise_cursor_task** 🎯 - **Claude jako nadzorca** - pilnuje i poprawia Cursor AI
18. **create_cursor_rules** - Create/update .cursorrules files

## 📦 Resources

1. **orchestrator://projects** - List all managed projects
2. **orchestrator://logs** - Recent system logs
3. **orchestrator://live-updates** 🔥 - Live updates stream (SSE-compatible)
4. **orchestrator://metrics** 🆕 - Real-time performance metrics
5. **orchestrator://communication-guide** ⭐ - Complete guide for Claude-Cursor communication

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

### 📖 Communication Guide - Built-in Context

**No more manual context setup!** The orchestrator includes a comprehensive communication guide as an MCP resource:

**Access in Claude Desktop:**
Claude can automatically read `orchestrator://communication-guide` to get complete instructions on how to:
- Send tasks to Cursor AI
- Choose the right communication method (single task, checkboxes, API mode)
- Monitor progress and receive feedback
- Use supervise_cursor_task for automatic verification
- Apply best practices

**This means:**
- ✅ No need to manually paste instructions in every conversation
- ✅ Claude always knows the latest communication patterns
- ✅ Consistent workflow across all projects
- ✅ Automatic updates when you modify the guide

**Claude Desktop will automatically use this resource** when needed!

### 🎯 Claude Supervisor - **Claude pilnuje Cursor AI!**

**Twoje marzenie się spełniło!** Claude działa jako nadzorca który:

1. **Zleca zadanie** Cursorowi
2. **Sprawdza wynik** według kryteriów akceptacji
3. **Znajduje błędy** i braki
4. **Automatycznie poprawia** - re-submituje zadanie z poprawkami
5. **Iteruje** aż do sukcesu (max 3 razy)
6. **Raportuje** wszystkie iteracje i wynik końcowy

#### **Przykład użycia:**

```python
supervise_cursor_task(
    project_path="/Users/mariusz/amgsquant",
    task_description="Stwórz formularz logowania w React",
    acceptance_criteria=[
        "Formularz ma pola email i password",
        "Jest walidacja formatu email",
        "Hasło ma minimum 8 znaków",
        "Jest obsługa błędów API",
        "Są testy jednostkowe"
    ],
    max_iterations=3
)
```

#### **Workflow:**
```
TY → Claude: "Stwórz formularz logowania"
  ↓
Claude → Cursor: "Create login form..."
  ↓
Cursor → tworzy kod
  ↓
Claude → sprawdza:
  ❌ "Brakuje walidacji email"
  ❌ "Nie ma error handling"
  ↓
Claude → Cursor: "Dodaj walidację i error handling"
  ↓
Cursor → poprawia
  ↓
Claude → sprawdza ponownie:
  ✅ "Wszystko OK!"
  ↓
Claude → Ty: "Formularz gotowy! ✅"
```

**To jest dokładnie to co chciałeś! 🎉**

### 🔥 Full Automation - NEW!

**Complete automatic workflow with bidirectional communication:**

#### **File Watcher (Built-in)**
- Automatically monitors `.cursor-tasks/` directory for API file changes
- Detects when Cursor AI updates task progress
- Updates task status in database in real-time
- Notifies Claude Desktop of changes via SSE

#### **Auto-Executor Script** (for testing)
```bash
uv run python cursor_auto_executor.py /path/to/project
```
- Watches for new tasks in `.cursor-tasks/`
- Automatically "executes" tasks (simulation)
- Updates API files with progress (10%, 30%, 60%, 90%, 100%)
- Useful for testing the communication flow

#### **Live Dashboard**
```bash
uv run python dashboard_server.py
```
Then open http://localhost:8080 in browser:
- Real-time task monitoring from SQLite database
- Statistics and success rates
- List of monitored projects
- Recent tasks with status
- Auto-refresh every 5 seconds

#### **Tools for monitoring:**
- `start_watching_project(project_path)` - Start automatic monitoring
- `stop_watching_project(project_path)` - Stop monitoring
- `get_watching_status()` - List monitored projects
- `monitor_api_communication(task_id)` - Monitor specific task
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
├── cursor_orchestrator_advanced.py  # Main MCP server code
├── dashboard_server.py              # Live dashboard HTTP server
├── dashboard.html                   # Real-time monitoring UI
├── cursor_auto_executor.py          # Testing script (simulates Cursor AI)
├── claude_supervisor.py             # Example supervisor usage
├── orchestrator_setup_guide.md      # Detailed setup guide
├── orchestrator_config_files.md     # Additional config examples
├── pyproject.toml                   # Project dependencies
├── uv.lock                          # Locked dependencies
└── README.md                        # This file
```

## 🗄️ Database

State stored in: `~/.claude-cursor-orchestrator/state.db`

Tables:
- **tasks** - Task history and status
- **projects** - Project states
- **activity_log** - System activity
- **task_templates** - Reusable task templates

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

