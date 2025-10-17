# 🤖 Cursor AI - API Communication Guide

## Jak komunikować się z Claude Desktop przez Orchestrator

### 📁 Pliki komunikacji

Gdy otrzymujesz zadanie w trybie API, znajdziesz:

1. **`task_xxx.md`** - instrukcje zadania
2. **`api_xxx.json`** - plik komunikacji z Claude Desktop

### 🔄 Workflow komunikacji

#### 1. **Otrzymujesz zadanie**
```json
{
  "task_id": "task_20251017_143000",
  "status": "pending",
  "progress": 0,
  "message": "Task created, waiting for Cursor AI execution",
  "command": "Stwórz schemat Prisma...",
  "project_path": "/Users/mariusz/amgsquant"
}
```

#### 2. **Rozpocznij pracę**
Zaktualizuj plik `api_xxx.json`:
```json
{
  "task_id": "task_20251017_143000",
  "status": "in_progress",
  "progress": 25,
  "message": "Creating Prisma schema file...",
  "updated_at": "2025-10-17T14:30:15"
}
```

#### 3. **Raportuj postęp**
```json
{
  "status": "in_progress",
  "progress": 50,
  "message": "Adding User model with relationships..."
}
```

#### 4. **Zakończ zadanie**
```json
{
  "status": "completed",
  "progress": 100,
  "message": "Prisma schema created successfully",
  "result": "Created schema.prisma with User model, UserRole enum, and relationships",
  "files_created": ["packages/database/schema.prisma"],
  "updated_at": "2025-10-17T14:30:45"
}
```

### 🛠️ Przykład implementacji w Cursor

**W Cursor AI (Cmd+K):**

```
Przeczytaj plik api_xxx.json i wykonaj zadanie zgodnie z instrukcjami. 
Po każdym kroku aktualizuj plik api_xxx.json z postępem:

1. Ustaw status: "in_progress", progress: 25
2. Wykonaj zadanie
3. Aktualizuj postęp: progress: 50, 75, 100
4. Na końcu ustaw status: "completed" z wynikiem

Używaj tego formatu:
{
  "status": "in_progress|completed|failed",
  "progress": 0-100,
  "message": "Opis co robisz",
  "result": "Wynik zadania (tylko przy completed)",
  "files_created": ["lista", "plików"],
  "updated_at": "ISO timestamp"
}
```

### 📊 Statusy

- **`pending`** - Zadanie oczekuje na wykonanie
- **`in_progress`** - Zadanie w trakcie wykonywania  
- **`completed`** - Zadanie zakończone pomyślnie
- **`failed`** - Zadanie zakończone błędem

### 🔍 Monitoring

Claude Desktop może monitorować postęp przez:
- `monitor_api_communication(task_id)` - sprawdza status
- `get_task_status(task_id)` - ogólny status zadania

### ⚡ Automatyzacja

Możesz stworzyć skrypt który:
1. Czyta `api_xxx.json`
2. Wykonuje zadanie
3. Aktualizuje postęp automatycznie

```bash
#!/bin/bash
# auto-execute.sh
API_FILE="api_xxx.json"

# Update status to in_progress
jq '.status = "in_progress" | .progress = 25' "$API_FILE" > tmp && mv tmp "$API_FILE"

# Execute task
# ... your code here ...

# Update to completed
jq '.status = "completed" | .progress = 100 | .result = "Task completed"' "$API_FILE" > tmp && mv tmp "$API_FILE"
```

---

**🎯 Cel:** Pełna automatyzacja komunikacji między Claude Desktop a Cursor AI bez udziału użytkownika!
