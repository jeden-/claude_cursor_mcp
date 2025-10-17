# MTQuant Sprint 1 - Foundation & MT5 Integration

**Duration:** 7-10 dni (full-time work)  
**Goal:** Działający MT5 client z podstawową strukturą projektu i pierwszym testem połączenia z brokerem demo

---

## Sprint Overview

### Objectives
1. Setup kompletnej struktury projektu MTQuant
2. Konfiguracja środowiska Python 3.11 + dependencies
3. Implementacja MT5 MCP Client z pełnym error handling
4. Broker Adapter pattern dla MT5
5. Symbol Mapper dla mapowania nazw instrumentów
6. Pierwsze testy połączenia z MT5 demo account
7. Basic logging i monitoring setup

### Prerequisites
- Python 3.11.9 zainstalowany
- Docker zainstalowany
- Cursor AI skonfigurowany z `.cursorrules`
- Konto demo MT5 (IC Markets, Exness, lub inne)
- Git zainstalowany

---

## DAY 1 - Project Initialization

### Task 1.1: Utworzenie struktury projektu (30 min)

**Cursor AI Prompt:**
```
Create the complete MTQuant project structure following the file organization from .cursorrules:

mtquant/
├── mtquant/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── environments/
│   │   │   └── __init__.py
│   │   ├── policies/
│   │   │   └── __init__.py
│   │   ├── training/
│   │   │   └── __init__.py
│   │   └── agent_manager.py
│   ├── mcp_integration/
│   │   ├── __init__.py
│   │   ├── clients/
│   │   │   ├── __init__.py
│   │   │   └── base_client.py
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   └── base_adapter.py
│   │   ├── managers/
│   │   │   ├── __init__.py
│   │   │   ├── broker_manager.py
│   │   │   ├── connection_pool.py
│   │   │   └── symbol_mapper.py
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── order.py
│   │       └── position.py
│   ├── risk_management/
│   │   ├── __init__.py
│   │   ├── pre_trade_checker.py
│   │   ├── position_sizer.py
│   │   └── circuit_breaker.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── fetchers/
│   │   │   └── __init__.py
│   │   ├── processors/
│   │   │   └── __init__.py
│   │   └── storage/
│   │       └── __init__.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── exceptions.py
├── api/
│   ├── __init__.py
│   ├── routes/
│   │   └── __init__.py
│   ├── models/
│   │   └── __init__.py
│   └── main.py
├── config/
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   └── __init__.py
│   ├── integration/
│   │   └── __init__.py
│   └── conftest.py
├── scripts/
│   └── __init__.py
├── docker/
├── .cursorrules (already exists)
├── .gitignore (already exists)
├── requirements.txt
├── setup.py
└── README.md

For each __init__.py file:
- Add proper package initialization
- Add docstrings explaining the package purpose
- For main packages (agents, mcp_integration, risk_management), add version info

Generate README.md with:
- Project title and description
- Architecture overview
- Quick start guide (placeholder)
- Tech stack list
- License (MIT)
```

**Manual Steps:**
```powershell
# Utwórz projekt
mkdir mtquant
cd mtquant

# Inicjuj git
git init
git branch -m main

# Utwórz venv z Python 3.11
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Sprawdź wersję
python --version  # Should show: Python 3.11.9
```

**Verification:**
- [ ] Wszystkie foldery utworzone zgodnie ze strukturą
- [ ] Wszystkie `__init__.py` files istnieją
- [ ] `python --version` pokazuje 3.11.9
- [ ] Git repository zainicjowany

---

### Task 1.2: Requirements & Dependencies (30 min)

**Cursor AI Prompt:**
```
Create requirements.txt for MTQuant with the following dependencies organized by category.

Pin all versions for reproducibility. Add comments for each section.

Categories and packages:

# Core Framework
fastapi[all]==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0

# RL/ML Stack
finrl==0.3.6
stable-baselines3==2.2.1
gymnasium==0.29.1
torch==2.1.2
numpy==1.24.3
pandas==2.0.3
scikit-learn==1.3.2

# Technical Analysis
ta-lib==0.4.28

# Broker Integration
MetaTrader5==5.0.45
httpx==0.26.0
websockets==12.0
aiohttp==3.9.1

# Database Drivers
psycopg[binary,pool]==3.1.18
redis[hiredis]==5.0.1
sqlalchemy[asyncio]==2.0.25

# Utilities
loguru==0.7.2
pytz==2023.3
pyyaml==6.0.1
python-multipart==0.0.6

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
pytest-mock==3.12.0
faker==22.0.0

# Development Tools
black==24.1.1
ruff==0.1.14
mypy==1.8.0
ipython==8.19.0

# Optional: QuestDB (install separately if using time-series DB)
# questdb==1.1.0

Also create requirements-dev.txt for development-only dependencies:
- jupyter==1.0.0
- matplotlib==3.8.2
- seaborn==0.13.1
- plotly==5.18.0

Add installation notes for Windows-specific packages (TA-Lib).
```

**Manual Steps:**
```powershell
# Instaluj dependencies
pip install -r requirements.txt

# Jeśli TA-Lib failuje (typowy problem na Windows):
# 1. Pobierz .whl z: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
# 2. Dla Python 3.11 64-bit Windows: TA_Lib‑0.4.28‑cp311‑cp311‑win_amd64.whl
pip install TA_Lib-0.4.28-cp311-cp311-win_amd64.whl

# Weryfikacja instalacji kluczowych pakietów
python -c "import MetaTrader5 as mt5; print(f'MT5: {mt5.__version__}')"
python -c "import stable_baselines3; print('SB3: OK')"
python -c "import finrl; print('FinRL: OK')"
```

**Verification:**
- [ ] `requirements.txt` utworzony z wszystkimi packages
- [ ] `requirements-dev.txt` utworzony
- [ ] Wszystkie packages zainstalowane bez błędów
- [ ] TA-Lib działa (jeśli problem - manual install .whl)
- [ ] Kluczowe imports działają (MT5, SB3, FinRL)

---

### Task 1.3: Configuration Files (45 min)

**Cursor AI Prompt 1 - brokers.yaml:**
```
Create config/brokers.yaml with broker configuration structure.

Include:
1. Demo accounts section (for testing)
2. Live accounts section (placeholders, will be populated later)
3. Each broker entry should have:
   - broker_id (unique identifier)
   - platform (mt4 or mt5)
   - account (account number)
   - password (will be from .env)
   - server (broker server address)
   - description
   - is_demo (boolean)

Add configurations for:
- IC Markets MT5 Demo
- Exness MT5 Demo (placeholder)
- Generic MT4 Demo (placeholder for future)

Use YAML best practices. Add comments explaining each field.
Password should reference environment variable: ${MT5_DEMO_PASSWORD}
```

**Cursor AI Prompt 2 - symbols.yaml:**
```
Create config/symbols.yaml with symbol mapping following the SymbolMapper pattern from .cursorrules.

Structure:
1. Each standard symbol (XAUUSD, BTCUSD, USDJPY, etc.) as top-level key
2. Under each symbol, broker-specific mappings
3. Include metadata: instrument_type, pip_value, typical_spread, trading_hours

Symbols to include:
- XAUUSD (gold)
- BTCUSD (bitcoin)
- USDJPY (forex)
- EURUSD (forex)
- GBPUSD (forex)
- SPX/US500 (index)
- ETHUSD (crypto)
- WTI/USOIL (oil)

Broker mappings for each (where applicable):
- ic_markets
- oanda
- exness
- pepperstone

Use the exact format from .cursorrules SYMBOL_MAP example.
Add comments explaining the mapping purpose.
```

**Cursor AI Prompt 3 - risk-limits.yaml:**
```
Create config/risk-limits.yaml with comprehensive risk management parameters.

Sections:

1. Position Sizing Limits:
   - max_position_size_pct (10% of portfolio)
   - max_position_size_adv_pct (5% of Average Daily Volume)
   - min_position_size (minimum lot size)

2. Portfolio Limits:
   - max_total_exposure_pct (150% gross exposure)
   - max_sector_exposure_pct (40% per asset class)
   - max_correlation_threshold (0.7 - reduce if exceeded)

3. Loss Limits:
   - max_daily_loss_pct (5%)
   - max_weekly_loss_pct (10%)
   - max_drawdown_pct (20%)

4. Circuit Breaker Levels:
   - level_1_loss_pct (5% - warning)
   - level_2_loss_pct (10% - reduce positions)
   - level_3_loss_pct (15% - halt all trading)

5. Agent-Specific Limits:
   - max_trades_per_day (per agent)
   - max_holding_period_hours
   - cooldown_after_loss_minutes

6. Pre-Trade Checks:
   - price_band_pct (±10% from last known price)
   - min_account_balance (minimum margin required)
   - max_leverage (varies by instrument)

Add comments explaining each limit and its purpose.
Use conservative values appropriate for live trading.
```

**Cursor AI Prompt 4 - .env.example:**
```
Create .env.example as a template for environment variables.

Sections:

# Broker Credentials (MT5)
MT5_DEMO_ACCOUNT=YOUR_ACCOUNT_NUMBER
MT5_DEMO_PASSWORD=YOUR_PASSWORD
MT5_DEMO_SERVER=YOUR_SERVER_NAME
MT5_LIVE_ACCOUNT=YOUR_LIVE_ACCOUNT
MT5_LIVE_PASSWORD=YOUR_LIVE_PASSWORD
MT5_LIVE_SERVER=YOUR_LIVE_SERVER

# Broker Credentials (MT4)
MT4_DEMO_ACCOUNT=YOUR_ACCOUNT_NUMBER
MT4_DEMO_PASSWORD=YOUR_PASSWORD
MT4_DEMO_SERVER=YOUR_SERVER_NAME

# Database - PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=mtquant
POSTGRES_USER=mtquant_user
POSTGRES_PASSWORD=YOUR_DB_PASSWORD

# Database - QuestDB
QUESTDB_HOST=localhost
QUESTDB_HTTP_PORT=9000
QUESTDB_PG_PORT=8812
QUESTDB_PASSWORD=YOUR_QUESTDB_PASSWORD

# Database - Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=YOUR_REDIS_PASSWORD
REDIS_DB=0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=YOUR_SECRET_KEY_HERE_GENERATE_SECURE_ONE

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/mtquant.log

# Environment
ENVIRONMENT=development  # development, staging, production

Add comments for each section explaining what the variables are for.
Include instructions for generating secure API_SECRET_KEY.
```

**Manual Steps:**
```powershell
# Skopiuj .env.example do .env
cp .env.example .env

# Edytuj .env i dodaj PRAWDZIWE credentials dla MT5 demo
# Użyj Notepad++ lub VS Code
notepad .env

# Dodaj credentials swojego brokera demo:
# MT5_DEMO_ACCOUNT=twój_numer_konta
# MT5_DEMO_PASSWORD=twoje_hasło
# MT5_DEMO_SERVER=nazwa_serwera (np. "ICMarkets-Demo")
```

**Verification:**
- [ ] `config/brokers.yaml` utworzony z demo configs
- [ ] `config/symbols.yaml` utworzony z mappingami dla 8 instrumentów
- [ ] `config/risk-limits.yaml` utworzony z wszystkimi limitami
- [ ] `.env.example` utworzony jako template
- [ ] `.env` utworzony i wypełniony PRAWDZIWYMI credentials demo
- [ ] `.env` jest w `.gitignore` (nie commituj!)

---

### Task 1.4: Base Models & Exceptions (45 min)

**Cursor AI Prompt 1 - Custom Exceptions:**
```
Create mtquant/utils/exceptions.py with custom exception hierarchy for MTQuant.

Following the pattern from .cursorrules, define:

1. Base exception:
   - MTQuantError (base for all MTQuant exceptions)

2. Broker-related exceptions:
   - BrokerError (general broker error)
   - BrokerConnectionError (connection issues)
   - BrokerAPIError (API response errors)
   - BrokerTimeoutError (timeout errors)
   - OrderExecutionError (order placement failures)

3. Risk-related exceptions:
   - RiskViolationError (risk limit breaches)
   - PositionSizeError (invalid position size)
   - CircuitBreakerError (circuit breaker triggered)

4. Trading exceptions:
   - TradingError (general trading error)
   - InvalidOrderError (malformed order)
   - InsufficientMarginError (not enough margin)

5. Data exceptions:
   - DataError (data-related issues)
   - SymbolNotFoundError (symbol mapping failed)
   - MarketDataError (market data fetch failed)

Each exception should:
- Inherit from appropriate parent
- Have docstring explaining when it's raised
- Support message and optional details dict
- Include __str__ method for readable error messages

Add type hints for all methods.
```

**Cursor AI Prompt 2 - Order Model:**
```
Create mtquant/mcp_integration/models/order.py with Order dataclass.

Following .cursorrules patterns, define Order model with:

Fields:
- order_id: Optional[str] (broker order ID after execution)
- agent_id: str (which agent created this order)
- symbol: str (standard symbol like XAUUSD)
- side: Literal['buy', 'sell']
- order_type: Literal['market', 'limit', 'stop']
- quantity: float (position size in lots)
- price: Optional[float] (for limit/stop orders)
- stop_loss: Optional[float]
- take_profit: Optional[float]
- signal: float (RL model signal -1 to 1)
- created_at: datetime
- status: Literal['pending', 'filled', 'cancelled', 'rejected']
- broker_id: Optional[str] (which broker to use)

Methods:
- to_dict() -> Dict
- from_dict(data: Dict) -> Order
- validate() -> bool (check if order is valid)
- __repr__() for readable representation

Use dataclass with proper type hints.
Add validation in __post_init__ for:
- Signal range (-1 to 1)
- Quantity > 0
- Side is valid
```

**Cursor AI Prompt 3 - Position Model:**
```
Create mtquant/mcp_integration/models/position.py with Position dataclass.

Fields:
- position_id: str
- agent_id: str
- symbol: str
- side: Literal['long', 'short']
- quantity: float
- entry_price: float
- current_price: float
- stop_loss: Optional[float]
- take_profit: Optional[float]
- unrealized_pnl: float
- opened_at: datetime
- broker_id: str

Properties (calculated):
- unrealized_pnl_pct: float (percentage P&L)
- position_value: float (quantity * current_price)
- duration_hours: float (how long position is open)
- is_winning: bool (unrealized_pnl > 0)

Methods:
- update_current_price(new_price: float) -> None
- to_dict() -> Dict
- from_dict(data: Dict) -> Position
- __repr__()

Use dataclass with type hints and property decorators.
```

**Cursor AI Prompt 4 - Logger Setup:**
```
Create mtquant/utils/logger.py with centralized logging configuration using loguru.

Features:
1. Console logging (colored, formatted)
2. File logging (rotating, JSON format for production)
3. Different log levels per environment (DEBUG in dev, INFO in prod)
4. Correlation ID support (for tracing requests)
5. Sensitive data masking (passwords, API keys)

Functions:
- setup_logger(
    level: str = "INFO",
    log_file: Optional[str] = None,
    rotation: str = "100 MB",
    retention: str = "30 days"
  ) -> None

- get_logger(name: str) -> Logger

Configuration:
- Read LOG_LEVEL from environment
- Format: "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
- Serialize to JSON for file logs
- Add custom filters for masking sensitive data in logs

Include example usage in docstring.
```

**Verification:**
- [ ] `exceptions.py` utworzony z hierarchią wyjątków
- [ ] `order.py` utworzony z kompletnym Order modelem
- [ ] `position.py` utworzony z Position modelem
- [ ] `logger.py` utworzony z loguru setup
- [ ] Wszystkie pliki mają type hints i docstrings
- [ ] Import test: `from mtquant.utils.exceptions import MTQuantError`

---

### Task 1.5: First Commit (15 min)

**Manual Steps:**
```powershell
# Dodaj wszystkie pliki do git
git add .

# Sprawdź status
git status

# Pierwszy commit
git commit -m "feat: initial MTQuant project structure

- Project folder structure following .cursorrules
- Requirements.txt with pinned dependencies
- Configuration files (brokers.yaml, symbols.yaml, risk-limits.yaml)
- Base models (Order, Position) with type hints
- Custom exception hierarchy
- Logger setup with loguru
- .env.example template

Sprint 1, Day 1 complete"

# Sprawdź log
git log --oneline
```

**Verification:**
- [ ] Wszystkie pliki w staging
- [ ] Commit wykonany z opisową wiadomością
- [ ] `.env` NIE jest w commicie (sprawdź w git log)
- [ ] Git history czytelny

---

## DAY 2 - MT5 Integration Core

### Task 2.1: SymbolMapper Implementation (60 min)

**Cursor AI Prompt:**
```
Implement mtquant/mcp_integration/managers/symbol_mapper.py following the exact pattern from .cursorrules.

Requirements:

1. Load symbol mappings from config/symbols.yaml
2. Class methods (no instance needed):
   - to_broker_symbol(standard: str, broker_id: str) -> str
   - to_standard_symbol(broker_symbol: str, broker_id: str) -> str
   - get_symbol_metadata(symbol: str) -> Dict
   - validate_symbol(symbol: str) -> bool
   - get_all_standard_symbols() -> List[str]

3. Error handling:
   - Raise SymbolNotFoundError if mapping doesn't exist
   - Raise ValueError for invalid broker_id

4. Caching:
   - Load YAML once on first use
   - Cache in class variable
   - Provide reload() method for config changes

5. Type hints for all methods
6. Comprehensive docstrings
7. Unit test examples in docstring

Add logging:
- DEBUG level for successful mappings
- WARNING for missing mappings
- INFO when loading config

Include example usage showing:
- Standard to broker conversion
- Reverse lookup (broker to standard)
- Metadata retrieval
```

**Manual Test:**
```python
# Test in Python REPL
python

from mtquant.mcp_integration.managers.symbol_mapper import SymbolMapper

# Test standard to broker
broker_symbol = SymbolMapper.to_broker_symbol('XAUUSD', 'ic_markets')
print(f"IC Markets: {broker_symbol}")  # Should print: XAUUSD

# Test with Oanda (different symbol)
broker_symbol = SymbolMapper.to_broker_symbol('XAUUSD', 'oanda')
print(f"Oanda: {broker_symbol}")  # Should print: GOLD.pro

# Test reverse lookup
standard = SymbolMapper.to_standard_symbol('GOLD.pro', 'oanda')
print(f"Standard: {standard}")  # Should print: XAUUSD

# Test metadata
metadata = SymbolMapper.get_symbol_metadata('XAUUSD')
print(f"Metadata: {metadata}")
```

**Verification:**
- [ ] SymbolMapper class implemented
- [ ] Loads config/symbols.yaml correctly
- [ ] to_broker_symbol() działa dla różnych brokerów
- [ ] to_standard_symbol() reverse lookup działa
- [ ] Raises SymbolNotFoundError dla nieznanych symboli
- [ ] Manual test passes w Python REPL

---

### Task 2.2: MT5 MCP Client (90 min)

**Cursor AI Prompt:**
```
Implement mtquant/mcp_integration/clients/mt5_client.py for MetaTrader 5 integration.

Use the official MetaTrader5 Python package (already installed).

Class: MT5Client

Initialization:
- __init__(self, broker_id: str, config: Dict)
- Load broker config from config/brokers.yaml
- Initialize connection variables
- Setup logger

Core Methods:

1. Connection Management:
async def connect(self) -> bool:
    """
    Connect to MT5 terminal.
    - Initialize MT5
    - Login with credentials from .env
    - Verify connection
    - Return True if successful
    
    Raises:
        BrokerConnectionError: If connection fails
        BrokerTimeoutError: If login times out
    """

async def disconnect(self) -> None:
    """Shutdown MT5 connection cleanly."""

async def health_check(self) -> bool:
    """
    Check if connection is alive.
    - Verify terminal is running
    - Test account info retrieval
    - Return connection status
    """

2. Market Data:
async def get_symbols(self) -> List[str]:
    """Get list of available symbols from broker."""

async def get_market_data(
    self,
    symbol: str,
    timeframe: str = 'H1',
    bars: int = 100
) -> pd.DataFrame:
    """
    Fetch OHLCV data.
    
    Args:
        symbol: Broker-specific symbol (use SymbolMapper first)
        timeframe: M1, M5, M15, H1, H4, D1
        bars: Number of bars to fetch
        
    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume
        
    Raises:
        MarketDataError: If fetch fails
    """

async def get_tick_data(self, symbol: str, count: int = 10) -> pd.DataFrame:
    """Get recent tick data."""

3. Trading Operations:
async def place_order(self, order: Order) -> str:
    """
    Place order on broker.
    
    Args:
        order: Order object (already validated)
        
    Returns:
        order_id: Broker's order ticket number
        
    Raises:
        OrderExecutionError: If order fails
        InsufficientMarginError: If not enough margin
    """

async def get_positions(self) -> List[Position]:
    """Get all open positions."""

async def close_position(self, position_id: str) -> bool:
    """Close specific position."""

async def get_account_info(self) -> Dict:
    """
    Get account information.
    Returns: balance, equity, margin, free_margin, profit
    """

Implementation Notes:
- Use asyncio.to_thread() for blocking MT5 calls
- Implement retry logic (3 attempts, exponential backoff)
- Comprehensive error handling per .cursorrules
- All methods must have type hints and docstrings
- Log all operations (DEBUG level for data, INFO for trades)
- Convert MT5 timeframes (MT5_TIMEFRAME_H1, etc.)
- Map MT5 order types to our Order model

Error Handling Pattern:
try:
    result = await asyncio.to_thread(MT5.some_operation)
    if result is None:
        error_code = MT5.last_error()
        raise BrokerAPIError(f"MT5 error: {error_code}")
    return result
except TimeoutError:
    raise BrokerTimeoutError("Operation timed out")
except Exception as e:
    logger.exception("Unexpected error in MT5 operation")
    raise BrokerError(f"MT5 operation failed: {e}")

Add constants for timeframe mapping:
TIMEFRAME_MAP = {
    'M1': MT5.TIMEFRAME_M1,
    'M5': MT5.TIMEFRAME_M5,
    'H1': MT5.TIMEFRAME_H1,
    # ... etc
}
```

**Manual Steps - Install MT5:**
```powershell
# Pobierz MetaTrader 5 od swojego brokera
# Zainstaluj i zaloguj się na konto demo
# Zostaw terminal otwarty podczas testowania

# Test w Python
python

import MetaTrader5 as MT5

# Test initialization
MT5.initialize()
print(f"MT5 version: {MT5.version()}")

# Test login (użyj swoich credentials)
account = 12345678  # twój numer konta demo
password = "yourpass"
server = "ICMarkets-Demo"

logged_in = MT5.login(account, password=password, server=server)
print(f"Logged in: {logged_in}")

if logged_in:
    account_info = MT5.account_info()
    print(f"Balance: {account_info.balance}")
    print(f"Equity: {account_info.equity}")
    
# Cleanup
MT5.shutdown()
```

**Verification:**
- [ ] MT5Client class implemented
- [ ] Wszystkie metody mają async/await
- [ ] Type hints wszędzie
- [ ] Error handling wg .cursorrules pattern
- [ ] Retry logic z exponential backoff
- [ ] Manual MT5 connection test przeszedł
- [ ] Logging setup (DEBUG dla data, INFO dla trades)

---

### Task 2.3: MT5 Broker Adapter (60 min)

**Cursor AI Prompt:**
```
Implement mtquant/mcp_integration/adapters/mt5_adapter.py using the BrokerAdapter pattern from .cursorrules.

Class: MT5BrokerAdapter(BrokerAdapter)

This adapter wraps MT5Client and adds:
1. Symbol mapping (standard <-> broker symbols)
2. Order conversion (our Order model <-> MT5 orders)
3. Position conversion (MT5 positions <-> our Position model)
4. Additional validation layer

Initialization:
def __init__(self, broker_id: str, config: Dict):
    self.broker_id = broker_id
    self.mt5_client = MT5Client(broker_id, config)
    self.symbol_mapper = SymbolMapper
    self.logger = get_logger(__name__)

Methods (implement BrokerAdapter interface):

async def connect() -> bool:
    """
    Connect to broker.
    - Call mt5_client.connect()
    - Log connection success
    """

async def disconnect() -> None:
    """Disconnect cleanly."""

async def place_order(self, order: Order) -> str:
    """
    Place order with symbol mapping.
    
    Steps:
    1. Map standard symbol to broker symbol
    2. Validate order (price, quantity, etc.)
    3. Convert Order to MT5 order format
    4. Call mt5_client.place_order()
    5. Log trade for audit
    6. Return order_id
    """

async def get_positions(self) -> List[Position]:
    """
    Get positions with symbol unmapping.
    
    Steps:
    1. Fetch MT5 positions
    2. Convert to our Position model
    3. Map broker symbols back to standard
    4. Return List[Position]
    """

async def get_market_data(
    self,
    symbol: str,
    timeframe: str = 'H1',
    bars: int = 100
) -> pd.DataFrame:
    """
    Fetch market data with symbol mapping.
    
    Args:
        symbol: STANDARD symbol (e.g., XAUUSD)
        
    Steps:
    1. Map standard symbol to broker symbol
    2. Fetch data from mt5_client
    3. Add standard symbol column to DataFrame
    4. Return DataFrame
    """

async def health_check() -> HealthStatus:
    """
    Check adapter health.
    
    Returns HealthStatus dataclass:
    - is_connected: bool
    - latency_ms: float
    - last_check: datetime
    - error: Optional[str]
    """

Helper Methods:
def _convert_order_to_mt5(self, order: Order) -> Dict:
    """Convert our Order model to MT5 request dict."""

def _convert_mt5_to_position(self, mt5_position: Dict) -> Position:
    """Convert MT5 position to our Position model."""

def _validate_order(self, order: Order) -> bool:
    """
    Validate order before sending to broker.
    Checks:
    - Symbol exists
    - Quantity > 0
    - Price reasonable (if limit/stop)
    """

Error Handling:
- Wrap all mt5_client calls in try/except
- Re-raise with appropriate MTQuant exceptions
- Add context to error messages (broker_id, symbol, etc.)

Type hints for all methods.
Comprehensive docstrings.
```

**Verification:**
- [ ] MT5BrokerAdapter implements BrokerAdapter interface
- [ ] Symbol mapping integrated (uses SymbolMapper)
- [ ] Order conversion methods implemented
- [ ] Position conversion methods implemented
- [ ] Health check returns HealthStatus
- [ ] Error handling comprehensive
- [ ] All type hints present

---

### Task 2.4: Integration Test (45 min)

**Cursor AI Prompt:**
```
Create tests/integration/test_mt5_integration.py with integration tests for MT5 adapter.

Use pytest-asyncio for async tests.
These tests will run against REAL MT5 demo account.

Test Setup:
@pytest.fixture
async def mt5_adapter():
    """Create MT5 adapter connected to demo account."""
    # Load config from .env
    # Create adapter
    # Connect
    # Yield adapter
    # Disconnect in cleanup

Tests:

@pytest.mark.asyncio
async def test_mt5_connection(mt5_adapter):
    """Test basic connection to MT5 demo."""
    # Verify connection
    # Check health status
    # Assert is_connected = True

@pytest.mark.asyncio
async def test_fetch_market_data(mt5_adapter):
    """Test fetching OHLCV data for XAUUSD."""
    # Fetch data for standard symbol XAUUSD
    # Assert DataFrame not empty
    # Assert has correct columns
    # Assert data is recent (last bar < 1 hour old)

@pytest.mark.asyncio
async def test_get_account_info(mt5_adapter):
    """Test account info retrieval."""
    # Get account info
    # Assert balance > 0
    # Assert equity > 0
    # Assert margin fields present

@pytest.mark.asyncio
async def test_symbol_mapping(mt5_adapter):
    """Test symbol mapping works end-to-end."""
    # Verify XAUUSD maps correctly for this broker
    # Fetch data using standard symbol
    # Check broker symbol used internally

@pytest.mark.asyncio  
async def test_get_positions_empty(mt5_adapter):
    """Test getting positions (should be empty on fresh demo)."""
    # Get positions
    # Assert empty list (or handle if positions exist)

Add pytest.ini configuration:
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

markers =
    integration: Integration tests requiring external services
    unit: Unit tests (no external dependencies)
```

**Manual Steps:**
```powershell
# Upewnij się że MT5 terminal jest otwarty i zalogowany

# Uruchom integration tests
pytest tests/integration/test_mt5_integration.py -v -s

# Expected output:
# test_mt5_connection PASSED
# test_fetch_market_data PASSED
# test_get_account_info PASSED
# test_symbol_mapping PASSED
# test_get_positions_empty PASSED
```

**Verification:**
- [ ] Integration test file created
- [ ] pytest.ini configured
- [ ] MT5 terminal running i zalogowany
- [ ] Wszystkie testy PASS
- [ ] Dane z MT5 poprawnie pobrane (OHLCV dla XAUUSD)
- [ ] Symbol mapping działa (XAUUSD <-> broker symbol)

---

### Task 2.5: Day 2 Commit (15 min)

```powershell
git add .
git commit -m "feat: MT5 integration with broker adapter

- SymbolMapper with config loading and caching
- MT5Client with async operations and error handling
- MT5BrokerAdapter implementing BrokerAdapter pattern
- Integration tests for MT5 connection and data fetch
- Symbol mapping end-to-end functionality
- Health check implementation

Tests: 5/5 passing
Sprint 1, Day 2 complete"
```

---

## DAY 3 - Connection Pool & Broker Manager

### Task 3.1: Connection Pool (60 min)

**Cursor AI Prompt:**
```
Implement mtquant/mcp_integration/managers/connection_pool.py for managing multiple broker connections.

Features:
1. Pool of broker adapters (MT5, MT4 in future)
2. Health monitoring (periodic checks every 30s)
3. Automatic failover to backup broker
4. Connection statistics tracking

Class: ConnectionPool

Properties:
- adapters: Dict[str, BrokerAdapter] (broker_id -> adapter)
- health_status: Dict[str, HealthStatus]
- primary_broker: str
- backup_brokers: List[str]

Methods:

async def add_adapter(
    self,
    broker_id: str,
    adapter: BrokerAdapter,
    is_primary: bool = False
) -> None:
    """
    Add broker adapter to pool.
    
    Args:
        broker_id: Unique broker identifier
        adapter: BrokerAdapter instance
        is_primary: Mark as primary broker for routing
    """

async def connect_all(self) -> Dict[str, bool]:
    """
    Connect all adapters in pool.
    Returns dict of broker_id -> connection_status
    """

async def disconnect_all(self) -> None:
    """Disconnect all adapters cleanly."""

async def get_adapter(self, broker_id: str) -> BrokerAdapter:
    """
    Get specific adapter by ID.
    Raises KeyError if not found.
    """

async def get_healthy_adapter(self) -> BrokerAdapter:
    """
    Get first healthy adapter.
    Priority: primary broker -> backup brokers
    
    Raises:
        BrokerConnectionError: If no healthy adapters available
    """

async def health_check_all(self) -> Dict[str, HealthStatus]:
    """
    Check health of all adapters.
    Updates internal health_status dict.
    Returns current health status.
    """

async def start_health_monitoring(self, interval: int = 30) -> None:
    """
    Start background task for periodic health checks.
    
    Args:
        interval: Seconds between health checks
    """

async def stop_health_monitoring(self) -> None:
    """Stop health monitoring task."""

async def failover_to_backup(self) -> str:
    """
    Failover to backup broker.
    
    Returns:
        broker_id of new primary broker
        
    Raises:
        BrokerConnectionError: If no backup available
    """

Statistics Methods:
def get_connection_stats(self) -> Dict:
    """
    Return connection statistics:
    - total_adapters
    - healthy_adapters  
    - primary_broker
    - backup_brokers
    - uptime per broker
    """

Implementation Notes:
- Use asyncio.create_task() for background monitoring
- Log all failovers (WARNING level)
- Track connection attempts and failures
- Thread-safe (use asyncio.Lock for adapter dict access)

Type hints, docstrings, comprehensive error handling.
```

**Verification:**
- [ ] ConnectionPool class implemented
- [ ] Can add multiple adapters
- [ ] Health monitoring background task works
- [ ] Failover logic implemented
- [ ] Statistics tracking present
- [ ] Type hints and docstrings complete

---

### Task 3.2: Broker Manager (75 min)

**Cursor AI Prompt:**
```
Implement mtquant/mcp_integration/managers/broker_manager.py as the main orchestrator for broker operations.

This is the high-level API that other parts of MTQuant will use.

Class: BrokerManager

Initialization:
def __init__(self):
    self.connection_pool = ConnectionPool()
    self.symbol_mapper = SymbolMapper
    self.logger = get_logger(__name__)
    self._initialized = False

Setup:
async def initialize(self, broker_configs: List[Dict]) -> None:
    """
    Initialize broker manager with configurations.
    
    Args:
        broker_configs: List of broker config dicts from brokers.yaml
        
    Steps:
    1. Create adapter for each broker config
    2. Add to connection pool
    3. Connect all adapters
    4. Start health monitoring
    5. Set _initialized = True
    """

async def shutdown(self) -> None:
    """Shutdown all connections cleanly."""

Trading Operations (with intelligent routing):

async def place_order(
    self,
    order: Order,
    preferred_broker: Optional[str] = None
) -> str:
    """
    Place order with intelligent broker selection.
    
    Args:
        order: Order object (with STANDARD symbol)
        preferred_broker: Optional broker preference
        
    Logic:
    1. If preferred_broker specified and healthy -> use it
    2. Else get healthy adapter from pool
    3. Place order
    4. Return order_id
    
    Raises:
        BrokerError: If order fails
        RiskViolationError: If order violates limits (future)
    """

async def get_positions(
    self,
    broker_id: Optional[str] = None
) -> List[Position]:
    """
    Get positions from broker(s).
    
    Args:
        broker_id: Specific broker, or None for all brokers
        
    Returns:
        List of positions (aggregated if multiple brokers)
    """

async def close_position(
    self,
    position_id: str,
    broker_id: str
) -> bool:
    """Close specific position at specific broker."""

Market Data Operations:

async def get_market_data(
    self,
    symbol: str,
    timeframe: str = 'H1',
    bars: int = 100,
    broker_id: Optional[str] = None
) -> pd.DataFrame:
    """
    Fetch market data with automatic broker selection.
    
    Args:
        symbol: STANDARD symbol (XAUUSD, BTCUSD, etc.)
        timeframe: Timeframe string
        bars: Number of bars
        broker_id: Optional specific broker
        
    Logic:
    1. Map symbol for target broker
    2. Fetch data from healthy adapter
    3. Return DataFrame with standard symbol
    """

async def get_account_info(
    self,
    broker_id: Optional[str] = None
) -> Dict[str, Dict]:
    """
    Get account info from broker(s).
    
    Returns:
        Dict of broker_id -> account_info
    """

Monitoring:

async def get_broker_status(self) -> Dict[str, Any]:
    """
    Get comprehensive broker status.
    
    Returns:
        {
            'healthy_brokers': List[str],
            'unhealthy_brokers': List[str],
            'primary_broker': str,
            'connection_stats': Dict,
            'last_health_check': datetime
        }
    """

def is_initialized(self) -> bool:
    """Check if manager is initialized."""

Helper Methods:

def _select_broker_for_order(
    self,
    order: Order,
    preferred: Optional[str]
) -> str:
    """
    Intelligent broker selection logic.
    
    Priority:
    1. Preferred broker (if healthy)
    2. Primary broker (if healthy)
    3. First healthy backup
    
    Consider:
    - Broker health
    - Spread/commission (future)
    - Latency (future)
    """

Implementation:
- Use connection pool for all adapter access
- Comprehensive logging (INFO for operations, DEBUG for routing decisions)
- Error handling per .cursorrules
- Type hints everywhere
- Docstrings for all public methods

Example usage in docstring:
```python
# Initialize manager
manager = BrokerManager()
configs = load_broker_configs()  # from YAML
await manager.initialize(configs)

# Place order (automatic broker selection)
order = Order(symbol='XAUUSD', side='buy', quantity=0.1, ...)
order_id = await manager.place_order(order)

# Get positions from all brokers
positions = await manager.get_positions()

# Get market data
data = await manager.get_market_data('XAUUSD', 'H1', bars=200)
```
```

**Verification:**
- [ ] BrokerManager class implemented
- [ ] Initialization loads configs and connects
- [ ] Intelligent broker selection works
- [ ] Can place orders through manager
- [ ] Can get positions aggregated
- [ ] Market data fetch works with any broker
- [ ] Status monitoring implemented

---

### Task 3.3: Integration Test - Manager (45 min)

**Cursor AI Prompt:**
```
Create tests/integration/test_broker_manager.py for BrokerManager integration tests.

Test Setup:
@pytest.fixture
async def broker_configs():
    """Load broker configs from YAML."""
    # Load config/brokers.yaml
    # Filter for demo accounts only
    # Return list of configs

@pytest.fixture
async def broker_manager(broker_configs):
    """Create and initialize BrokerManager."""
    manager = BrokerManager()
    await manager.initialize(broker_configs)
    yield manager
    await manager.shutdown()

Tests:

@pytest.mark.asyncio
async def test_manager_initialization(broker_manager):
    """Test manager initializes correctly."""
    assert broker_manager.is_initialized()
    status = await broker_manager.get_broker_status()
    assert len(status['healthy_brokers']) > 0

@pytest.mark.asyncio
async def test_market_data_fetch(broker_manager):
    """Test market data fetch through manager."""
    # Fetch XAUUSD data (standard symbol)
    data = await broker_manager.get_market_data('XAUUSD', 'H1', bars=50)
    
    # Verify DataFrame
    assert not data.empty
    assert len(data) == 50
    assert 'close' in data.columns

@pytest.mark.asyncio
async def test_get_positions(broker_manager):
    """Test getting positions from all brokers."""
    positions = await broker_manager.get_positions()
    # Should be list (empty or with positions)
    assert isinstance(positions, list)

@pytest.mark.asyncio
async def test_broker_failover(broker_manager):
    """Test failover when primary broker goes down."""
    # Get initial primary
    status = await broker_manager.get_broker_status()
    primary = status['primary_broker']
    
    # Simulate primary failure (disconnect it)
    await broker_manager.connection_pool.get_adapter(primary).disconnect()
    
    # Health check should detect failure
    await broker_manager.connection_pool.health_check_all()
    
    # Try to fetch data (should use backup)
    data = await broker_manager.get_market_data('XAUUSD')
    assert not data.empty  # Should work with backup

@pytest.mark.asyncio
async def test_account_info(broker_manager):
    """Test getting account info from all brokers."""
    info = await broker_manager.get_account_info()
    
    # Should have at least one broker
    assert len(info) > 0
    
    # Check first broker has required fields
    first_broker = list(info.values())[0]
    assert 'balance' in first_broker
    assert 'equity' in first_broker

Run with:
pytest tests/integration/test_broker_manager.py -v -s --tb=short
```

**Manual Steps:**
```powershell
# Upewnij się że MT5 terminal jest running

# Run tests
pytest tests/integration/test_broker_manager.py -v -s

# Expected: All tests PASS
```

**Verification:**
- [ ] Test file created
- [ ] BrokerManager initialization test passes
- [ ] Market data test passes (fetches XAUUSD H1)
- [ ] Positions test passes
- [ ] Failover test passes (or skipped if only 1 broker)
- [ ] Account info test passes

---

### Task 3.4: Day 3 Commit (15 min)

```powershell
git add .
git commit -m "feat: broker management layer with connection pooling

- ConnectionPool for managing multiple broker connections
- Health monitoring with automatic failover
- BrokerManager as high-level API for trading operations
- Intelligent broker selection for order routing
- Integration tests for manager and failover
- Account aggregation across multiple brokers

Tests: 10/10 passing (5 from Day 2 + 5 from Day 3)
Sprint 1, Day 3 complete"
```

---

## DAY 4-5 - Risk Management Foundation

### Task 4.1: Pre-Trade Checker (90 min)

**Cursor AI Prompt:**
```
Implement mtquant/risk_management/pre_trade_checker.py for pre-trade risk validation.

This runs BEFORE every order execution. Must execute in <50ms.

Class: PreTradeChecker

Initialization:
def __init__(self, risk_limits: Dict):
    """
    Args:
        risk_limits: Loaded from config/risk-limits.yaml
    """
    self.limits = risk_limits
    self.logger = get_logger(__name__)

Validation Methods:

async def validate(self, order: Order, portfolio: Dict) -> ValidationResult:
    """
    Comprehensive pre-trade validation.
    
    Args:
        order: Order to validate
        portfolio: Current portfolio state (equity, positions, etc.)
        
    Returns:
        ValidationResult with:
            - is_valid: bool
            - checks_passed: List[str]
            - checks_failed: List[str]
            - error_message: Optional[str]
            
    Runs all checks in parallel for speed.
    """
    
async def check_price_band(self, order: Order, last_price: float) -> bool:
    """
    Validate price is within reasonable band.
    
    Check: |order.price - last_price| / last_price <= price_band_pct
    
    Returns: True if valid
    Raises: ValueError if price outside band
    """

async def check_position_size(self, order: Order, portfolio: Dict) -> bool:
    """
    Validate position size limits.
    
    Checks:
    - order.quantity > min_position_size
    - order.quantity <= max_position_size_pct * portfolio['equity']
    - order.quantity <= max_position_size_adv_pct * avg_daily_volume
    
    Returns: True if valid
    Raises: PositionSizeError if exceeds limits
    """

async def check_capital_availability(
    self,
    order: Order,
    portfolio: Dict
) -> bool:
    """
    Validate sufficient capital/margin.
    
    Checks:
    - required_margin = order.quantity * order.price / leverage
    - free_margin = portfolio['equity'] - portfolio['used_margin']
    - required_margin <= free_margin
    
    Returns: True if sufficient capital
    Raises: InsufficientMarginError if not enough margin
    """

async def check_portfolio_exposure(
    self,
    order: Order,
    current_positions: List[Position]
) -> bool:
    """
    Check total portfolio exposure limits.
    
    Checks:
    - Total exposure (current + new order) <= max_total_exposure_pct
    - Sector/asset class exposure <= max_sector_exposure_pct
    
    Returns: True if within limits
    Raises: RiskViolationError if exceeds exposure limits
    """

async def check_regulatory_limits(self, order: Order) -> bool:
    """
    Regulatory compliance checks.
    
    Checks:
    - Leverage within regulatory limits per instrument
    - Pattern day trader rules (if applicable)
    - Any instrument-specific restrictions
    
    Returns: True if compliant
    Raises: RiskViolationError if non-compliant
    """

async def check_correlation_risk(
    self,
    order: Order,
    current_positions: List[Position]
) -> bool:
    """
    Check correlation with existing positions.
    
    If new order would create correlated positions (ρ > 0.7),
    warn or reject based on configuration.
    
    Returns: True if acceptable correlation
    Raises: RiskViolationError if correlation too high
    """

Helper Class:
@dataclass
class ValidationResult:
    is_valid: bool
    checks_passed: List[str]
    checks_failed: List[str]
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0

Implementation Notes:
- Run checks in parallel with asyncio.gather()
- Target execution time: <50ms
- Log all failures (WARNING level)
- Log passes (DEBUG level)
- Include timing in ValidationResult

Type hints, comprehensive docstrings, error handling per .cursorrules.
```

**Verification:**
- [ ] PreTradeChecker class implemented
- [ ] All 6 validation methods present
- [ ] ValidationResult dataclass defined
- [ ] Checks run in parallel (asyncio.gather)
- [ ] Execution time tracked and <50ms
- [ ] Comprehensive error handling
- [ ] Type hints and docstrings complete

---

### Task 4.2: Position Sizer (75 min)

**Cursor AI Prompt:**
```
Implement mtquant/risk_management/position_sizer.py for intelligent position sizing.

Supports multiple strategies: Kelly Criterion, Volatility-based, Fixed Fractional.

Class: PositionSizer

Initialization:
def __init__(self, config: Dict):
    """
    Args:
        config: Position sizing configuration
            - method: 'kelly' | 'volatility' | 'fixed'
            - risk_per_trade: float (e.g., 0.02 for 2%)
            - kelly_fraction: float (e.g., 0.25 for quarter Kelly)
    """

Core Method:
async def calculate(
    self,
    signal: float,
    portfolio_equity: float,
    instrument_volatility: float,
    win_rate: Optional[float] = None,
    avg_win: Optional[float] = None,
    avg_loss: Optional[float] = None,
    method: Optional[str] = None
) -> float:
    """
    Calculate optimal position size.
    
    Args:
        signal: RL agent signal (-1 to 1)
        portfolio_equity: Total portfolio value
        instrument_volatility: ATR or realized volatility
        win_rate: Historical win rate (for Kelly)
        avg_win: Average win amount (for Kelly)
        avg_loss: Average loss amount (for Kelly)
        method: Override default method
        
    Returns:
        position_size: Position size in lots (fractional)
        
    Process:
    1. Calculate base size using selected method
    2. Scale by signal strength (abs(signal))
    3. Apply max position limit
    4. Return final size
    """

Strategy Methods:

def _kelly_criterion(
    self,
    win_rate: float,
    avg_win: float,
    avg_loss: float,
    portfolio_equity: float
) -> float:
    """
    Kelly Criterion position sizing.
    
    Formula: Kelly% = (win_rate * avg_win - (1-win_rate) * avg_loss) / avg_loss
    Use fractional Kelly (0.25x) for safety.
    
    Returns: Position size in USD
    """

def _volatility_based(
    self,
    risk_per_trade: float,
    portfolio_equity: float,
    volatility: float,
    atr_multiplier: float = 2.0
) -> float:
    """
    Volatility-based position sizing.
    
    Formula: Position = (Risk% * Portfolio) / (ATR * Multiplier)
    
    Args:
        risk_per_trade: Max risk per trade (e.g., 0.02)
        portfolio_equity: Total equity
        volatility: ATR or standard deviation
        atr_multiplier: Stop-loss distance in ATR units
        
    Returns: Position size
    """

def _fixed_fractional(
    self,
    fraction: float,
    portfolio_equity: float
) -> float:
    """
    Fixed fractional position sizing.
    
    Simple: Position = Portfolio * Fraction
    
    Args:
        fraction: Fixed % of portfolio (e.g., 0.02 for 2%)
        portfolio_equity: Total equity
        
    Returns: Position size
    """

def _apply_signal_scaling(self, base_size: float, signal: float) -> float:
    """
    Scale position by signal strength.
    
    If signal = 0.5 (weak), use 50% of calculated size.
    If signal = 1.0 (strong), use 100% of calculated size.
    
    Returns: Scaled position size
    """

def _apply_limits(self, size: float, max_size: float) -> float:
    """
    Apply max position limit.
    
    Ensures: size <= max_size
    Returns: Capped position size
    """

Validation:
def validate_inputs(
    self,
    signal: float,
    portfolio_equity: float,
    volatility: float
) -> None:
    """
    Validate inputs before calculation.
    
    Checks:
    - -1 <= signal <= 1
    - portfolio_equity > 0
    - volatility > 0
    
    Raises: ValueError if invalid
    """

Helper Methods:
def get_method_name(self) -> str:
    """Return current sizing method name."""

def get_config(self) -> Dict:
    """Return current configuration."""

Implementation:
- Type hints for all methods
- Docstrings with formulas and examples
- Comprehensive logging (DEBUG for calculations)
- Error handling for edge cases (zero volatility, etc.)

Example usage in docstring:
```python
sizer = PositionSizer(config={
    'method': 'volatility',
    'risk_per_trade': 0.02
})

position_size = await sizer.calculate(
    signal=0.8,  # Strong buy signal
    portfolio_equity=50000,
    instrument_volatility=15.5,
    method='volatility'
)
# Returns: position size in lots
```
```

**Verification:**
- [ ] PositionSizer class implemented
- [ ] Kelly Criterion method works
- [ ] Volatility-based method works
- [ ] Fixed fractional method works
- [ ] Signal scaling applied correctly
- [ ] Limits enforced (max position size)
- [ ] Input validation present

---

### Task 4.3: Circuit Breaker (60 min)

**Cursor AI Prompt:**
```
Implement mtquant/risk_management/circuit_breaker.py for automatic trading halts.

Three-tier circuit breaker system following .cursorrules specification.

Class: CircuitBreaker

Initialization:
def __init__(self, config: Dict):
    """
    Args:
        config: Circuit breaker configuration from risk-limits.yaml
            - level_1_loss_pct: float (e.g., 0.05 for 5%)
            - level_2_loss_pct: float (e.g., 0.10)
            - level_3_loss_pct: float (e.g., 0.15)
            - cooldown_minutes: int (time before reset)
    """
    self.config = config
    self.status = CircuitBreakerStatus.NORMAL
    self.triggered_at: Optional[datetime] = None
    self.trigger_level: Optional[int] = None
    self.logger = get_logger(__name__)

Status Enum:
class CircuitBreakerStatus(Enum):
    NORMAL = "normal"
    LEVEL_1 = "level_1_warning"
    LEVEL_2 = "level_2_reduce"
    LEVEL_3 = "level_3_halt"

Core Methods:

async def check(
    self,
    daily_pnl_pct: float,
    portfolio: Dict
) -> CircuitBreakerStatus:
    """
    Check if circuit breaker should trigger.
    
    Args:
        daily_pnl_pct: Daily P&L as percentage (e.g., -0.06 for -6%)
        portfolio: Current portfolio state
        
    Logic:
    1. If daily_pnl_pct <= -15% -> Level 3 (HALT)
    2. Elif daily_pnl_pct <= -10% -> Level 2 (REDUCE)
    3. Elif daily_pnl_pct <= -5% -> Level 1 (WARNING)
    4. Else -> NORMAL
    
    If status changes:
    - Update self.status
    - Set self.triggered_at
    - Log event (CRITICAL for L3, WARNING for L1-2)
    - Send alerts
    - Execute appropriate action
    
    Returns: Current CircuitBreakerStatus
    """

async def level_1_activate(self) -> None:
    """
    Level 1: Warning (5% daily loss)
    
    Actions:
    - Send WARNING alerts to monitoring
    - Log event
    - Reduce position sizes by 25%
    - No trading halt
    """

async def level_2_activate(self) -> None:
    """
    Level 2: Reduce Positions (10% daily loss)
    
    Actions:
    - Send HIGH PRIORITY alerts
    - Halt new position openings
    - Close most risky positions (highest loss or volatility)
    - Keep only core positions
    - Reduce position sizes by 50%
    """

async def level_3_activate(self) -> None:
    """
    Level 3: FULL HALT (15-20% daily loss)
    
    Actions:
    - Send CRITICAL alerts (SMS + email)
    - HALT ALL trading immediately
    - Flatten ALL positions
    - Lock system (manual intervention required to resume)
    - Log full state for post-mortem
    """

async def reset(self) -> bool:
    """
    Reset circuit breaker to NORMAL.
    
    Conditions:
    - Can only reset if cooldown period elapsed
    - Requires manual confirmation (safety)
    
    Returns: True if reset successful
    Raises: CircuitBreakerError if reset not allowed
    """

async def can_trade(self) -> bool:
    """
    Check if trading is allowed.
    
    Returns:
        - True if NORMAL or LEVEL_1
        - False if LEVEL_2 or LEVEL_3
    """

async def get_status_report(self) -> Dict:
    """
    Get detailed status report.
    
    Returns:
        {
            'status': CircuitBreakerStatus,
            'triggered_at': Optional[datetime],
            'trigger_level': Optional[int],
            'time_since_trigger_mins': Optional[float],
            'can_reset': bool,
            'can_trade': bool
        }
    """

Helper Methods:

def _is_cooldown_elapsed(self) -> bool:
    """Check if cooldown period has elapsed since trigger."""

def _send_alert(self, level: int, message: str) -> None:
    """Send alert via monitoring system (placeholder for now)."""

def _log_trigger(self, level: int, daily_pnl_pct: float) -> None:
    """
    Log circuit breaker trigger with full context.
    Level 1: WARNING
    Level 2: ERROR  
    Level 3: CRITICAL
    """

Implementation Notes:
- Thread-safe (use asyncio.Lock for status changes)
- Comprehensive logging at each trigger
- Alert placeholders (implement with alert system later)
- Status persists until manual reset (safety)
- Type hints, docstrings everywhere

Example usage:
```python
breaker = CircuitBreaker(config=risk_limits['circuit_breaker'])

# Check during trading
current_status = await breaker.check(
    daily_pnl_pct=-0.06,  # -6% daily loss
    portfolio={'equity': 48000, 'start_equity': 50000}
)

if current_status == CircuitBreakerStatus.LEVEL_3:
    # HALT triggered - flatten all positions
    await flatten_all_positions()
```
```

**Verification:**
- [ ] CircuitBreaker class implemented
- [ ] CircuitBreakerStatus enum defined
- [ ] Three-tier logic (5%/10%/15%) works
- [ ] Level 1: Warning + reduce size 25%
- [ ] Level 2: Halt new + close risky
- [ ] Level 3: FULL HALT + flatten all
- [ ] Reset requires cooldown elapsed
- [ ] Status tracking and reporting works

---

### Task 4.4: Risk Management Integration Test (45 min)

**Cursor AI Prompt:**
```
Create tests/unit/test_risk_management.py for risk management unit tests.

Test all three components: PreTradeChecker, PositionSizer, CircuitBreaker.

Mock data - no external dependencies.

Test Cases:

# PreTradeChecker Tests
def test_price_band_validation():
    """Test price must be within ±10% of last known price."""
    # Valid price (within band)
    # Invalid price (outside band)

def test_position_size_limits():
    """Test position size limits enforced."""
    # Within limits
    # Exceeds max size
    # Below min size

def test_capital_availability():
    """Test sufficient margin check."""
    # Sufficient margin
    # Insufficient margin -> raises InsufficientMarginError

async def test_comprehensive_validation():
    """Test full validation with all checks."""
    # All checks pass
    # Some checks fail
    # ValidationResult correct

# PositionSizer Tests
def test_kelly_criterion():
    """Test Kelly Criterion calculation."""
    # With 60% win rate, avg win 100, avg loss 50
    # Expected: Kelly% = (0.6*100 - 0.4*50)/50 = 0.8
    # Fractional (0.25x) = 0.2
    # Verify calculation

def test_volatility_based_sizing():
    """Test volatility-based position sizing."""
    # Portfolio: $50k, Risk: 2%, ATR: 20
    # Expected: (50000 * 0.02) / (20 * 2) = 25
    # Verify calculation

def test_signal_scaling():
    """Test position scaled by signal strength."""
    # Base size: 100
    # Signal: 0.5 (weak) -> 50
    # Signal: 1.0 (strong) -> 100
    # Verify scaling

def test_position_limits_applied():
    """Test max position limit enforced."""
    # Calculated: 150, Max: 100 -> Result: 100
    # Verify limit applied

# CircuitBreaker Tests
async def test_circuit_breaker_levels():
    """Test circuit breaker triggers at correct levels."""
    # -3% loss -> NORMAL
    # -6% loss -> LEVEL_1
    # -11% loss -> LEVEL_2
    # -16% loss -> LEVEL_3

async def test_circuit_breaker_reset():
    """Test reset conditions."""
    # Cannot reset before cooldown
    # Can reset after cooldown

async def test_trading_allowed():
    """Test can_trade() logic."""
    # NORMAL -> True
    # LEVEL_1 -> True (warning only)
    # LEVEL_2 -> False (halt new positions)
    # LEVEL_3 -> False (full halt)

Use pytest fixtures for setup:
@pytest.fixture
def risk_limits():
    return {
        'max_position_size_pct': 0.10,
        'price_band_pct': 0.10,
        'circuit_breaker': {
            'level_1_loss_pct': 0.05,
            'level_2_loss_pct': 0.10,
            'level_3_loss_pct': 0.15,
            'cooldown_minutes': 60
        }
    }

@pytest.fixture
def portfolio():
    return {
        'equity': 50000,
        'balance': 50000,
        'used_margin': 5000,
        'free_margin': 45000
    }

Run with:
pytest tests/unit/test_risk_management.py -v --cov=mtquant/risk_management
```

**Manual Steps:**
```powershell
# Run unit tests
pytest tests/unit/test_risk_management.py -v --cov=mtquant/risk_management

# Expected output:
# test_price_band_validation PASSED
# test_position_size_limits PASSED
# test_capital_availability PASSED
# ... (all tests PASSED)
# Coverage: >80%
```

**Verification:**
- [ ] All PreTradeChecker tests pass
- [ ] All PositionSizer tests pass
- [ ] All CircuitBreaker tests pass
- [ ] Coverage >80% for risk_management module
- [ ] No external dependencies in unit tests

---

### Task 4.5: Days 4-5 Commit (15 min)

```powershell
git add .
git commit -m "feat: comprehensive risk management system

- PreTradeChecker with 6-layer validation (<50ms execution)
- PositionSizer with Kelly, volatility, and fixed fractional methods
- CircuitBreaker with 3-tier halt system (5%/10%/15%)
- Signal-based position scaling
- Correlation risk monitoring
- Unit tests for all risk components

Tests: 25+ passing
Coverage: >80% for risk_management module
Sprint 1, Days 4-5 complete"
```

---

## DAY 6-7 - First RL Agent & End-to-End Test

### Task 6.1: Basic Trading Environment (90 min)

**Cursor AI Prompt:**
```
Create mtquant/agents/environments/base_trading_env.py - a FinRL-compatible trading environment.

This is the foundation for RL agents to learn trading.

Import and extend:
from finrl.meta.env_stock_trading.env_stocktrading import StockTradingEnv
import gymnasium as gym

Class: MTQuantTradingEnv(StockTradingEnv)

Customizations for MTQuant:

1. State Space (following .cursorrules):
   - Log returns (NOT raw prices)
   - Normalized technical indicators (RSI, MACD, Bollinger, SMA)
   - Position state (holdings, cash, unrealized P&L, position age)
   - Risk metrics (portfolio volatility, drawdown, Sharpe)

2. Action Space:
   - Continuous: -1 to 1 (where 0=flat, positive=long, negative=short)
   - Maps to position size via PositionSizer

3. Reward Function (risk-adjusted):
   def _calculate_reward(self, action: float) -> float:
       """
       Sortino ratio - transaction costs
       
       reward = (returns - rf_rate) / downside_volatility - tx_cost_penalty
       
       Penalizes:
       - Downside volatility (not upside)
       - Transaction costs (0.003 per trade)
       - Excessive trading
       
       Rewards:
       - Risk-adjusted returns
       - Holding winning positions
       """

4. Integration with MTQuant:
   def __init__(
       self,
       symbol: str,
       historical_data: pd.DataFrame,
       initial_capital: float = 10000,
       transaction_cost: float = 0.003,
       risk_limits: Dict = None,
       position_sizer: PositionSizer = None
   ):
       """
       Args:
           symbol: Instrument to trade (XAUUSD, BTCUSD, etc.)
           historical_data: OHLCV DataFrame with indicators
           initial_capital: Starting capital
           transaction_cost: Cost per trade (0.3%)
           risk_limits: Risk limits from config
           position_sizer: PositionSizer instance
       """

5. Methods to Override:
   def _get_state(self) -> np.ndarray:
       """
       Construct state vector.
       
       State = [
           log_returns,  # Stationary
           normalized_rsi,
           normalized_macd,
           normalized_bollinger,
           holdings_normalized,
           cash_normalized,
           unrealized_pnl_normalized,
           position_age_normalized,
           portfolio_volatility,
           current_drawdown
       ]
       
       All values normalized to 0-1 or -1 to 1.
       """

   def step(self, action: float) -> Tuple[np.ndarray, float, bool, bool, Dict]:
       """
       Execute one trading step.
       
       Args:
           action: Continuous action (-1 to 1)
           
       Process:
       1. Convert action to position size via PositionSizer
       2. Validate with PreTradeChecker (if available)
       3. Execute trade (update portfolio)
       4. Calculate reward (Sortino - tx cost)
       5. Get next state
       6. Check if episode done
       
       Returns:
           (state, reward, terminated, truncated, info)
       """

   def _execute_trade(self, action: float) -> Dict:
       """
       Execute trade based on action.
       
       Returns:
           trade_info: {
               'action': float,
               'position_size': float,
               'execution_price': float,
               'transaction_cost': float,
               'pnl': float
           }
       """

6. Risk Integration:
   def _validate_action(self, action: float) -> bool:
       """
       Optional: Validate action with PreTradeChecker.
       
       If risk check fails:
       - Log warning
       - Return False
       - Environment will use action=0 (flat)
       
       This makes RL agent learn risk-aware behavior.
       """

7. Metrics Tracking:
   def _update_metrics(self) -> None:
       """
       Track episode metrics:
       - Total trades
       - Win rate
       - Sharpe ratio
       - Max drawdown
       - Average holding period
       
       Store in self.episode_metrics
       """

   def get_episode_summary(self) -> Dict:
       """
       Return episode summary for analysis.
       
       Returns:
           {
               'total_trades': int,
               'win_rate': float,
               'sharpe_ratio': float,
               'sortino_ratio': float,
               'max_drawdown': float,
               'total_return': float,
               'avg_holding_period': float
           }
       """

Implementation Notes:
- Follow FinRL conventions for compatibility
- Use gymnasium API (not old gym)
- Comprehensive logging (DEBUG level for steps, INFO for episodes)
- Type hints everywhere
- Docstrings with examples

Example usage in docstring:
```python
# Load historical data
data = pd.read_csv('XAUUSD_H1.csv')  # With indicators

# Create environment
env = MTQuantTradingEnv(
    symbol='XAUUSD',
    historical_data=data,
    initial_capital=10000,
    transaction_cost=0.003
)

# Test with random agent
obs, info = env.reset()
for _ in range(100):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        break

# Get episode metrics
summary = env.get_episode_summary()
print(f"Sharpe: {summary['sharpe_ratio']:.2f}")
```
```

**Verification:**
- [ ] MTQuantTradingEnv class implemented
- [ ] Extends FinRL StockTradingEnv
- [ ] State space uses log returns (not prices)
- [ ] Reward function is Sortino - tx costs
- [ ] Action space continuous (-1 to 1)
- [ ] Episode metrics tracking works
- [ ] Environment runs without errors

---

### Task 6.2: PPO Agent Training Script (75 min)

**Cursor AI Prompt:**
```
Create mtquant/agents/training/train_ppo.py for training PPO agent on single instrument.

Use Stable Baselines3 PPO with FinRL environment.

Script structure:

```python
import pandas as pd
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from mtquant.agents.environments.base_trading_env import MTQuantTradingEnv
from mtquant.data.processors.feature_engineering import add_technical_indicators
from mtquant.utils.logger import get_logger
import yaml

logger = get_logger(__name__)

def load_config(config_path: str = 'config/agents.yaml') -> Dict:
    """Load agent training configuration."""
    with open(config_path) as f:
        return yaml.safe_load(f)

def prepare_data(symbol: str, timeframe: str = 'H1') -> pd.DataFrame:
    """
    Load and prepare historical data.
    
    Args:
        symbol: Instrument symbol
        timeframe: Data timeframe (H1, H4, D1)
        
    Returns:
        DataFrame with OHLCV + technical indicators
        
    Process:
    1. Load historical data (from CSV or database)
    2. Add technical indicators (RSI, MACD, Bollinger, SMA)
    3. Calculate log returns
    4. Drop NaN rows
    5. Normalize indicators to 0-1 range
    """
    # Placeholder: Load from file or database
    # In production: fetch from BrokerManager
    data = pd.read_csv(f'data/historical/{symbol}_{timeframe}.csv')
    
    # Add technical indicators
    data = add_technical_indicators(data)
    
    # Calculate log returns
    data['log_returns'] = np.log(data['close'] / data['close'].shift(1))
    
    # Drop NaN
    data = data.dropna()
    
    logger.info(f"Prepared {len(data)} bars for {symbol}")
    return data

def create_env(symbol: str, data: pd.DataFrame, config: Dict) -> DummyVecEnv:
    """
    Create vectorized training environment.
    
    Args:
        symbol: Instrument symbol
        data: Historical data with indicators
        config: Agent configuration
        
    Returns:
        Vectorized environment for training
    """
    def make_env():
        return MTQuantTradingEnv(
            symbol=symbol,
            historical_data=data,
            initial_capital=config['initial_capital'],
            transaction_cost=config['transaction_cost']
        )
    
    # Wrap in DummyVecEnv (required by SB3)
    env = DummyVecEnv([make_env])
    return env

def train_ppo_agent(
    symbol: str,
    data: pd.DataFrame,
    config: Dict,
    total_timesteps: int = 100000,
    model_save_path: str = 'models/checkpoints'
) -> PPO:
    """
    Train PPO agent on historical data.
    
    Args:
        symbol: Instrument to trade
        data: Historical data
        config: Training configuration
        total_timesteps: Number of training steps
        model_save_path: Where to save model checkpoints
        
    Returns:
        Trained PPO model
    """
    logger.info(f"Training PPO agent for {symbol}")
    logger.info(f"Data shape: {data.shape}")
    logger.info(f"Total timesteps: {total_timesteps}")
    
    # Create environment
    env = create_env(symbol, data, config)
    
    # Initialize PPO agent
    model = PPO(
        policy='MlpPolicy',
        env=env,
        learning_rate=config['learning_rate'],
        n_steps=config['n_steps'],
        batch_size=config['batch_size'],
        gamma=config['gamma'],
        gae_lambda=config['gae_lambda'],
        ent_coef=config['ent_coef'],
        verbose=1,
        tensorboard_log=f'./logs/tensorboard/{symbol}'
    )
    
    # Train
    model.learn(
        total_timesteps=total_timesteps,
        callback=None,  # Add callbacks for checkpointing later
        progress_bar=True
    )
    
    # Save final model
    model_path = f'{model_save_path}/{symbol}_ppo_final.zip'
    model.save(model_path)
    logger.info(f"Model saved to {model_path}")
    
    return model

def evaluate_agent(model: PPO, env: DummyVecEnv, n_episodes: int = 10) -> Dict:
    """
    Evaluate trained agent.
    
    Args:
        model: Trained PPO model
        env: Environment to evaluate on
        n_episodes: Number of evaluation episodes
        
    Returns:
        Evaluation metrics
    """
    logger.info(f"Evaluating agent for {n_episodes} episodes")
    
    total_rewards = []
    sharpe_ratios = []
    
    for episode in range(n_episodes):
        obs = env.reset()
        episode_reward = 0
        done = False
        
        while not done:
            action, _states = model.predict(obs, deterministic=True)
            obs, reward, done, info = env.step(action)
            episode_reward += reward[0]
        
        total_rewards.append(episode_reward)
        
        # Get episode summary from environment
        # Note: Need to access underlying env, not vecenv
        summary = env.envs[0].get_episode_summary()
        sharpe_ratios.append(summary['sharpe_ratio'])
        
        logger.info(f"Episode {episode+1}: Reward={episode_reward:.2f}, Sharpe={summary['sharpe_ratio']:.2f}")
    
    return {
        'mean_reward': np.mean(total_rewards),
        'std_reward': np.std(total_rewards),
        'mean_sharpe': np.mean(sharpe_ratios),
        'total_episodes': n_episodes
    }

def main():
    """Main training script."""
    # Configuration
    SYMBOL = 'XAUUSD'
    TIMEFRAME = 'H1'
    TOTAL_TIMESTEPS = 100000
    
    # Load configs
    config = load_config()
    agent_config = config['ppo_agent']
    
    # Prepare data
    data = prepare_data(SYMBOL, TIMEFRAME)
    
    # Split train/test (80/20)
    train_size = int(len(data) * 0.8)
    train_data = data[:train_size]
    test_data = data[train_size:]
    
    logger.info(f"Train size: {len(train_data)}, Test size: {len(test_data)}")
    
    # Train agent
    model = train_ppo_agent(
        symbol=SYMBOL,
        data=train_data,
        config=agent_config,
        total_timesteps=TOTAL_TIMESTEPS
    )
    
    # Evaluate on test data
    test_env = create_env(SYMBOL, test_data, agent_config)
    eval_results = evaluate_agent(model, test_env, n_episodes=10)
    
    logger.info("Evaluation Results:")
    logger.info(f"  Mean Reward: {eval_results['mean_reward']:.2f}")
    logger.info(f"  Mean Sharpe: {eval_results['mean_sharpe']:.2f}")
    
    # Final message
    logger.info(f"Training complete for {SYMBOL}")
    logger.info(f"Model saved to: models/checkpoints/{SYMBOL}_ppo_final.zip")

if __name__ == '__main__':
    main()
```

Run with:
```powershell
python mtquant/agents/training/train_ppo.py
```

Configuration file needed - create config/agents.yaml:
```yaml
ppo_agent:
  initial_capital: 10000
  transaction_cost: 0.003
  learning_rate: 0.0003
  n_steps: 2048
  batch_size: 64
  gamma: 0.99
  gae_lambda: 0.95
  ent_coef: 0.01
  clip_range: 0.2
  max_grad_norm: 0.5
```