# 🚀 Przewodnik Pełnej Automatyzacji

## 🤖 Claude Desktop ↔ Cursor AI - Bez Twojego udziału!

---

## 📋 **Spis treści**

1. [Szybki start](#szybki-start)
2. [Jak to działa](#jak-to-działa)
3. [Tryby pracy](#tryby-pracy)
4. [Przykłady użycia](#przykłady-użycia)
5. [Monitorowanie](#monitorowanie)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 **Szybki start**

### **Krok 1: Zrestartuj Claude Desktop**

```bash
# Zamknij Claude Desktop i otwórz ponownie
# Lub na macOS:
killall "Claude" && open -a "Claude"
```

### **Krok 2: Stwórz zadanie w Claude Desktop**

```
Execute task in /Users/mariusz/amgsquant:
- Stwórz API endpoint GET /api/users
- Dodaj kontroler w NestJS
- Dodaj testy jednostkowe
```

### **Krok 3: Uruchom Auto-Executor (w osobnym terminalu)**

```bash
cd /Users/mariusz/claude_cursor_mcp
python3 cursor_auto_executor.py /Users/mariusz/amgsquant
```

### **Krok 4: Otwórz Dashboard**

```bash
open dashboard.html
```

### **Krok 5: Obserwuj magię! ✨**

Claude Desktop automatycznie otrzyma aktualizacje o postępie zadania!

---

## 🔄 **Jak to działa**

### **Architektura systemu:**

```
┌─────────────────┐
│ Claude Desktop  │
│                 │
│ "Execute task"  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Orchestrator   │
│  (MCP Server)   │
│                 │
│  • Creates task │
│  • Creates API  │
│  • Starts       │
│    watching     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ .cursor-tasks/  │
│                 │
│ • task_xxx.md   │
│ • api_xxx.json  │
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌──────────────┐   ┌──────────────┐
│ File Watcher │   │Auto-Executor │
│              │   │              │
│ Monitors     │   │ Executes     │
│ changes      │   │ tasks        │
└──────┬───────┘   └──────┬───────┘
       │                  │
       │                  ▼
       │          Updates API file
       │          (progress 10-100%)
       │                  │
       └──────────────────┘
                │
                ▼
       Detects change
                │
                ▼
       ┌────────────────┐
       │  Orchestrator  │
       │  Updates DB    │
       │  Notifies      │
       └────────┬───────┘
                │
                ▼
       ┌────────────────┐
       │ Claude Desktop │
       │ Gets update!   │
       └────────────────┘
```

---

## 🎛️ **Tryby pracy**

### **1. API Mode (domyślny) - Pełna automatyzacja**

```python
CURSOR_MODE = "api"
```

- Tworzy pliki `task_xxx.md` + `api_xxx.json`
- File Watcher automatycznie monitoruje
- Auto-Executor automatycznie wykonuje
- Claude Desktop dostaje live updates

**Użyj gdy:** chcesz pełną automatyzację bez Twojego udziału

### **2. Instruction Mode - Manualne wykonanie**

```python
CURSOR_MODE = "instruction"
```

- Tworzy tylko `task_xxx.md`
- Musisz użyć Cmd+K/Cmd+L w Cursor
- Musisz ręcznie zaktualizować status

**Użyj gdy:** chcesz mieć pełną kontrolę

### **3. Auto Mode - Semi-automatyczne**

```python
CURSOR_MODE = "auto"
```

- Tworzy `task_xxx.md` z hintami
- Sugeruje użycie Cmd+K
- Częściowa automatyzacja

**Użyj gdy:** chcesz balans między kontrolą a automatyzacją

---

## 💡 **Przykłady użycia**

### **Przykład 1: Tworzenie API**

**W Claude Desktop:**
```
Execute task in /Users/mariusz/ecommerce:
Stwórz REST API dla produktów:
- GET /api/products - lista produktów
- GET /api/products/:id - szczegóły produktu
- POST /api/products - dodaj produkt
- PUT /api/products/:id - aktualizuj produkt
- DELETE /api/products/:id - usuń produkt

Użyj NestJS + Prisma + TypeScript
```

**W terminalu:**
```bash
python3 cursor_auto_executor.py /Users/mariusz/ecommerce
```

**Wynik:**
- Auto-Executor tworzy wszystkie pliki
- Aktualizuje API file z postępem
- Claude Desktop widzi: "Creating controllers... 50%"
- Po zakończeniu: "Completed! All endpoints created"

### **Przykład 2: Refaktoryzacja kodu**

**W Claude Desktop:**
```
Execute task in /Users/mariusz/legacy-app:
Zrefaktoryzuj stary kod:
- Zamień var na const/let
- Dodaj TypeScript types
- Wydziel funkcje pomocnicze
- Dodaj testy jednostkowe
```

**Monitorowanie w Claude:**
```
monitor_api_communication(task_20251017_150000_123456)

→ Status: in_progress (30%)
→ Message: "Refactoring variables..."
```

### **Przykład 3: Tworzenie całego projektu**

**W Claude Desktop:**
```
Execute task in /Users/mariusz/new-project:
Stwórz pełny projekt Next.js 14:
- App Router
- Tailwind CSS
- Prisma ORM
- NextAuth.js
- Folder structure
- Landing page
- Dashboard
```

**Dashboard pokazuje:**
```
📊 Progress: ████████░░ 75%
💬 "Creating dashboard components..."
⏱️  Estimated: 2 min remaining
```

---

## 📊 **Monitorowanie**

### **1. W Claude Desktop**

```
# Sprawdź status zadania
get_task_status("task_20251017_150000_123456")

# Monitoruj API
monitor_api_communication("task_20251017_150000_123456")

# Lista monitorowanych projektów
get_watching_status()

# Live updates
orchestrator://live-updates
```

### **2. W Dashboard (dashboard.html)**

- **Total Tasks:** Wszystkie zadania
- **✅ Completed:** Zakończone pomyślnie
- **⚡ Running:** W trakcie wykonywania
- **❌ Failed:** Niepowodzenia
- **👁️ Watching:** Monitorowane projekty
- **📊 Success Rate:** % sukcesu

### **3. W terminalu (Auto-Executor)**

```
🔔 NEW TASK DETECTED: task_20251017_150000_123456
📝 Task ID: task_20251017_150000_123456
📁 Project: /Users/mariusz/amgsquant
🔧 Command: Stwórz API endpoint...

✅ Updated API file: in_progress (30%) - Creating files...
✅ Updated API file: in_progress (60%) - Implementing...
✅ Updated API file: completed (100%) - Success!
```

---

## 🔧 **Narzędzia CLI**

### **Auto-Executor**

```bash
# Uruchom dla projektu
python3 cursor_auto_executor.py /path/to/project

# Automatycznie:
# - Wykrywa nowe taski
# - Wykonuje je
# - Aktualizuje API files
# - Ctrl+C aby zatrzymać
```

### **Monitoring File Watcher**

```python
# W Claude Desktop lub przez MCP

# Start monitoring
start_watching_project("/Users/mariusz/amgsquant")

# Stop monitoring  
stop_watching_project("/Users/mariusz/amgsquant")

# Check status
get_watching_status()
```

---

## 🐛 **Troubleshooting**

### **Problem: File Watcher nie działa**

**Rozwiązanie:**
```bash
# Sprawdź czy watchdog jest zainstalowany
pip install watchdog

# Zrestartuj orchestrator
# W Claude Desktop - zamknij i otwórz ponownie
```

### **Problem: Auto-Executor nie wykrywa tasków**

**Rozwiązanie:**
```bash
# Sprawdź czy folder .cursor-tasks/ istnieje
ls -la /path/to/project/.cursor-tasks/

# Sprawdź czy są pliki API
ls -la /path/to/project/.cursor-tasks/api_*.json

# Upewnij się że tryb to "api"
# W cursor_orchestrator_advanced.py:
# CURSOR_MODE = "api"
```

### **Problem: Claude Desktop nie dostaje aktualizacji**

**Rozwiązanie:**
```bash
# Sprawdź logi
tail -f ~/.claude-cursor-orchestrator/orchestrator.log

# Sprawdź czy File Watcher jest aktywny
# W Claude Desktop:
get_watching_status()

# Powinno pokazać monitorowane projekty
```

### **Problem: Task się zawiesza**

**Rozwiązanie:**
```python
# W Claude Desktop:

# 1. Sprawdź status
get_task_status("task_id")

# 2. Sprawdź API
monitor_api_communication("task_id")

# 3. Anuluj jeśli trzeba
cancel_task("task_id")

# 4. Spróbuj ponownie
retry_task("task_id")
```

---

## 🎊 **Gratulacje!**

Masz teraz **w pełni automatyczny system** komunikacji między Claude Desktop a Cursor AI!

### **Co możesz teraz robić:**

✅ Wysyłać zadania z Claude Desktop  
✅ Auto-Executor wykonuje je automatycznie  
✅ File Watcher monitoruje postęp  
✅ Claude Desktop dostaje live updates  
✅ Dashboard pokazuje wszystko w czasie rzeczywistym  
✅ **Zero interakcji z Twojej strony!** 🤖

---

## 📚 **Więcej informacji:**

- **README.md** - Pełna dokumentacja
- **CURSOR_AI_API_GUIDE.md** - Przewodnik dla Cursor AI
- **orchestrator_setup_guide.md** - Setup guide
- **GitHub:** https://github.com/jeden-/claude_cursor_mcp

---

**🚀 Miłego automatyzowania!**

