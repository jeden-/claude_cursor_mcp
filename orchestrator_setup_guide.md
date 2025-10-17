# Claude-Cursor Advanced Orchestrator - Kompletny Przewodnik

## 📋 Spis treści

1. [Instalacja](#instalacja)
2. [Konfiguracja](#konfiguracja)
3. [Użycie](#użycie)
4. [Przykłady workflow](#przykłady-workflow)
5. [Zaawansowane funkcje](#zaawansowane-funkcje)
6. [Troubleshooting](#troubleshooting)

---

## 🚀 Instalacja

### Wymagania wstępne

```bash
# Python 3.10+
python --version

# Cursor AI z dostępem do CLI
cursor-agent --version

# Git
git --version

# uv (package manager - zalecany)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Krok 1: Przygotowanie środowiska

```bash
# Utwórz katalog projektu
mkdir ~/claude-cursor-orchestrator
cd ~/claude-cursor-orchestrator

# Inicjalizuj projekt Python
uv init
```

### Krok 2: Instalacja zależności

```bash
# Zainstaluj MCP SDK
uv add "mcp[cli]"

# Dodatkowe zależności
uv add aiofiles watchdog
```

### Krok 3: Zapisz kod serwera

Zapisz pełny kod serwera z poprzedniego artifactu jako `orchestrator.py` w katalogu projektu.

### Krok 4: Testowanie z inspektorem

```bash
# Uruchom inspektor MCP do testowania
uv run mcp dev orchestrator.py
```

To otworzy interaktywny interfejs w przeglądarce do testowania wszystkich narzędzi.

### Krok 5: Instalacja w Claude Desktop

```bash
# Automatyczna instalacja
uv run mcp install orchestrator.py

# LUB ręczna konfiguracja - edytuj plik konfiguracyjny Claude Desktop
```

**Lokalizacja pliku konfiguracyjnego:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

**Dodaj do konfiguracji:**

```json
{
  "mcpServers": {
    "cursor-orchestrator": {
      "command": "uv",
      "args": [
        "--directory",
        "/ścieżka/do/claude-cursor-orchestrator",
        "run",
        "orchestrator.py"
      ]
    }
  }
}
```

### Krok 6: Restart Claude Desktop

Zamknij i uruchom ponownie Claude Desktop. Powinieneś zobaczyć ikonę 🔌 w interfejsie z dostępnymi narzędziami.

---

## ⚙️ Konfiguracja

### Konfiguracja podstawowa

Edytuj zmienne w klasie `Config` w `orchestrator.py`:

```python
class Config:
    # Maksymalna liczba równoczesnych zadań
    MAX_CONCURRENT_TASKS = 3
    
    # Timeout dla pojedynczego zadania (sekundy)
    TASK_TIMEOUT = 300  # 5 minut
    
    # Komenda Cursor CLI
    CURSOR_CLI = "cursor-agent"
    
    # Automatyczne commitowanie zmian
    GIT_AUTO_COMMIT = True
    
    # Ścieżki do bazy danych i logów
    DB_PATH = Path.home() / ".claude-cursor-orchestrator" / "state.db"
    LOG_PATH = Path.home() / ".claude-cursor-orchestrator" / "orchestrator.log"
```

### Konfiguracja Cursor AI

Upewnij się, że masz skonfigurowany Cursor CLI:

```bash
# Sprawdź instalację
cursor-agent --help

# Jeśli nie zainstalowany, pobierz z:
curl https://cursor.com/install -fsSL | bash
```

### Weryfikacja instalacji

Po restarcie Claude Desktop, spróbuj:

```
Czy możesz sprawdzić status systemu orkiestracji?
```

Claude powinien wywołać `get_system_stats()` i pokazać aktywne statystyki.

---

## 📖 Użycie

### Podstawowe komendy

#### 1. Sprawdzenie statusu systemu

```
Pokaż mi statystyki systemu orkiestracji.
```

#### 2. Utworzenie nowego zadania

```
Wykonaj zadanie w projekcie /Users/myuser/projects/myapp:
- Opis: Dodaj walidację email do formularza rejestracji
- Komenda: Zaimplementuj walidację email używając regex w pliku auth/register.tsx
- Priorytet: high
```

#### 3. Sprawdzenie statusu zadania

```
Sprawdź status zadania task_20250117_143022_123456
```

#### 4. Monitorowanie projektu

```
Jaki jest status projektu /Users/myuser/projects/myapp?
```

#### 5. Lista zadań projektu

```
Pokaż wszystkie zadania dla projektu /Users/myuser/projects/myapp
```

---

## 🎯 Przykłady Workflow

### Workflow 1: Nowy feature od podstaw

```
Rozpocznij pracę nad nowym feature'em w projekcie /Users/dev/ecommerce-app:

1. Cel: Zaimplementuj system recenzji produktów
2. Stack: React, TypeScript, Node.js, PostgreSQL

Proszę:
- Ocenić aktualny stan projektu
- Zaproponować plan implementacji
- Podzielić na zadania z priorytetami
- Wykonać zadania po kolei przez Cursor
- Monitorować postęp i commitować zmiany
```

**Claude automatycznie:**
1. Sprawdzi status projektu (`get_project_status`)
2. Zaproponuje podział na zadania
3. Utworzy zadania z odpowiednimi priorytetami:
   - CRITICAL: Setup bazy danych (migrations)
   - HIGH: Backend API endpoints
   - MEDIUM: Frontend components
   - LOW: Styling i polish
4. Wyśle każde zadanie do Cursor (`execute_cursor_task`)
5. Będzie monitorował postęp
6. Auto-commituje zmiany przez Git

### Workflow 2: Debugging i naprawa błędów

```
W projekcie /Users/dev/myapp mamy błąd w produkcji:
- Error: "TypeError: Cannot read property 'map' of undefined"
- Lokalizacja: components/ProductList.tsx
- Priorytet: CRITICAL

Proszę:
1. Przeanalizować kod w tej lokalizacji
2. Zidentyfikować przyczynę błędu
3. Zaproponować rozwiązanie
4. Naprawić przez Cursor
5. Dodać testy zapobiegające regresji
```

### Workflow 3: Refaktoring architektoniczny

```
Chcę zrefaktorować projekt /Users/dev/legacy-app:

Cel: Migracja z JavaScript do TypeScript

Plan:
- Ocenić zakres prac
- Migrować plik po pliku, rozpoczynając od utils
- Zachować funkcjonalność (wszystkie testy muszą przejść)
- Dokumentować zmiany w commitach

Rozpocznij od analizy projektu i zaproponuj strategię.
```

### Workflow 4: Multi-projekt orchestration

```
Mam 3 projekty wymagające synchronizacji:
1. /Users/dev/frontend - React app
2. /Users/dev/backend - Node.js API
3. /Users/dev/shared - Wspólne typy TypeScript

Zadanie: Dodaj nowe pole 'subscriptionTier' do User model

Proszę:
1. Zaktualizować typy w shared library
2. Zaktualizować backend (migrations, API)
3. Zaktualizować frontend (components, forms)
4. Wykonaj to w odpowiedniej kolejności z dependency tracking
```

---

## 🔧 Zaawansowane Funkcje

### 1. Tworzenie Cursor Rules

System może automatycznie generować i aktualizować `.cursorrules`:

```
Na podstawie naszych ostatnich interakcji, stwórz .cursorrules dla projektu /Users/dev/myapp z następującymi standardami:
- Używaj TypeScript strict mode
- Preferuj functional components w React
- Wszystkie funkcje muszą mieć JSDoc
- Testy są obowiązkowe dla logiki biznesowej
- Commituj małe, atomowe zmiany
```

Claude wywołuje `create_cursor_rules()` i generuje plik.

### 2. Real-time monitoring

```
Monitoruj projekt /Users/dev/critical-app w czasie rzeczywistym. 
Powiadom mnie gdy:
- Pojawią się nieprzechodzące testy
- Cursor zakończy zadanie
- Wystąpi błąd w wykonaniu
```

Claude może używać `get_activity_log()` i `get_project_status()` w pętli.

### 3. Batch operations

```
Wykonaj te zadania równolegle (max 3 concurrent):

Projekt A: Aktualizuj dependencies
Projekt B: Napraw linting errors  
Projekt C: Generuj nową dokumentację API
```

System automatycznie kolejkuje i wykonuje z limitem concurrent tasks.

### 4. Context preservation

```
Kontynuuj pracę z wczoraj nad projektem /Users/dev/webapp.
Przypomnij mi co zostało zrobione i co pozostało.
```

System używa activity log i task history do odtworzenia kontekstu.

### 5. Error recovery

```
Zadanie task_20250117_150000_999999 nie powiodło się.
Przeanalizuj błąd, zaproponuj poprawkę i spróbuj ponownie.
```

### 6. Git integration

```
Przed rozpoczęciem pracy nad nowym feature'em:
1. Sprawdź czy nie ma uncommitted changes
2. Utwórz nowy branch 'feature/user-notifications'
3. Następnie zacznij implementację
```

System używa `GitInterface` do operacji Git przed wykonaniem zadań.

---

## 🛠 Narzędzia dostępne w Claude

Po instalacji Claude Desktop ma dostęp do tych narzędzi:

### Core Tools

1. **execute_cursor_task** - Wyślij zadanie do Cursor
2. **get_task_status** - Sprawdź status zadania
3. **get_project_status** - Pełny status projektu
4. **list_project_tasks** - Lista wszystkich zadań
5. **cancel_task** - Anuluj zadanie

### Management Tools

6. **create_cursor_rules** - Generuj/aktualizuj .cursorrules
7. **get_activity_log** - Historia aktywności
8. **get_system_stats** - Statystyki całego systemu

### Resources

- **orchestrator://projects** - Lista wszystkich projektów
- **orchestrator://logs** - Logi systemowe

### Prompts

- **orchestration_workflow_prompt** - Wygeneruj workflow prompt

---

## 📊 Dashboard i monitoring

### Sprawdzanie statusu wszystkich projektów

```
Pokaż mi dashboard wszystkich moich projektów.
```

Claude użyje resource `orchestrator://projects` i wygeneruje podsumowanie.

### Analiza wydajności

```
Przeanalizuj wydajność systemu w ostatniej godzinie:
- Ile zadań zostało wykonanych?
- Jaki był średni czas wykonania?
- Czy były błędy?
```

Claude wywołuje `get_activity_log()` i `get_system_stats()`.

### Logi w czasie rzeczywistym

```
Pokaż ostatnie 50 wpisów z logów systemowych.
```

Użyje resource `orchestrator://logs`.

---

## 🐛 Troubleshooting

### Problem: Claude nie widzi narzędzi MCP

**Rozwiązanie:**
```bash
# Sprawdź czy serwer uruchamia się poprawnie
uv run orchestrator.py

# Sprawdź logi Claude Desktop
# macOS: ~/Library/Logs/Claude/
# Windows: %APPDATA%\Claude\logs\

# Zweryfikuj ścieżkę w config
cat "~/Library/Application Support/Claude/claude_desktop_config.json"
```

### Problem: Cursor CLI nie działa

**Rozwiązanie:**
```bash
# Sprawdź instalację
which cursor-agent

# Reinstaluj CLI
curl https://cursor.com/install -fsSL | bash

# Sprawdź permissions
cursor-agent --help
```

### Problem: Zadania timeout'ują

**Rozwiązanie:**
```python
# Zwiększ timeout w Config
class Config:
    TASK_TIMEOUT = 600  # 10 minut zamiast 5
```

### Problem: Zbyt wiele równoczesnych zadań

**Rozwiązanie:**
```python
# Zmniejsz limit
class Config:
    MAX_CONCURRENT_TASKS = 2  # zamiast 3
```

### Problem: Baza danych się zapełnia

**Rozwiązanie:**
```bash
# Wyczyść starą historię
sqlite3 ~/.claude-cursor-orchestrator/state.db

# W SQLite:
DELETE FROM tasks WHERE created_at < datetime('now', '-30 days');
DELETE FROM activity_log WHERE timestamp < datetime('now', '-7 days');
VACUUM;
```

### Problem: Git auto-commit nie działa

**Rozwiązanie:**
```bash
# Sprawdź git config w projekcie
cd /path/to/project
git config user.name
git config user.email

# Ustaw jeśli brak
git config user.name "Your Name"
git config user.email "your@email.com"

# Lub wyłącz auto-commit
# W orchestrator.py:
GIT_AUTO_COMMIT = False
```

---

## 🔒 Bezpieczeństwo

### Zalecenia bezpieczeństwa

1. **Ograniczenia dostępu do plików:**
```python
# Dodaj whitelist projektów
ALLOWED_PROJECTS = [
    "/Users/myuser/projects/",
    "/Users/myuser/work/"
]

# W execute_cursor_task sprawdzaj:
if not any(project_path.startswith(p) for p in ALLOWED_PROJECTS):
    raise ValueError("Project path not allowed")
```

2. **Walidacja komend:**
```python
# Blokuj niebezpieczne komendy
FORBIDDEN_PATTERNS = ["rm -rf", "sudo", "> /dev/"]

if any(pattern in command for pattern in FORBIDDEN_PATTERNS):
    raise ValueError("Command contains forbidden pattern")
```

3. **Rate limiting:**
```python
# Dodaj rate limiting dla zadań
MAX_TASKS_PER_HOUR = 50
```

4. **Audyt logów:**
```bash
# Regularnie przeglądaj logi
tail -f ~/.claude-cursor-orchestrator/orchestrator.log
```

---

## 🚀 Rozszerzenia i customizacja

### Dodanie własnego narzędzia

```python
@mcp.tool()
async def custom_deployment(project_path: str, environment: str) -> Dict[str, Any]:
    """
    Deploy project to specified environment
    """
    # Twoja logika deployment
    pass
```

### Integracja z Slack notifications

```python
import aiohttp

async def notify_slack(message: str):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    async with aiohttp.ClientSession() as session:
        await session.post(webhook_url, json={"text": message})

# Dodaj w execute_task po completion:
await notify_slack(f"Task {task.id} completed!")
```

### Custom metrics i analytics

```python
@mcp.tool()
async def get_productivity_metrics(days: int = 7) -> Dict[str, Any]:
    """Get productivity metrics for last N days"""
    # Implementacja analytics
    pass
```

---

## 📚 Przykładowe sesje

### Sesja 1: Szybkie bugfixy

```
Użytkownik: Mam 5 bugów do naprawy w /Users/dev/webapp. 
Oto lista z GitHub issues #123, #124, #125, #126, #127.

Proszę:
1. Pobierz detale każdego issue z GitHub
2. Priorytetyzuj według severity
3. Napraw je wszystkie przez Cursor
4. Commituj z referencją do issue number
5. Powiadom mnie gdy wszystkie będą gotowe

Claude: Rozumiem, zacznę od...
[Wywołuje get_project_status]
[Wywołuje execute_cursor_task dla każdego bug z odpowiednim priorytetem]
[Monitoruje postęp]
[Reportuje completion]
```

### Sesja 2: Kompleksowy refactoring

```
Użytkownik: Potrzebuję zmienić architekturę authentikacji w całej aplikacji.

Obecny stan: Session-based auth
Docelowy stan: JWT tokens

Projekty do aktualizacji:
- Backend (/Users/dev/api)  
- Frontend (/Users/dev/web)
- Mobile (/Users/dev/mobile)

Claude: To duża zmiana wymagająca koordynacji między projektami.
[Generuje orchestration_workflow_prompt]
[Analizuje każdy projekt]
[Tworzy dependency graph]
[Wykonuje zadania w odpowiedniej kolejności]
[Zapewnia consistency między projektami]
```

---

## 🎓 Najlepsze praktyki

### 1. Struktura promptów

**Dobry prompt:**
```
Zadanie: Dodaj feature X do projektu /path
Priorytet: HIGH
Kontekst: 
- Używamy TypeScript
- Mamy już podobny feature Y
- Testy są obowiązkowe
Oczekiwania:
- Kod zgodny z .cursorrules
- Pełne pokrycie testami
- Dokumentacja w README
```

**Zły prompt:**
```
Zrób coś z kodem
```

### 2. Monitoring i feedback

```
Co 10 minut podczas długiej sesji:
"Jak idzie praca nad projektem X?"
```

### 3. Error handling

```
Jeśli zadanie fail'uje:
1. Przeanalizuj error log
2. Skoryguj approach
3. Retry z adjustments
```

### 4. Git hygiene

```
Po zakończeniu feature:
"Zrób squash ostatnich 10 commitów z sensownym message"
```

### 5. Context maintenance

```
Na początku nowej sesji:
"Przypomnij mi gdzie skończyliśmy wczoraj z projektem X"
```

---

## 📞 Support i Community

### Logi i diagnostyka

```bash
# Logi serwera
tail -f ~/.claude-cursor-orchestrator/orchestrator.log

# Database inspection
sqlite3 ~/.claude-cursor-orchestrator/state.db
.tables
SELECT * FROM tasks ORDER BY created_at DESC LIMIT 10;
```

### Zgłaszanie problemów

Jeśli napotkasz problem, zbierz:
1. Wersję Python (`python --version`)
2. Wersję MCP SDK (`uv pip list | grep mcp`)
3. Relevant logs
4. Opis problemu i steps to reproduce

---

## 🔄 Aktualizacje

### Aktualizacja serwera

```bash
# Pull najnowszą wersję kodu
cd ~/claude-cursor-orchestrator
# Zaktualizuj orchestrator.py

# Restart Claude Desktop
```

### Migracja bazy danych

```bash
# Backup przed aktualizacją
cp ~/.claude-cursor-orchestrator/state.db ~/.claude-cursor-orchestrator/state.db.backup

# Po aktualizacji sprawdź schema
sqlite3 ~/.claude-cursor-orchestrator/state.db
.schema
```

---

## 🎉 Gotowe do startu!

Gratulacje! Masz teraz pełnofunkcjonalny system orkiestracji Claude-Cursor.

**Pierwszy test:**
```
W Claude Desktop napisz:
"Sprawdź status systemu orkiestracji i pokaż dostępne projekty"
```

**Pierwszy projekt:**
```
"Rozpocznij pracę nad /Users/myuser/projects/myapp:
Cel: Dodaj dark mode do aplikacji
Priorytet: MEDIUM"
```

System automatycznie:
✅ Utworzy zadanie
✅ Wyśle do Cursor
✅ Będzie monitorował postęp
✅ Zacommituje zmiany
✅ Powiadomi Cię o completion

**Miłego orkiestrowania! 🚀**
