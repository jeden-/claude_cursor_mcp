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
    CURSOR_CLI = "cursor-agent"
    GIT_AUTO_COMMIT = True
    
    @classmethod
    def ensure_dirs(cls):
        """Create necessary directories"""
        cls.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

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
    async def execute_command(project_path: str, command: str, timeout: int = 300) -> Dict[str, Any]:
        """Execute command via Cursor CLI"""
        try:
            logger.info(f"Executing Cursor command in {project_path}: {command}")
            
            process = await asyncio.create_subprocess_exec(
                Config.CURSOR_CLI,
                "-p", command,
                "--output-format", "json",
                cwd=project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            if process.returncode == 0:
                result = json.loads(stdout.decode())
                return {"success": True, "result": result}
            else:
                error = stderr.decode()
                logger.error(f"Cursor command failed: {error}")
                return {"success": False, "error": error}
                
        except asyncio.TimeoutError:
            logger.error(f"Cursor command timed out after {timeout}s")
            return {"success": False, "error": "Command timed out"}
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
                timeout=Config.TASK_TIMEOUT
            )
            
            # Update task with result
            task.completed_at = datetime.now().isoformat()
            
            if result["success"]:
                task.status = TaskStatus.COMPLETED
                task.result = json.dumps(result["result"])
                self.state_manager.update_project_state(
                    task.project_path,
                    completed_tasks=sqlite3.connect(Config.DB_PATH).execute(
                        "SELECT completed_tasks FROM projects WHERE path = ?",
                        (task.project_path,)
                    ).fetchone()[0] + 1
                )
                logger.info(f"Task {task.id} completed successfully")
                
                # Auto-commit if enabled
                if Config.GIT_AUTO_COMMIT:
                    await GitInterface.auto_commit(
                        task.project_path,
                        f"Auto-commit: {task.description}"
                    )
            else:
                task.status = TaskStatus.FAILED
                task.error = result["error"]
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

# Task processor will be started when server runs
@mcp.resource("orchestrator://start")
async def _start_background_tasks() -> str:
    """Start background tasks when server initializes"""
    asyncio.create_task(task_executor.process_queue())
    return "Background tasks started"

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
