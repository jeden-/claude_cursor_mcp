"""
Claude-Cursor Advanced Orchestration MCP Server
Production-ready system for bidirectional AI workflow management
"""

import os
import json
import asyncio
import subprocess
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from mcp.server.fastmcp import FastMCP

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Centralized configuration"""
    DB_PATH = Path.home() / ".claude-cursor-orchestrator" / "state.db"
    LOG_PATH = Path.home() / ".claude-cursor-orchestrator" / "orchestrator.log"
    MAX_CONCURRENT_TASKS = 3
    TASK_TIMEOUT = 300  # 5 minutes
    CURSOR_CLI = "/Applications/Cursor.app/Contents/Resources/app/bin/cursor"
    CURSOR_MODE = "instruction"  # "instruction", "mock", "auto", or "api" (bidirectional)
    GIT_AUTO_COMMIT = True
    AUTO_OPEN_CURSOR = True  # Automatically open project in Cursor
    
    # Security: Allowed project paths (empty list = allow all)
    # Set to [] to disable restrictions and allow all paths
    ALLOWED_PROJECT_PATHS = []  # Disabled - allows all paths in home directory
    
    # Or specify allowed directories:
    # ALLOWED_PROJECT_PATHS = [
    #     Path.home() / "projects",
    #     Path.home() / "work", 
    #     Path.home() / "Documents",
    #     Path.home() / "fakturowanie",  # Add your custom paths here
    # ]
    
    @classmethod
    def ensure_dirs(cls):
        """Create necessary directories"""
        cls.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate_project_path(cls, path: str) -> bool:
        """Validate if project path is allowed"""
        # If no restrictions, allow all
        if not cls.ALLOWED_PROJECT_PATHS:
            return True
        
        try:
            project_path = Path(path).resolve()
            # Check if path exists
            if not project_path.exists():
                logger.warning(f"Project path does not exist: {path}")
                return False
            
            # Check if path is within allowed directories
            for allowed_path in cls.ALLOWED_PROJECT_PATHS:
                try:
                    allowed_path = allowed_path.resolve()
                    if project_path.is_relative_to(allowed_path):
                        return True
                except (ValueError, RuntimeError):
                    continue
            
            logger.warning(f"Project path not in allowed directories: {path}")
            return False
        except Exception as e:
            logger.error(f"Error validating path {path}: {e}")
            return False

# ============================================================================
# LOGGING
# ============================================================================

Config.ensure_dirs()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_PATH),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("orchestrator")

# ============================================================================
# DATA MODELS
# ============================================================================

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Task:
    id: str
    project_path: str
    description: str
    command: str
    status: TaskStatus
    priority: TaskPriority
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    
    def to_dict(self):
        d = asdict(self)
        d['status'] = self.status.value
        d['priority'] = self.priority.value
        return d

@dataclass
class ProjectState:
    path: str
    name: str
    active_tasks: List[str]
    completed_tasks: int
    failed_tasks: int
    last_activity: str
    cursor_status: str
    git_branch: Optional[str] = None
    git_status: Optional[str] = None

# ============================================================================
# DATABASE MANAGER
# ============================================================================

class StateManager:
    """Manages persistent state using SQLite"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                project_path TEXT NOT NULL,
                description TEXT NOT NULL,
                command TEXT NOT NULL,
                status TEXT NOT NULL,
                priority INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                result TEXT,
                error TEXT,
                context TEXT
            )
        """)
        
        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                path TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                completed_tasks INTEGER DEFAULT 0,
                failed_tasks INTEGER DEFAULT 0,
                last_activity TEXT,
                cursor_status TEXT DEFAULT 'idle',
                git_branch TEXT,
                git_status TEXT
            )
        """)
        
        # Activity log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                project_path TEXT,
                task_id TEXT,
                event_type TEXT NOT NULL,
                details TEXT
            )
        """)
        
        # Task templates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_templates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                command TEXT NOT NULL,
                priority TEXT NOT NULL,
                tags TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                use_count INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_task(self, task: Task):
        """Save or update task"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task.id, task.project_path, task.description, task.command,
            task.status.value, task.priority.value, task.created_at,
            task.started_at, task.completed_at, task.result, task.error,
            json.dumps(task.context) if task.context else None
        ))
        
        conn.commit()
        conn.close()
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Retrieve task by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return Task(
            id=row[0],
            project_path=row[1],
            description=row[2],
            command=row[3],
            status=TaskStatus(row[4]),
            priority=TaskPriority(row[5]),
            created_at=row[6],
            started_at=row[7],
            completed_at=row[8],
            result=row[9],
            error=row[10],
            context=json.loads(row[11]) if row[11] else None
        )
    
    def get_project_tasks(self, project_path: str, status: Optional[TaskStatus] = None) -> List[Task]:
        """Get all tasks for a project"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status:
            cursor.execute(
                "SELECT * FROM tasks WHERE project_path = ? AND status = ? ORDER BY priority DESC, created_at",
                (project_path, status.value)
            )
        else:
            cursor.execute(
                "SELECT * FROM tasks WHERE project_path = ? ORDER BY priority DESC, created_at",
                (project_path,)
            )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [Task(
            id=r[0], project_path=r[1], description=r[2], command=r[3],
            status=TaskStatus(r[4]), priority=TaskPriority(r[5]),
            created_at=r[6], started_at=r[7], completed_at=r[8],
            result=r[9], error=r[10],
            context=json.loads(r[11]) if r[11] else None
        ) for r in rows]
    
    def update_project_state(self, project_path: str, **kwargs):
        """Update project state"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if project exists
        cursor.execute("SELECT path FROM projects WHERE path = ?", (project_path,))
        exists = cursor.fetchone() is not None
        
        if not exists:
            # Create new project entry
            name = Path(project_path).name
            cursor.execute("""
                INSERT INTO projects (path, name, last_activity)
                VALUES (?, ?, ?)
            """, (project_path, name, datetime.now().isoformat()))
        
        # Update fields
        for key, value in kwargs.items():
            cursor.execute(f"UPDATE projects SET {key} = ? WHERE path = ?", (value, project_path))
        
        cursor.execute("UPDATE projects SET last_activity = ? WHERE path = ?",
                      (datetime.now().isoformat(), project_path))
        
        conn.commit()
        conn.close()
    
    def get_project_state(self, project_path: str) -> Optional[ProjectState]:
        """Get project state"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM projects WHERE path = ?", (project_path,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        # Get active tasks
        active_tasks = self.get_project_tasks(project_path, TaskStatus.RUNNING)
        
        return ProjectState(
            path=row[0],
            name=row[1],
            active_tasks=[t.id for t in active_tasks],
            completed_tasks=row[2],
            failed_tasks=row[3],
            last_activity=row[4],
            cursor_status=row[5],
            git_branch=row[6],
            git_status=row[7]
        )
    
    def log_activity(self, event_type: str, project_path: Optional[str] = None,
                    task_id: Optional[str] = None, details: Optional[Dict] = None):
        """Log activity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO activity_log (timestamp, project_path, task_id, event_type, details)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            project_path,
            task_id,
            event_type,
            json.dumps(details) if details else None
        ))
        
        conn.commit()
        conn.close()

# ============================================================================
# CURSOR INTEGRATION
# ============================================================================

class CursorInterface:
    """Interface for Cursor AI operations"""
    
    @staticmethod
    async def execute_command(project_path: str, command: str, timeout: int = 300, task_id: str = None) -> Dict[str, Any]:
        """Execute command via Cursor - creates instruction file and optionally opens project"""
        try:
            logger.info(f"Executing Cursor command in {project_path}: {command}")
            project = Path(project_path)
            
            # Mode: instruction - create task file for user to execute manually in Cursor
            if Config.CURSOR_MODE == "instruction":
                # Create .cursor-tasks directory
                tasks_dir = project / ".cursor-tasks"
                tasks_dir.mkdir(exist_ok=True)
                
                # Generate task file
                task_file = tasks_dir / f"task_{task_id or datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                task_content = f"""# Cursor Task: {task_id or 'New Task'}

**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Project:** {project_path}

## Task Instructions

{command}

## Next Steps

1. Review the task instructions above
2. Use Cursor's AI features (Cmd+K or Cmd+L) to implement
3. Test your changes
4. When complete, mark this task as done in the orchestrator

---
*This task was created by Claude-Cursor Orchestrator*
"""
                task_file.write_text(task_content)
                logger.info(f"Created task file: {task_file}")
                
                # Open project in Cursor if configured
                if Config.AUTO_OPEN_CURSOR and Config.CURSOR_CLI:
                    try:
                        process = await asyncio.create_subprocess_exec(
                            Config.CURSOR_CLI,
                            str(project),
                            str(task_file),
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        await asyncio.wait_for(process.communicate(), timeout=10)
                        logger.info(f"Opened project in Cursor: {project}")
                    except Exception as e:
                        logger.warning(f"Could not auto-open Cursor: {e}")
                
                return {
                    "success": True,
                    "mode": "instruction",
                    "task_file": str(task_file),
                    "message": f"Task file created: {task_file.name}. Project opened in Cursor."
                }
            
            # Mode: mock - simulate execution for testing
            elif Config.CURSOR_MODE == "mock":
                logger.info(f"[MOCK] Simulating task execution: {command[:100]}...")
                await asyncio.sleep(2)  # Simulate processing time
                return {
                    "success": True,
                    "mode": "mock",
                    "message": "Task simulated successfully (mock mode)"
                }
            
            # Mode: auto - try to auto-execute via Cursor CLI (experimental)
            elif Config.CURSOR_MODE == "auto":
                logger.info(f"[AUTO] Attempting auto-execution: {command[:100]}...")
                
                # Create task file first
                tasks_dir = project / ".cursor-tasks"
                tasks_dir.mkdir(exist_ok=True)
                
                task_file = tasks_dir / f"task_{task_id or datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                task_content = f"""# Cursor Task: {task_id or 'New Task'}

**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Project:** {project_path}

## Task Instructions

{command}

## Auto-Execute Command

Execute this task using Cursor AI (Cmd+K):
```
Zaimplementuj to zadanie zgodnie z instrukcjami powyżej. Stwórz wszystkie potrzebne pliki i struktury.
```

---
*This task was created by Claude-Cursor Orchestrator*
"""
                task_file.write_text(task_content)
                logger.info(f"Created auto-execute task file: {task_file}")
                
                # Try to open Cursor with auto-execute hint
                if Config.AUTO_OPEN_CURSOR and Config.CURSOR_CLI:
                    try:
                        # Open Cursor with the task file
                        process = await asyncio.create_subprocess_exec(
                            Config.CURSOR_CLI,
                            str(project),
                            str(task_file),
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        await asyncio.wait_for(process.communicate(), timeout=10)
                        logger.info(f"Opened project in Cursor: {project}")
                    except Exception as e:
                        logger.warning(f"Could not auto-open Cursor: {e}")
                
                return {
                    "success": True,
                    "mode": "auto",
                    "task_file": str(task_file),
                    "message": f"Auto-execute task created: {task_file.name}. Use Cmd+K in Cursor to execute."
                }
            
            # Mode: api - bidirectional communication with Cursor AI
            elif Config.CURSOR_MODE == "api":
                logger.info(f"[API] Starting bidirectional communication: {command[:100]}...")
                
                # Create task file with API communication setup
                tasks_dir = project / ".cursor-tasks"
                tasks_dir.mkdir(exist_ok=True)
                
                task_file = tasks_dir / f"task_{task_id or datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                
                # Create API communication file
                api_file = tasks_dir / f"api_{task_id or datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                task_content = f"""# Cursor Task: {task_id or 'New Task'}

**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Project:** {project_path}
**Mode:** API Communication

## Task Instructions

{command}

## API Communication

This task uses bidirectional communication with Claude Desktop.

**Communication File:** `{api_file.name}`

### How it works:
1. Claude Desktop sends task via orchestrator
2. Cursor AI executes the task
3. Cursor AI reports progress to `{api_file.name}`
4. Orchestrator monitors progress and reports back to Claude Desktop

### Execute Command:
```bash
# Cursor AI should execute this task and update the API file
# with progress: {{"status": "in_progress", "progress": 50, "message": "Creating files..."}}
# completion: {{"status": "completed", "result": "Task completed successfully"}}
```

---
*This task was created by Claude-Cursor Orchestrator with API communication*
"""
                task_file.write_text(task_content)
                
                # Initialize API communication file
                api_data = {
                    "task_id": task_id,
                    "status": "pending",
                    "progress": 0,
                    "message": "Task created, waiting for Cursor AI execution",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "command": command,
                    "project_path": project_path
                }
                api_file.write_text(json.dumps(api_data, indent=2))
                
                logger.info(f"Created API communication files: {task_file.name}, {api_file.name}")
                
                # Try to open Cursor with API mode
                if Config.AUTO_OPEN_CURSOR and Config.CURSOR_CLI:
                    try:
                        process = await asyncio.create_subprocess_exec(
                            Config.CURSOR_CLI,
                            str(project),
                            str(task_file),
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        await asyncio.wait_for(process.communicate(), timeout=10)
                        logger.info(f"Opened project in Cursor with API mode: {project}")
                    except Exception as e:
                        logger.warning(f"Could not auto-open Cursor: {e}")
                
                # Start watching this project for API updates
                api_monitor.watch_project(project_path)
                
                return {
                    "success": True,
                    "mode": "api",
                    "task_file": str(task_file),
                    "api_file": str(api_file),
                    "message": f"API communication established. Task: {task_file.name}, API: {api_file.name}. Monitoring for updates..."
                }
            
            # Unsupported mode
            else:
                return {
                    "success": False,
                    "error": f"Unsupported CURSOR_MODE: {Config.CURSOR_MODE}"
                }
                
        except Exception as e:
            logger.error(f"Cursor execution error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def get_project_status(project_path: str) -> Dict[str, Any]:
        """Get current Cursor project status"""
        try:
            # Check if Cursor workspace is open
            workspace_file = Path(project_path) / ".cursor"
            if not workspace_file.exists():
                return {"status": "no_workspace", "details": "Cursor workspace not initialized"}
            
            # Get open files and errors (simplified - would need actual Cursor API)
            return {
                "status": "ready",
                "workspace_open": True,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

# ============================================================================
# GIT INTEGRATION
# ============================================================================

class GitInterface:
    """Git operations"""
    
    @staticmethod
    async def get_status(project_path: str) -> Dict[str, Any]:
        """Get Git status"""
        try:
            process = await asyncio.create_subprocess_exec(
                "git", "status", "--porcelain", "-b",
                cwd=project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                status = stdout.decode().strip()
                lines = status.split('\n')
                branch = lines[0].replace('## ', '') if lines else "unknown"
                changes = len([l for l in lines[1:] if l])
                
                return {
                    "branch": branch,
                    "has_changes": changes > 0,
                    "num_changes": changes,
                    "status": status
                }
            return {"error": stderr.decode()}
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    async def auto_commit(project_path: str, message: str) -> bool:
        """Auto-commit changes"""
        try:
            # Add all changes
            await asyncio.create_subprocess_exec(
                "git", "add", ".",
                cwd=project_path
            )
            
            # Commit
            process = await asyncio.create_subprocess_exec(
                "git", "commit", "-m", message,
                cwd=project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            return process.returncode == 0
        except Exception as e:
            logger.error(f"Git commit error: {e}")
            return False

# ============================================================================
# FILE WATCHER FOR API COMMUNICATION
# ============================================================================

class APIFileWatcher(FileSystemEventHandler):
    """Watches for changes in API communication files"""
    
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.last_modified = {}
        
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
            
        if not event.src_path.endswith('.json'):
            return
            
        if 'api_' not in event.src_path:
            return
            
        # Debounce - ignore rapid consecutive modifications
        now = datetime.now().timestamp()
        if event.src_path in self.last_modified:
            if now - self.last_modified[event.src_path] < 1.0:
                return
        
        self.last_modified[event.src_path] = now
        
        # Trigger callback in thread-safe way
        try:
            loop = asyncio.get_running_loop()
            loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self.callback(event.src_path))
            )
        except RuntimeError:
            # No event loop running, try to schedule for later
            try:
                asyncio.run(self.callback(event.src_path))
            except Exception as e:
                logger.error(f"Failed to handle API file update: {e}")

class APIFileMonitor:
    """Monitors API communication files across all projects"""
    
    def __init__(self):
        self.observers = {}
        self.subscribers = []  # Callbacks for notifications
        
    async def handle_api_update(self, file_path: str):
        """Handle API file update"""
        try:
            logger.info(f"🔔 API file updated: {file_path}")
            
            # Read updated API data
            api_data = json.loads(Path(file_path).read_text())
            
            task_id = api_data.get('task_id')
            status = api_data.get('status')
            progress = api_data.get('progress', 0)
            message = api_data.get('message', '')
            
            # Update task in database
            task = state_manager.get_task(task_id)
            if task:
                # Update task status based on API status
                if status == 'in_progress':
                    task.status = TaskStatus.RUNNING
                elif status == 'completed':
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.now().isoformat()
                    task.result = api_data.get('result', 'Task completed')
                elif status == 'failed':
                    task.status = TaskStatus.FAILED
                    task.error = api_data.get('error', 'Unknown error')
                    
                state_manager.save_task(task)
                
                logger.info(f"✅ Task {task_id} updated: {status} ({progress}%) - {message}")
                
                # Notify subscribers
                notification = {
                    'type': 'task_update',
                    'task_id': task_id,
                    'status': status,
                    'progress': progress,
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                }
                
                for subscriber in self.subscribers:
                    try:
                        await subscriber(notification)
                    except Exception as e:
                        logger.error(f"Subscriber notification failed: {e}")
                        
        except Exception as e:
            logger.error(f"Error handling API update: {e}")
    
    def watch_project(self, project_path: str):
        """Start watching a project's .cursor-tasks directory"""
        tasks_dir = Path(project_path) / ".cursor-tasks"
        
        if not tasks_dir.exists():
            tasks_dir.mkdir(parents=True, exist_ok=True)
            
        if str(tasks_dir) in self.observers:
            return  # Already watching
            
        try:
            observer = Observer()
            handler = APIFileWatcher(self.handle_api_update)
            observer.schedule(handler, str(tasks_dir), recursive=False)
            observer.start()
            
            self.observers[str(tasks_dir)] = observer
            logger.info(f"👁️  Watching API files in: {tasks_dir}")
            
        except Exception as e:
            logger.error(f"Failed to start watching {tasks_dir}: {e}")
    
    def stop_watching(self, project_path: str):
        """Stop watching a project"""
        tasks_dir = str(Path(project_path) / ".cursor-tasks")
        
        if tasks_dir in self.observers:
            self.observers[tasks_dir].stop()
            self.observers[tasks_dir].join()
            del self.observers[tasks_dir]
            logger.info(f"Stopped watching: {tasks_dir}")
    
    def stop_all(self):
        """Stop all observers"""
        for observer in self.observers.values():
            observer.stop()
            observer.join()
        self.observers.clear()
        logger.info("Stopped all file watchers")
    
    def subscribe(self, callback):
        """Subscribe to API notifications"""
        self.subscribers.append(callback)

# Global API monitor
api_monitor = APIFileMonitor()

# ============================================================================
# TASK EXECUTOR
# ============================================================================

class TaskExecutor:
    """Executes and manages tasks"""
    
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
    
    async def submit_task(self, task: Task):
        """Submit task for execution"""
        self.state_manager.save_task(task)
        self.state_manager.log_activity(
            "task_submitted",
            project_path=task.project_path,
            task_id=task.id,
            details={"description": task.description}
        )
        await self.task_queue.put(task)
        logger.info(f"Task {task.id} submitted to queue")
    
    async def execute_task(self, task: Task):
        """Execute a single task"""
        try:
            # Update task status
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now().isoformat()
            self.state_manager.save_task(task)
            self.state_manager.update_project_state(
                task.project_path,
                cursor_status="busy"
            )
            
            logger.info(f"Executing task {task.id}: {task.description}")
            
            # Execute via Cursor
            result = await CursorInterface.execute_command(
                task.project_path,
                task.command,
                timeout=Config.TASK_TIMEOUT,
                task_id=task.id
            )
            
            # Update task with result
            task.completed_at = datetime.now().isoformat()
            
            if result["success"]:
                task.status = TaskStatus.COMPLETED
                # Store result (can be message, task_file path, or actual result)
                task.result = json.dumps(result.get("message") or result.get("result") or "Success")
                self.state_manager.update_project_state(
                    task.project_path,
                    completed_tasks=sqlite3.connect(Config.DB_PATH).execute(
                        "SELECT completed_tasks FROM projects WHERE path = ?",
                        (task.project_path,)
                    ).fetchone()[0] + 1
                )
                logger.info(f"Task {task.id} completed successfully: {result.get('message', '')}")
                
                # Auto-commit if enabled and mode is not instruction (user commits manually)
                if Config.GIT_AUTO_COMMIT and Config.CURSOR_MODE != "instruction":
                    await GitInterface.auto_commit(
                        task.project_path,
                        f"Auto-commit: {task.description}"
                    )
            else:
                task.status = TaskStatus.FAILED
                task.error = result.get("error", "Unknown error")
                self.state_manager.update_project_state(
                    task.project_path,
                    failed_tasks=sqlite3.connect(Config.DB_PATH).execute(
                        "SELECT failed_tasks FROM projects WHERE path = ?",
                        (task.project_path,)
                    ).fetchone()[0] + 1
                )
                logger.error(f"Task {task.id} failed: {task.error}")
            
            self.state_manager.save_task(task)
            self.state_manager.log_activity(
                "task_completed" if task.status == TaskStatus.COMPLETED else "task_failed",
                project_path=task.project_path,
                task_id=task.id,
                details={"status": task.status.value}
            )
            
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now().isoformat()
            self.state_manager.save_task(task)
        finally:
            # Update project status
            self.state_manager.update_project_state(
                task.project_path,
                cursor_status="idle"
            )
            # Remove from running tasks
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]
    
    async def process_queue(self):
        """Process task queue"""
        while True:
            # Wait for task
            task = await self.task_queue.get()
            
            # Check if we can run more tasks
            while len(self.running_tasks) >= Config.MAX_CONCURRENT_TASKS:
                await asyncio.sleep(1)
            
            # Execute task
            task_coro = asyncio.create_task(self.execute_task(task))
            self.running_tasks[task.id] = task_coro
            
            self.task_queue.task_done()

# ============================================================================
# MCP SERVER
# ============================================================================

# Initialize components
state_manager = StateManager(Config.DB_PATH)
task_executor = TaskExecutor(state_manager)

# Create MCP server
mcp = FastMCP("Claude-Cursor Advanced Orchestrator")

# Background task handle
_background_task: Optional[asyncio.Task] = None

def _ensure_background_task():
    """Ensure background task processor is running"""
    global _background_task
    if _background_task is None or _background_task.done():
        try:
            loop = asyncio.get_running_loop()
            _background_task = loop.create_task(task_executor.process_queue())
            logger.info("Background task processor started")
        except RuntimeError:
            # No event loop running yet - will be started on first tool call
            logger.warning("No event loop yet - background task will start on first tool call")

# ============================================================================
# MCP TOOLS
# ============================================================================

@mcp.tool()
async def execute_cursor_task(
    project_path: str,
    description: str,
    command: str,
    priority: str = "medium",
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Submit a task for Cursor AI to execute.
    
    Args:
        project_path: Absolute path to project directory
        description: Human-readable description of the task
        command: The command/prompt for Cursor to execute
        priority: Task priority (low, medium, high, critical)
        context: Additional context for the task
    
    Returns:
        Task information including task_id for tracking
    """
    # Ensure background task processor is running
    _ensure_background_task()
    
    # Validate project path
    if not Config.validate_project_path(project_path):
        return {
            "error": "Invalid project path",
            "message": f"Project path '{project_path}' is not allowed or does not exist. Check Config.ALLOWED_PROJECT_PATHS"
        }
    
    # Create task
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    task = Task(
        id=task_id,
        project_path=project_path,
        description=description,
        command=command,
        status=TaskStatus.PENDING,
        priority=TaskPriority[priority.upper()],
        created_at=datetime.now().isoformat(),
        context=context
    )
    
    # Submit task
    await task_executor.submit_task(task)
    
    return {
        "task_id": task_id,
        "status": "submitted",
        "message": f"Task submitted successfully. Track progress with task_id: {task_id}"
    }

@mcp.tool()
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get the current status of a task.
    
    Args:
        task_id: The task ID to check
    
    Returns:
        Complete task information including status, result, and errors
    """
    task = state_manager.get_task(task_id)
    
    if not task:
        return {"error": f"Task {task_id} not found"}
    
    return task.to_dict()

@mcp.tool()
async def get_project_status(project_path: str) -> Dict[str, Any]:
    """
    Get comprehensive status of a project including Cursor and Git state.
    
    Args:
        project_path: Project directory path
    
    Returns:
        Project state, active tasks, Git status, and Cursor status
    """
    # Validate project path
    if not Config.validate_project_path(project_path):
        return {
            "error": "Invalid project path",
            "message": f"Project path '{project_path}' is not allowed or does not exist"
        }
    
    # Get project state from DB
    project_state = state_manager.get_project_state(project_path)
    
    # Get live Cursor status
    cursor_status = await CursorInterface.get_project_status(project_path)
    
    # Get Git status
    git_status = await GitInterface.get_status(project_path)
    
    # Get active tasks
    active_tasks = state_manager.get_project_tasks(project_path, TaskStatus.RUNNING)
    pending_tasks = state_manager.get_project_tasks(project_path, TaskStatus.PENDING)
    
    return {
        "project": asdict(project_state) if project_state else None,
        "cursor": cursor_status,
        "git": git_status,
        "tasks": {
            "active": [t.to_dict() for t in active_tasks],
            "pending": [t.to_dict() for t in pending_tasks],
            "active_count": len(active_tasks),
            "pending_count": len(pending_tasks)
        }
    }

@mcp.tool()
async def list_project_tasks(
    project_path: str,
    status: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    List tasks for a project with optional filtering.
    
    Args:
        project_path: Project directory path
        status: Optional status filter (pending, running, completed, failed, cancelled)
        limit: Maximum number of tasks to return
    
    Returns:
        List of tasks matching the criteria
    """
    status_filter = TaskStatus(status) if status else None
    tasks = state_manager.get_project_tasks(project_path, status_filter)
    
    return {
        "tasks": [t.to_dict() for t in tasks[:limit]],
        "total": len(tasks),
        "returned": min(len(tasks), limit)
    }

@mcp.tool()
async def cancel_task(task_id: str) -> Dict[str, Any]:
    """
    Cancel a pending or running task.
    
    Args:
        task_id: The task ID to cancel
    
    Returns:
        Cancellation status
    """
    task = state_manager.get_task(task_id)
    
    if not task:
        return {"error": f"Task {task_id} not found"}
    
    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        return {"error": f"Task {task_id} is already {task.status.value}"}
    
    # Cancel running task
    if task.id in task_executor.running_tasks:
        task_executor.running_tasks[task.id].cancel()
    
    # Update task status
    task.status = TaskStatus.CANCELLED
    task.completed_at = datetime.now().isoformat()
    state_manager.save_task(task)
    
    state_manager.log_activity(
        "task_cancelled",
        project_path=task.project_path,
        task_id=task_id
    )
    
    return {
        "task_id": task_id,
        "status": "cancelled",
        "message": "Task cancelled successfully"
    }

@mcp.tool()
async def retry_task(
    task_id: str,
    max_retries: int = 3,
    retry_delay: int = 5
) -> Dict[str, Any]:
    """
    Retry a failed task with exponential backoff.
    
    Args:
        task_id: The task ID to retry
        max_retries: Maximum number of retry attempts
        retry_delay: Base delay between retries in seconds
    
    Returns:
        New task information or error
    """
    # Ensure background task processor is running
    _ensure_background_task()
    
    # Get original task
    original_task = state_manager.get_task(task_id)
    
    if not original_task:
        return {"error": f"Task {task_id} not found"}
    
    if original_task.status != TaskStatus.FAILED:
        return {
            "error": "Task is not in FAILED state",
            "message": f"Task status is {original_task.status.value}. Only FAILED tasks can be retried."
        }
    
    # Validate project path
    if not Config.validate_project_path(original_task.project_path):
        return {
            "error": "Invalid project path",
            "message": "Original task's project path is no longer allowed"
        }
    
    # Create new task with retry context
    new_task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_retry"
    
    retry_context = original_task.context.copy() if original_task.context else {}
    retry_context["retry_of"] = task_id
    retry_context["retry_attempt"] = retry_context.get("retry_attempt", 0) + 1
    retry_context["max_retries"] = max_retries
    retry_context["original_error"] = original_task.error
    
    # Check if max retries exceeded
    if retry_context["retry_attempt"] > max_retries:
        return {
            "error": "Max retries exceeded",
            "message": f"Task has already been retried {retry_context['retry_attempt']-1} times. Max retries: {max_retries}"
        }
    
    new_task = Task(
        id=new_task_id,
        project_path=original_task.project_path,
        description=f"[RETRY {retry_context['retry_attempt']}/{max_retries}] {original_task.description}",
        command=original_task.command,
        status=TaskStatus.PENDING,
        priority=original_task.priority,
        created_at=datetime.now().isoformat(),
        context=retry_context
    )
    
    # Submit retry task
    await task_executor.submit_task(new_task)
    
    # Log activity
    state_manager.log_activity(
        "task_retried",
        project_path=original_task.project_path,
        task_id=new_task_id,
        details={
            "original_task_id": task_id,
            "retry_attempt": retry_context["retry_attempt"],
            "max_retries": max_retries
        }
    )
    
    logger.info(f"Retrying task {task_id} as {new_task_id} (attempt {retry_context['retry_attempt']}/{max_retries})")
    
    return {
        "new_task_id": new_task_id,
        "original_task_id": task_id,
        "retry_attempt": retry_context["retry_attempt"],
        "max_retries": max_retries,
        "status": "retry_submitted",
        "message": f"Task retry submitted successfully. Track with task_id: {new_task_id}"
    }

@mcp.tool()
async def create_cursor_rules(
    project_path: str,
    rules: List[str],
    append: bool = True
) -> Dict[str, Any]:
    """
    Create or update .cursorrules file for the project.
    
    Args:
        project_path: Project directory path
        rules: List of rules to add
        append: If True, append to existing rules; if False, replace
    
    Returns:
        Status of rules creation
    """
    try:
        rules_file = Path(project_path) / ".cursorrules"
        
        mode = "a" if append and rules_file.exists() else "w"
        
        with open(rules_file, mode) as f:
            f.write("\n".join(rules) + "\n")
        
        state_manager.log_activity(
            "rules_updated",
            project_path=project_path,
            details={"num_rules": len(rules), "append": append}
        )
        
        return {
            "success": True,
            "rules_file": str(rules_file),
            "num_rules": len(rules),
            "mode": "appended" if append else "replaced"
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def save_task_template(
    name: str,
    description: str,
    command: str,
    priority: str = "medium",
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Save a task as a reusable template.
    
    Args:
        name: Unique name for the template
        description: Template description
        command: Command/prompt template
        priority: Default priority (low, medium, high, critical)
        tags: Optional tags for organization
    
    Returns:
        Template information
    """
    try:
        template_id = f"template_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        now = datetime.now().isoformat()
        tags_str = json.dumps(tags) if tags else None
        
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO task_templates (id, name, description, command, priority, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (template_id, name, description, command, priority, tags_str, now, now))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Template '{name}' saved with ID {template_id}")
        
        return {
            "template_id": template_id,
            "name": name,
            "status": "saved",
            "message": f"Template '{name}' saved successfully"
        }
    except sqlite3.IntegrityError:
        return {
            "error": "Template name already exists",
            "message": f"A template with name '{name}' already exists. Use a different name or delete the existing one."
        }
    except Exception as e:
        logger.error(f"Error saving template: {e}")
        return {"error": str(e)}

@mcp.tool()
async def list_task_templates(tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    List all saved task templates.
    
    Args:
        tags: Optional filter by tags
    
    Returns:
        List of templates
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        
        if tags:
            # Filter by tags (simple contains check)
            cursor.execute("SELECT * FROM task_templates ORDER BY use_count DESC, name")
            rows = cursor.fetchall()
            # Filter in Python (simple approach)
            filtered_rows = []
            for row in rows:
                if row[5]:  # tags column
                    template_tags = json.loads(row[5])
                    if any(tag in template_tags for tag in tags):
                        filtered_rows.append(row)
            rows = filtered_rows
        else:
            cursor.execute("SELECT * FROM task_templates ORDER BY use_count DESC, name")
            rows = cursor.fetchall()
        
        conn.close()
        
        templates = [
            {
                "id": r[0],
                "name": r[1],
                "description": r[2],
                "command": r[3],
                "priority": r[4],
                "tags": json.loads(r[5]) if r[5] else [],
                "created_at": r[6],
                "updated_at": r[7],
                "use_count": r[8]
            }
            for r in rows
        ]
        
        return {
            "templates": templates,
            "count": len(templates)
        }
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        return {"error": str(e)}

@mcp.tool()
async def create_task_from_template(
    template_name: str,
    project_path: str,
    variables: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create a new task from a saved template.
    
    Args:
        template_name: Name of the template to use
        project_path: Project path for the new task
        variables: Optional variables to replace in command (e.g., {"feature_name": "dark_mode"})
    
    Returns:
        New task information
    """
    # Ensure background task processor is running
    _ensure_background_task()
    
    # Validate project path
    if not Config.validate_project_path(project_path):
        return {
            "error": "Invalid project path",
            "message": f"Project path '{project_path}' is not allowed or does not exist"
        }
    
    try:
        # Get template
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM task_templates WHERE name = ?", (template_name,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return {"error": f"Template '{template_name}' not found"}
        
        template_id, name, description, command, priority, tags, created_at, updated_at, use_count = row
        
        # Update use count
        cursor.execute("UPDATE task_templates SET use_count = use_count + 1 WHERE id = ?", (template_id,))
        conn.commit()
        conn.close()
        
        # Apply variables to command if provided
        if variables:
            for var_name, var_value in variables.items():
                command = command.replace(f"{{{var_name}}}", var_value)
                description = description.replace(f"{{{var_name}}}", var_value)
        
        # Create task
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_from_template"
        
        task = Task(
            id=task_id,
            project_path=project_path,
            description=description,
            command=command,
            status=TaskStatus.PENDING,
            priority=TaskPriority[priority.upper()],
            created_at=datetime.now().isoformat(),
            context={"template_id": template_id, "template_name": template_name}
        )
        
        # Submit task
        await task_executor.submit_task(task)
        
        logger.info(f"Task created from template '{template_name}': {task_id}")
        
        return {
            "task_id": task_id,
            "template_name": template_name,
            "status": "submitted",
            "message": f"Task created from template '{template_name}'. Track with task_id: {task_id}"
        }
        
    except Exception as e:
        logger.error(f"Error creating task from template: {e}")
        return {"error": str(e)}

@mcp.tool()
async def delete_task_template(template_name: str) -> Dict[str, Any]:
    """
    Delete a task template.
    
    Args:
        template_name: Name of the template to delete
    
    Returns:
        Deletion status
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM task_templates WHERE name = ?", (template_name,))
        deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if deleted > 0:
            logger.info(f"Template '{template_name}' deleted")
            return {
                "status": "deleted",
                "message": f"Template '{template_name}' deleted successfully"
            }
        else:
            return {
                "error": "Template not found",
                "message": f"No template with name '{template_name}' found"
            }
    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        return {"error": str(e)}

@mcp.tool()
async def get_activity_log(
    project_path: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Retrieve activity log with optional filtering.
    
    Args:
        project_path: Optional project path filter
        event_type: Optional event type filter
        limit: Maximum number of entries to return
    
    Returns:
        Activity log entries
    """
    conn = sqlite3.connect(Config.DB_PATH)
    cursor = conn.cursor()
    
    query = "SELECT * FROM activity_log WHERE 1=1"
    params = []
    
    if project_path:
        query += " AND project_path = ?"
        params.append(project_path)
    
    if event_type:
        query += " AND event_type = ?"
        params.append(event_type)
    
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return {
        "entries": [
            {
                "id": r[0],
                "timestamp": r[1],
                "project_path": r[2],
                "task_id": r[3],
                "event_type": r[4],
                "details": json.loads(r[5]) if r[5] else None
            }
            for r in rows
        ],
        "count": len(rows)
    }

@mcp.tool()
async def monitor_api_communication(task_id: str) -> Dict[str, Any]:
    """
    Monitor API communication between Claude Desktop and Cursor AI.
    
    Args:
        task_id: Task ID to monitor
        
    Returns:
        Current API communication status and progress
    """
    try:
        # Find API file for this task
        api_files = list(Path.home().glob(f".claude-cursor-orchestrator/api_*{task_id}*.json"))
        if not api_files:
            return {"error": f"No API communication file found for task {task_id}"}
        
        api_file = api_files[0]
        
        # Read API data
        api_data = json.loads(api_file.read_text())
        
        # Check if Cursor AI has updated the file recently
        file_mtime = datetime.fromtimestamp(api_file.stat().st_mtime)
        time_diff = (datetime.now() - file_mtime).total_seconds()
        
        return {
            "task_id": task_id,
            "api_file": str(api_file),
            "status": api_data.get("status", "unknown"),
            "progress": api_data.get("progress", 0),
            "message": api_data.get("message", ""),
            "last_update": api_data.get("updated_at", ""),
            "file_age_seconds": time_diff,
            "is_active": time_diff < 60,  # Active if updated within last minute
            "full_data": api_data
        }
        
    except Exception as e:
        logger.error(f"Error monitoring API communication: {e}")
        return {"error": str(e)}

@mcp.tool()
async def start_watching_project(project_path: str) -> Dict[str, Any]:
    """
    Start monitoring API communication files for a project.
    
    Args:
        project_path: Project directory path
        
    Returns:
        Confirmation that watching has started
    """
    try:
        api_monitor.watch_project(project_path)
        return {
            "success": True,
            "message": f"Started monitoring API files in {project_path}/.cursor-tasks/",
            "watching": list(api_monitor.observers.keys())
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def stop_watching_project(project_path: str) -> Dict[str, Any]:
    """
    Stop monitoring API communication files for a project.
    
    Args:
        project_path: Project directory path
        
    Returns:
        Confirmation that watching has stopped
    """
    try:
        api_monitor.stop_watching(project_path)
        return {
            "success": True,
            "message": f"Stopped monitoring {project_path}",
            "watching": list(api_monitor.observers.keys())
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def get_watching_status() -> Dict[str, Any]:
    """
    Get list of projects currently being monitored.
    
    Returns:
        List of projects with active file watchers
    """
    return {
        "watching_projects": list(api_monitor.observers.keys()),
        "count": len(api_monitor.observers),
        "subscribers": len(api_monitor.subscribers)
    }

@mcp.tool()
async def get_system_stats() -> Dict[str, Any]:
    """
    Get overall system statistics and health.
    
    Returns:
        System-wide statistics
    """
    conn = sqlite3.connect(Config.DB_PATH)
    cursor = conn.cursor()
    
    # Count tasks by status
    cursor.execute("""
        SELECT status, COUNT(*) FROM tasks GROUP BY status
    """)
    task_stats = dict(cursor.fetchall())
    
    # Count projects
    cursor.execute("SELECT COUNT(*) FROM projects")
    total_projects = cursor.fetchone()[0]
    
    # Recent activity
    cursor.execute("""
        SELECT event_type, COUNT(*) FROM activity_log
        WHERE timestamp > datetime('now', '-1 hour')
        GROUP BY event_type
    """)
    recent_activity = dict(cursor.fetchall())
    
    conn.close()
    
    return {
        "tasks": {
            "total": sum(task_stats.values()),
            "by_status": task_stats,
            "running": len(task_executor.running_tasks),
            "queue_size": task_executor.task_queue.qsize()
        },
        "projects": {
            "total": total_projects
        },
        "recent_activity": recent_activity,
        "config": {
            "max_concurrent_tasks": Config.MAX_CONCURRENT_TASKS,
            "task_timeout": Config.TASK_TIMEOUT,
            "git_auto_commit": Config.GIT_AUTO_COMMIT
        }
    }

# ============================================================================
# MCP RESOURCES
# ============================================================================

@mcp.resource("orchestrator://projects")
async def list_all_projects() -> str:
    """List all managed projects"""
    conn = sqlite3.connect(Config.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects ORDER BY last_activity DESC")
    projects = cursor.fetchall()
    conn.close()
    
    result = "# Managed Projects\n\n"
    for p in projects:
        result += f"## {p[1]} ({p[0]})\n"
        result += f"- Status: {p[5]}\n"
        result += f"- Completed: {p[2]}, Failed: {p[3]}\n"
        result += f"- Last Activity: {p[4]}\n"
        result += f"- Git Branch: {p[6] or 'N/A'}\n\n"
    
    return result

@mcp.resource("orchestrator://live-updates")
async def get_live_updates() -> str:
    """
    Get live updates stream (SSE-compatible format).
    Returns recent notifications from API file watcher.
    """
    # Get recent activity log
    conn = sqlite3.connect(Config.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM activity_log 
        WHERE action IN ('task_completed', 'task_failed', 'task_started')
        ORDER BY timestamp DESC 
        LIMIT 50
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    updates = []
    for row in rows:
        updates.append({
            "id": row[0],
            "timestamp": row[1],
            "action": row[2],
            "project_path": row[3],
            "task_id": row[4],
            "details": json.loads(row[5]) if row[5] else None
        })
    
    output = "# Live Updates Stream\n\n"
    output += f"**Total Updates:** {len(updates)}\n\n"
    
    for update in updates[:20]:
        output += f"## {update['action'].upper()}\n"
        output += f"- **Time:** {update['timestamp']}\n"
        output += f"- **Task:** {update['task_id']}\n"
        output += f"- **Project:** {update['project_path']}\n"
        if update['details']:
            output += f"- **Details:** {json.dumps(update['details'], indent=2)}\n"
        output += "\n"
    
    return output

@mcp.resource("orchestrator://metrics")
async def get_realtime_metrics() -> str:
    """Get real-time performance metrics"""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        
        # Task statistics
        cursor.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
        status_counts = dict(cursor.fetchall())
        
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'completed'")
        total_completed = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'failed'")
        total_failed = cursor.fetchone()[0]
        
        # Success rate
        total_finished = total_completed + total_failed
        success_rate = (total_completed / total_finished * 100) if total_finished > 0 else 0
        
        # Average completion time (for completed tasks)
        cursor.execute("""
            SELECT AVG(
                (julianday(completed_at) - julianday(started_at)) * 24 * 60 * 60
            ) FROM tasks 
            WHERE status = 'completed' AND started_at IS NOT NULL AND completed_at IS NOT NULL
        """)
        avg_time_result = cursor.fetchone()[0]
        avg_completion_time = avg_time_result if avg_time_result else 0
        
        # Tasks by priority
        cursor.execute("SELECT priority, COUNT(*) FROM tasks GROUP BY priority")
        priority_counts = dict(cursor.fetchall())
        
        # Recent activity (last hour)
        cursor.execute("""
            SELECT event_type, COUNT(*) FROM activity_log
            WHERE timestamp > datetime('now', '-1 hour')
            GROUP BY event_type
        """)
        recent_activity = dict(cursor.fetchall())
        
        # Top projects by task count
        cursor.execute("""
            SELECT project_path, COUNT(*) as task_count
            FROM tasks
            GROUP BY project_path
            ORDER BY task_count DESC
            LIMIT 5
        """)
        top_projects = cursor.fetchall()
        
        # Template usage
        cursor.execute("SELECT COUNT(*), SUM(use_count) FROM task_templates")
        template_stats = cursor.fetchone()
        template_count = template_stats[0] if template_stats else 0
        template_uses = template_stats[1] if template_stats and template_stats[1] else 0
        
        # Queue size
        queue_size = task_executor.task_queue.qsize()
        running_count = len(task_executor.running_tasks)
        
        conn.close()
        
        # Format as markdown
        result = "# 📊 Real-Time Metrics\n\n"
        result += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        result += "## 🎯 Task Statistics\n\n"
        result += f"- **Success Rate**: {success_rate:.1f}%\n"
        result += f"- **Avg Completion Time**: {avg_completion_time:.1f}s\n"
        result += f"- **Completed**: {total_completed}\n"
        result += f"- **Failed**: {total_failed}\n"
        result += f"- **Currently Running**: {running_count}\n"
        result += f"- **In Queue**: {queue_size}\n\n"
        
        result += "## 📈 Status Breakdown\n\n"
        for status, count in status_counts.items():
            result += f"- {status}: {count}\n"
        result += "\n"
        
        result += "## ⭐ Priority Distribution\n\n"
        priority_names = {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "CRITICAL"}
        for priority, count in sorted(priority_counts.items()):
            result += f"- {priority_names.get(priority, priority)}: {count}\n"
        result += "\n"
        
        result += "## 🔥 Top Projects\n\n"
        for project_path, count in top_projects:
            project_name = Path(project_path).name
            result += f"- **{project_name}**: {count} tasks\n"
        result += "\n"
        
        result += "## 📝 Template Usage\n\n"
        result += f"- **Templates**: {template_count}\n"
        result += f"- **Total Uses**: {template_uses}\n"
        result += f"- **Avg Uses per Template**: {(template_uses / template_count):.1f}\n" if template_count > 0 else "- **Avg Uses per Template**: 0\n"
        result += "\n"
        
        result += "## ⚡ Recent Activity (Last Hour)\n\n"
        if recent_activity:
            for event, count in sorted(recent_activity.items(), key=lambda x: x[1], reverse=True):
                result += f"- {event}: {count}\n"
        else:
            result += "- No recent activity\n"
        result += "\n"
        
        result += "## ⚙️ System Config\n\n"
        result += f"- **Max Concurrent Tasks**: {Config.MAX_CONCURRENT_TASKS}\n"
        result += f"- **Task Timeout**: {Config.TASK_TIMEOUT}s\n"
        result += f"- **Git Auto-Commit**: {Config.GIT_AUTO_COMMIT}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return f"# ❌ Error\n\nFailed to generate metrics: {e}"

@mcp.resource("orchestrator://logs")
async def get_recent_logs() -> str:
    """Get recent system logs"""
    try:
        with open(Config.LOG_PATH, 'r') as f:
            lines = f.readlines()
            return ''.join(lines[-100:])  # Last 100 lines
    except Exception as e:
        return f"Error reading logs: {e}"

# ============================================================================
# MCP PROMPTS
# ============================================================================

@mcp.prompt()
def orchestration_workflow_prompt(project_name: str, goal: str) -> str:
    """Generate a comprehensive orchestration workflow prompt"""
    return f"""# Orchestration Workflow for {project_name}

Goal: {goal}

## Recommended Approach:

1. **Initial Assessment**
   - Use get_project_status() to understand current state
   - Check Git status and active tasks
   - Review any pending/failed tasks

2. **Task Planning**
   - Break down the goal into specific, actionable tasks
   - Assign appropriate priorities (critical for dependencies)
   - Consider task dependencies and ordering

3. **Execution Strategy**
   - Submit tasks using execute_cursor_task()
   - Monitor progress with get_task_status()
   - Handle failures gracefully with retries if needed

4. **Quality Assurance**
   - Review Cursor output for each completed task
   - Create .cursorrules for coding standards
   - Use Git commits to track progress

5. **Monitoring**
   - Check get_system_stats() for overall health
   - Use get_activity_log() to review recent actions
   - Adjust concurrent task limits if needed

## Best Practices:
- Start with high-priority foundational tasks
- Allow Cursor time to complete complex operations
- Use context parameter to pass relevant information
- Monitor for errors and adjust strategy accordingly
"""

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
