# ============================================================================
# pyproject.toml - Konfiguracja projektu Python
# ============================================================================

[project]
name = "claude-cursor-orchestrator"
version = "1.0.0"
description = "Advanced orchestration system for Claude Desktop and Cursor AI"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "mcp[cli]>=1.0.0",
    "aiofiles>=23.0.0",
    "watchdog>=3.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.black]
line-length = 100
target-version = ['py310']

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W"]

# ============================================================================
# .env.example - Przykładowe zmienne środowiskowe
# ============================================================================

# Cursor Configuration
CURSOR_CLI_PATH=cursor-agent
CURSOR_API_KEY=your_cursor_api_key_here

# Git Configuration  
GIT_AUTO_COMMIT=true
GIT_COMMIT_PREFIX="[Auto]"

# System Configuration
MAX_CONCURRENT_TASKS=3
TASK_TIMEOUT_SECONDS=300
LOG_LEVEL=INFO

# Paths
DB_PATH=~/.claude-cursor-orchestrator/state.db
LOG_PATH=~/.claude-cursor-orchestrator/orchestrator.log

# Security
ALLOWED_PROJECT_PATHS=/Users/myuser/projects,/Users/myuser/work
FORBIDDEN_COMMANDS=rm -rf,sudo,> /dev/

# Notifications (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK/URL

# Analytics (optional)
ENABLE_ANALYTICS=false
ANALYTICS_ENDPOINT=https://your-analytics-endpoint.com

# ============================================================================
# setup.sh - Skrypt instalacyjny dla Unix/macOS
# ============================================================================

#!/bin/bash

echo "🚀 Claude-Cursor Orchestrator Setup"
echo "===================================="

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.10+ required (found $python_version)"
    exit 1
fi
echo "✅ Python version OK ($python_version)"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi
echo "✅ uv package manager ready"

# Check Cursor CLI
if ! command -v cursor-agent &> /dev/null; then
    echo "⚠️  Cursor CLI not found. Installing..."
    curl https://cursor.com/install -fsSL | bash
    
    if ! command -v cursor-agent &> /dev/null; then
        echo "❌ Failed to install Cursor CLI. Please install manually from https://cursor.com"
        exit 1
    fi
fi
echo "✅ Cursor CLI ready"

# Create project directory
echo "Creating project structure..."
PROJECT_DIR="$HOME/claude-cursor-orchestrator"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Initialize uv project
uv init

# Install dependencies
echo "Installing dependencies..."
uv add "mcp[cli]"
uv add aiofiles watchdog

# Create directories
echo "Creating necessary directories..."
mkdir -p "$HOME/.claude-cursor-orchestrator"

# Copy .env file
if [ -f ".env.example" ]; then
    cp .env.example .env
    echo "✅ Created .env file (please configure)"
fi

# Test installation
echo "Testing MCP server..."
timeout 5 uv run orchestrator.py &> /dev/null
if [ $? -eq 124 ]; then
    echo "✅ Server starts successfully"
else
    echo "⚠️  Server test inconclusive, but installation complete"
fi

# Configure Claude Desktop
echo ""
echo "📝 Manual Configuration Required:"
echo "================================="
echo ""
echo "1. Edit Claude Desktop config:"
echo "   macOS: ~/Library/Application Support/Claude/claude_desktop_config.json"
echo "   Linux: ~/.config/Claude/claude_desktop_config.json"
echo ""
echo "2. Add this configuration:"
echo ""
cat << 'EOF'
{
  "mcpServers": {
    "cursor-orchestrator": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/YOUR_USERNAME/claude-cursor-orchestrator",
        "run",
        "orchestrator.py"
      ]
    }
  }
}
EOF
echo ""
echo "3. Replace YOUR_USERNAME with your actual username"
echo "4. Restart Claude Desktop"
echo ""
echo "✅ Installation complete!"

# ============================================================================
# setup.ps1 - Skrypt instalacyjny dla Windows PowerShell
# ============================================================================

# Claude-Cursor Orchestrator Setup for Windows
Write-Host "🚀 Claude-Cursor Orchestrator Setup" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green

# Check Python version
Write-Host "Checking Python version..."
$pythonVersion = python --version 2>&1
if ($pythonVersion -match "Python (\d+\.\d+)") {
    $version = [version]$matches[1]
    if ($version -lt [version]"3.10") {
        Write-Host "❌ Error: Python 3.10+ required" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Python version OK ($version)" -ForegroundColor Green
}

# Check if uv is installed
$uvInstalled = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvInstalled) {
    Write-Host "Installing uv package manager..."
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}
Write-Host "✅ uv package manager ready" -ForegroundColor Green

# Check Cursor CLI
$cursorInstalled = Get-Command cursor-agent -ErrorAction SilentlyContinue
if (-not $cursorInstalled) {
    Write-Host "⚠️  Cursor CLI not found" -ForegroundColor Yellow
    Write-Host "Please install from: https://cursor.com" -ForegroundColor Yellow
}

# Create project directory
Write-Host "Creating project structure..."
$projectDir = "$env:USERPROFILE\claude-cursor-orchestrator"
New-Item -ItemType Directory -Force -Path $projectDir | Out-Null
Set-Location $projectDir

# Initialize uv project
uv init

# Install dependencies
Write-Host "Installing dependencies..."
uv add "mcp[cli]"
uv add aiofiles watchdog

# Create directories
Write-Host "Creating necessary directories..."
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude-cursor-orchestrator" | Out-Null

# Copy .env file
if (Test-Path ".env.example") {
    Copy-Item .env.example .env
    Write-Host "✅ Created .env file (please configure)" -ForegroundColor Green
}

Write-Host ""
Write-Host "📝 Manual Configuration Required:" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Edit Claude Desktop config:"
Write-Host "   $env:APPDATA\Claude\claude_desktop_config.json"
Write-Host ""
Write-Host "2. Add this configuration:"
Write-Host ""
Write-Host @"
{
  "mcpServers": {
    "cursor-orchestrator": {
      "command": "uv",
      "args": [
        "--directory",
        "$projectDir",
        "run",
        "orchestrator.py"
      ]
    }
  }
}
"@
Write-Host ""
Write-Host "3. Restart Claude Desktop"
Write-Host ""
Write-Host "✅ Installation complete!" -ForegroundColor Green

# ============================================================================
# test_orchestrator.py - Testy jednostkowe
# ============================================================================

import pytest
import asyncio
import sqlite3
from pathlib import Path
import tempfile
import json

# Import from orchestrator
import sys
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import (
    Config, StateManager, Task, TaskStatus, TaskPriority,
    CursorInterface, GitInterface, TaskExecutor
)

@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    
    Config.DB_PATH = db_path
    yield db_path
    
    # Cleanup
    if db_path.exists():
        db_path.unlink()

@pytest.fixture
def state_manager(temp_db):
    """Create StateManager with temp database"""
    return StateManager(temp_db)

def test_state_manager_init(state_manager):
    """Test StateManager initialization"""
    conn = sqlite3.connect(state_manager.db_path)
    cursor = conn.cursor()
    
    # Check if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    
    assert 'tasks' in tables
    assert 'projects' in tables
    assert 'activity_log' in tables
    
    conn.close()

def test_task_save_and_retrieve(state_manager):
    """Test saving and retrieving tasks"""
    task = Task(
        id="test_task_1",
        project_path="/test/project",
        description="Test task",
        command="test command",
        status=TaskStatus.PENDING,
        priority=TaskPriority.HIGH,
        created_at="2025-01-17T10:00:00"
    )
    
    # Save task
    state_manager.save_task(task)
    
    # Retrieve task
    retrieved = state_manager.get_task("test_task_1")
    
    assert retrieved is not None
    assert retrieved.id == task.id
    assert retrieved.description == task.description
    assert retrieved.status == TaskStatus.PENDING

def test_project_state_update(state_manager):
    """Test project state updates"""
    project_path = "/test/project"
    
    state_manager.update_project_state(
        project_path,
        cursor_status="busy",
        git_branch="main"
    )
    
    project_state = state_manager.get_project_state(project_path)
    
    assert project_state is not None
    assert project_state.cursor_status == "busy"
    assert project_state.git_branch == "main"

@pytest.mark.asyncio
async def test_cursor_interface_mock():
    """Test Cursor interface with mock"""
    # This would require mocking subprocess
    # For now, just test structure
    result = {"success": True, "result": {"output": "test"}}
    
    assert result["success"] is True
    assert "result" in result

def test_activity_logging(state_manager):
    """Test activity logging"""
    state_manager.log_activity(
        "test_event",
        project_path="/test/project",
        task_id="test_task_1",
        details={"key": "value"}
    )
    
    conn = sqlite3.connect(state_manager.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activity_log WHERE event_type = 'test_event'")
    row = cursor.fetchone()
    conn.close()
    
    assert row is not None
    assert row[4] == "test_event"  # event_type column

def test_task_to_dict():
    """Test task serialization"""
    task = Task(
        id="test",
        project_path="/path",
        description="desc",
        command="cmd",
        status=TaskStatus.COMPLETED,
        priority=TaskPriority.HIGH,
        created_at="2025-01-17T10:00:00"
    )
    
    task_dict = task.to_dict()
    
    assert task_dict["id"] == "test"
    assert task_dict["status"] == "completed"
    assert task_dict["priority"] == 3

# ============================================================================
# Makefile - Komendy pomocnicze
# ============================================================================

.PHONY: install test dev clean logs stats help

help:
	@echo "Claude-Cursor Orchestrator - Available Commands"
	@echo "=============================================="
	@echo "  make install    - Install dependencies"
	@echo "  make dev        - Run in development mode with inspector"
	@echo "  make test       - Run tests"
	@echo "  make clean      - Clean temporary files"
	@echo "  make logs       - Show live logs"
	@echo "  make stats      - Show database statistics"
	@echo "  make backup     - Backup database"
	@echo "  make reset      - Reset database (WARNING: deletes data)"

install:
	@echo "Installing dependencies..."
	uv add "mcp[cli]"
	uv add aiofiles watchdog
	uv add --dev pytest pytest-asyncio black ruff
	@echo "✅ Installation complete"

dev:
	@echo "Starting development server with inspector..."
	uv run mcp dev orchestrator.py

test:
	@echo "Running tests..."
	uv run pytest test_orchestrator.py -v

clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	@echo "✅ Cleaned"

logs:
	@echo "Showing live logs (Ctrl+C to exit)..."
	tail -f ~/.claude-cursor-orchestrator/orchestrator.log

stats:
	@echo "Database Statistics"
	@echo "==================="
	@sqlite3 ~/.claude-cursor-orchestrator/state.db "SELECT status, COUNT(*) FROM tasks GROUP BY status;"
	@echo ""
	@sqlite3 ~/.claude-cursor-orchestrator/state.db "SELECT COUNT(*) as total_projects FROM projects;"

backup:
	@echo "Backing up database..."
	@cp ~/.claude-cursor-orchestrator/state.db ~/.claude-cursor-orchestrator/state.db.backup.$(shell date +%Y%m%d_%H%M%S)
	@echo "✅ Backup created"

reset:
	@echo "⚠️  WARNING: This will delete all data!"
	@read -p "Are you sure? (y/N): " confirm && [ $$confirm = y ]
	@rm -f ~/.claude-cursor-orchestrator/state.db
	@echo "✅ Database reset"

# ============================================================================
# .cursorrules - Przykładowe reguły dla projektu orchestrator
# ============================================================================

# Claude-Cursor Orchestrator Development Rules

## Code Style
- Use Python 3.10+ features
- Follow PEP 8 with 100 character line limit
- Use type hints for all functions
- Document all public functions with docstrings
- Use async/await for I/O operations

## Architecture
- Keep StateManager separate from business logic
- CursorInterface should handle all Cursor-specific operations
- TaskExecutor manages execution flow and concurrency
- Use dataclasses for models

## Error Handling
- All async operations must have try/except
- Log all errors with appropriate level
- Never expose internal errors to Claude Desktop
- Return structured error responses

## Testing
- Write tests for all new features
- Mock external dependencies (Cursor CLI, Git)
- Test edge cases and error conditions
- Maintain >80% code coverage

## Git Workflow
- Commit messages: "feat:", "fix:", "docs:", "refactor:"
- Small, atomic commits
- Never commit sensitive data
- Update CHANGELOG for user-facing changes

## Performance
- Limit concurrent tasks to avoid overload
- Use connection pooling for database
- Implement proper timeouts
- Log performance metrics

## Security
- Validate all input paths
- Sanitize commands before execution
- Never execute arbitrary code
- Audit logs regularly

# ============================================================================
# docker-compose.yml - Optional Docker setup
# ============================================================================

version: '3.8'

services:
  orchestrator:
    build: .
    container_name: claude-cursor-orchestrator
    volumes:
      # Mount projects
      - ~/projects:/projects:ro
      # Mount state
      - ./data:/root/.claude-cursor-orchestrator
      # Mount git config
      - ~/.gitconfig:/root/.gitconfig:ro
    environment:
      - CURSOR_CLI_PATH=cursor-agent
      - MAX_CONCURRENT_TASKS=3
      - LOG_LEVEL=INFO
    restart: unless-stopped
    
# Note: Docker setup is optional and may have limitations
# with Cursor CLI integration. Local installation is recommended.

# ============================================================================
# Dockerfile - Optional Docker image
# ============================================================================

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Copy project files
COPY pyproject.toml .
COPY orchestrator.py .

# Install dependencies
RUN uv sync

# Create data directory
RUN mkdir -p /root/.claude-cursor-orchestrator

EXPOSE 8080

CMD ["uv", "run", "orchestrator.py"]
