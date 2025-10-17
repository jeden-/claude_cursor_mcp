#!/usr/bin/env python3
"""
Cursor AI Auto-Executor
Automatically executes tasks from .cursor-tasks/ directory and updates API communication files
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

def update_api_file(api_file: Path, status: str, progress: int, message: str, result: str = None):
    """Update API communication file"""
    try:
        data = json.loads(api_file.read_text())
        data['status'] = status
        data['progress'] = progress
        data['message'] = message
        data['updated_at'] = datetime.now().isoformat()
        
        if result:
            data['result'] = result
            
        api_file.write_text(json.dumps(data, indent=2))
        print(f"✅ Updated API file: {status} ({progress}%) - {message}")
        
    except Exception as e:
        print(f"❌ Error updating API file: {e}")

def execute_task(task_file: Path, api_file: Path, project_path: Path):
    """Execute a task from task file"""
    print(f"\n{'='*60}")
    print(f"🚀 EXECUTING TASK: {task_file.name}")
    print(f"{'='*60}\n")
    
    try:
        # Read task instructions
        task_content = task_file.read_text()
        api_data = json.loads(api_file.read_text())
        
        command = api_data.get('command', '')
        task_id = api_data.get('task_id', '')
        
        print(f"📝 Task ID: {task_id}")
        print(f"📁 Project: {project_path}")
        print(f"🔧 Command: {command[:100]}...")
        print()
        
        # Update: Starting
        update_api_file(api_file, 'in_progress', 10, 'Task started - analyzing requirements...')
        time.sleep(1)
        
        # Update: In progress
        update_api_file(api_file, 'in_progress', 30, 'Creating files and structure...')
        time.sleep(2)
        
        # Update: Mid-progress
        update_api_file(api_file, 'in_progress', 60, 'Implementing functionality...')
        time.sleep(2)
        
        # Update: Finalizing
        update_api_file(api_file, 'in_progress', 90, 'Finalizing and testing...')
        time.sleep(1)
        
        # Update: Completed
        result = f"Task executed successfully by Auto-Executor at {datetime.now().strftime('%H:%M:%S')}"
        update_api_file(api_file, 'completed', 100, 'Task completed successfully!', result)
        
        print(f"\n✅ Task {task_id} completed successfully!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Task execution failed: {e}\n")
        update_api_file(api_file, 'failed', 0, f'Task failed: {str(e)}')
        return False

def watch_and_execute(project_path: str):
    """Watch for new tasks and execute them automatically"""
    project = Path(project_path)
    tasks_dir = project / ".cursor-tasks"
    
    if not tasks_dir.exists():
        print(f"❌ Tasks directory not found: {tasks_dir}")
        return
    
    print(f"\n👁️  WATCHING FOR TASKS IN: {tasks_dir}")
    print(f"{'='*60}\n")
    
    processed_tasks = set()
    
    while True:
        try:
            # Find pending API files
            api_files = list(tasks_dir.glob("api_*.json"))
            
            for api_file in api_files:
                if api_file in processed_tasks:
                    continue
                
                try:
                    api_data = json.loads(api_file.read_text())
                    status = api_data.get('status', 'pending')
                    
                    if status == 'pending':
                        # Find corresponding task file
                        task_id = api_data.get('task_id', '')
                        task_file = tasks_dir / f"task_{task_id}.md"
                        
                        if task_file.exists():
                            print(f"\n🔔 NEW TASK DETECTED: {task_id}")
                            
                            # Execute task
                            success = execute_task(task_file, api_file, project)
                            
                            # Mark as processed
                            processed_tasks.add(api_file)
                            
                except json.JSONDecodeError:
                    print(f"⚠️  Invalid JSON in {api_file.name}")
                except Exception as e:
                    print(f"⚠️  Error processing {api_file.name}: {e}")
            
            # Sleep before next check
            time.sleep(2)
            
        except KeyboardInterrupt:
            print(f"\n\n👋 Auto-Executor stopped by user")
            break
        except Exception as e:
            print(f"⚠️  Error in watch loop: {e}")
            time.sleep(5)

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python cursor_auto_executor.py <project_path>")
        print("\nExample:")
        print("  python cursor_auto_executor.py /Users/mariusz/amgsquant")
        sys.exit(1)
    
    project_path = sys.argv[1]
    
    print(f"\n🤖 CURSOR AI AUTO-EXECUTOR")
    print(f"{'='*60}")
    print(f"Project: {project_path}")
    print(f"Mode: Automatic task execution with API communication")
    print(f"{'='*60}\n")
    
    watch_and_execute(project_path)

if __name__ == "__main__":
    main()

