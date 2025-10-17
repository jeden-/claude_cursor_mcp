# MTQuant Sprint 1 - Foundation & MCP Integration

**Duration:** 7-10 dni (full-time work)  
**Goal:** Działający system MCP z MT5/MT4 integration, podstawowa struktura projektu, pierwsze testy połączenia z brokerem demo

---

## Sprint Overview

### Objectives
1. Setup kompletnej struktury projektu MTQuant
2. Konfiguracja środowiska Python 3.11 + dependencies
3. **Implementacja MCP Client dla komunikacji z MT5/MT4 servers**
4. Broker Adapter pattern dla MT5 i MT4
5. Symbol Mapper dla mapowania nazw instrumentów
6. Pierwsze testy połączenia z MT5 demo account przez MCP
7. Basic logging i monitoring setup

### Prerequisites
- Python 3.11.9 zainstalowany
- Docker zainstalowany (dla MT4 server)
- Cursor AI skonfigurowany z `.cursorrules`
- Konto demo MT5 (IC Markets, Exness, lub inne)
- Git zainstalowany
- **uv package manager** (`pip install uv`)

### Architektura MCP Integration

```
MTQuant Application (Python)
    ↓ (MCP Protocol - stdio/HTTP)
MCP Server Process
    ├── MT5 Server (Qoyyuum/mcp-metatrader5-server) - Python/FastMCP
    └── MT4 Server (8nite/metatrader-4-mcp) - Node.js/HTTP
        ↓ (MetaTrader5 package / File-based I/O)
MetaTrader 5/4 Terminal
```

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
│   │   │   ├── base_client.py
│   │   │   ├── mt5_mcp_client.py
│   │   │   └── mt4_mcp_client.py
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   ├── base_adapter.py
│   │   │   ├── mt5_adapter.py
│   │   │   └── mt4_adapter.py
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
├── mcp_servers/
│   ├── mt5/
│   │   └── README.md
│   └── mt4/
│       └── README.md
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
- Architecture overview (MCP-based integration)
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
- [ ] Folder `mcp_servers/` utworzony dla MCP server installations
- [ ] Wszystkie `__init__.py` files istnieją
- [ ] `python --version` pokazuje 3.11.9
- [ ] Git repository zainicjowany

---

### Task 1.2: Requirements & Dependencies (45 min)

**Cursor AI Prompt:**
```
Create requirements.txt for MTQuant with MCP integration dependencies.

Pin all versions for reproducibility. Add comments for each section.

Categories and packages:

# Core Framework
fastapi[all]==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0

# MCP Integration (CRITICAL)
mcp==1.0.0
anthropic-sdk==0.18.0

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

# Broker Integration (for MCP servers)
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
uv==0.1.15

# MCP Server Dependencies (install separately in mcp_servers/)
# MT5 Server: mcp-metatrader5-server==0.1.3
# MT4 Server: requires Node.js installation

Also create requirements-dev.txt for development-only dependencies:
- jupyter==1.0.0
- matplotlib==3.8.2
- seaborn==0.13.1
- plotly==5.18.0

Add installation notes:
1. Windows-specific: TA-Lib requires manual .whl installation
2. MCP servers: installed separately in mcp_servers/ directory
3. uv package manager: required for running MCP servers
```

**Manual Steps:**
```powershell
# Instaluj base dependencies
pip install -r requirements.txt

# Instaluj uv (MCP server runner)
pip install uv

# TA-Lib Windows installation (jeśli pip install failuje)
# 1. Download from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
# 2. For Python 3.11 64-bit: TA_Lib‑0.4.28‑cp311‑cp311‑win_amd64.whl
pip install TA_Lib-0.4.28-cp311-cp311-win_amd64.whl

# Weryfikacja instalacji
python -c "import mcp; print('MCP SDK installed')"
python -c "from stable_baselines3 import PPO; print('SB3: OK')"
python -c "import finrl; print('FinRL: OK')"
```

**Verification:**
- [ ] `requirements.txt` utworzony z MCP dependencies
- [ ] `requirements-dev.txt` utworzony
- [ ] Wszystkie packages zainstalowane bez błędów
- [ ] `mcp` package zaimportowany successfully
- [ ] `uv` command dostępny w PATH

---

### Task 1.3: MCP Servers Installation (60 min)

**Cursor AI Prompt:**
```
Create installation scripts and documentation for MCP servers in mcp_servers/ directory.

Create mcp_servers/mt5/README.md with:
```markdown
# MT5 MCP Server Installation

## Overview
Uses [Qoyyuum/mcp-metatrader5-server](https://github.com/Qoyyuum/mcp-metatrader5-server)
- Python-based FastMCP server
- Direct MetaTrader5 package integration
- Tools: initialize, login, shutdown, get_symbols, copy_rates_from_pos, order_send, etc.

## Installation

1. Clone the MCP server:
```bash
cd mcp_servers/mt5
git clone https://github.com/Qoyyuum/mcp-metatrader5-server.git server
cd server
```

2. Install with uv:
```bash
uv run fastmcp install src/mcp_metatrader5_server/server.py
```

3. Test installation:
```bash
uv run mt5mcp dev
# Should start server on http://127.0.0.1:8000
```

## Configuration

Server path for MTQuant: `C:\FULL_PATH\mtquant\mcp_servers\mt5\server`

Environment variables (in .env):
- MT5_DEMO_ACCOUNT
- MT5_DEMO_PASSWORD
- MT5_DEMO_SERVER
```

Create mcp_servers/mt4/README.md with:
```markdown
# MT4 MCP Server Installation

## Overview
Uses [8nite/metatrader-4-mcp](https://github.com/8nite/metatrader-4-mcp)
- Node.js/TypeScript HTTP server
- File-based I/O with MT4 Expert Advisor
- MQL4 EA integration required

## Installation

### Prerequisites
- Node.js 18+ installed
- MetaTrader 4 terminal installed

1. Clone the MCP server:
```bash
cd mcp_servers/mt4
git clone https://github.com/8nite/metatrader-4-mcp.git server
cd server
npm install
```

2. Copy MT4 Expert Advisor:
- Locate: `server/mql4/MCPBridge.mq4`
- Copy to: `C:\Program Files\MetaTrader 4\MQL4\Experts\`
- Compile in MT4 MetaEditor

3. Start HTTP server:
```bash
npm start
# Runs on http://localhost:3000
```

## Configuration

Server endpoint: `http://localhost:3000`
File exchange directory: `C:\Users\%USERNAME%\AppData\Roaming\MetaQuotes\Terminal\<TERMINAL_ID>\MQL4\Files\`
```

**Manual Steps:**
```powershell
# Install MT5 MCP Server
cd mcp_servers\mt5
git clone https://github.com/Qoyyuum/mcp-metatrader5-server.git server
cd server
uv run fastmcp install src\mcp_metatrader5_server\server.py

# Test MT5 server
uv run mt5mcp dev
# Open another terminal, test:
curl http://localhost:8000/health

# Install Node.js for MT4 (download from nodejs.org)
# Then install MT4 server
cd ..\..\mt4
git clone https://github.com/8nite/metatrader-4-mcp.git server
cd server
npm install
npm start
```

**Verification:**
- [ ] MT5 server cloned to `mcp_servers/mt5/server/`
- [ ] MT5 server runs with `uv run mt5mcp dev`
- [ ] MT4 server cloned to `mcp_servers/mt4/server/`
- [ ] Node.js installed, MT4 server runs with `npm start`
- [ ] Both README.md files created with setup instructions

---

### Task 1.4: Configuration Files (45 min)

**Same as original Day 1, Task 1.3 - create:**
- `config/brokers.yaml` (with MCP server paths)
- `config/symbols.yaml`
- `config/risk-limits.yaml`
- `.env.example` (with MCP-specific variables)

**Updated .env.example additions:**
```bash
# MCP Server Paths
MT5_MCP_SERVER_PATH=C:\FULL_PATH\mtquant\mcp_servers\mt5\server
MT4_MCP_SERVER_ENDPOINT=http://localhost:3000

# MT5 MCP Server Credentials
MT5_DEMO_ACCOUNT=YOUR_ACCOUNT_NUMBER
MT5_DEMO_PASSWORD=YOUR_PASSWORD
MT5_DEMO_SERVER=YOUR_SERVER_NAME

# MT4 MCP Server Credentials
MT4_DEMO_ACCOUNT=YOUR_ACCOUNT_NUMBER
MT4_DEMO_PASSWORD=YOUR_PASSWORD
MT4_DEMO_SERVER=YOUR_SERVER_NAME
```

**Verification:**
- [ ] `config/brokers.yaml` includes `mcp_server_path` field
- [ ] `.env` file created with MCP server paths
- [ ] All credential fields populated

---

### Task 1.5: Base Models & Exceptions (45 min)

Same as original Day 1, Task 1.4:
- `mtquant/utils/exceptions.py` - custom exception hierarchy
- `mtquant/mcp_integration/models/order.py` - Order dataclass
- `mtquant/mcp_integration/models/position.py` - Position dataclass
- `mtquant/utils/logger.py` - loguru setup

**Verification:**
- [ ] All base models created with type hints
- [ ] Exception hierarchy complete
- [ ] Logger configured

---

### Task 1.6: First Commit (15 min)

```powershell
git add .
git commit -m "feat: initial MTQuant project structure with MCP integration

- Project folder structure following .cursorrules
- Requirements.txt with MCP SDK dependencies
- MCP servers installed (MT5 + MT4)
- Configuration files with MCP server paths
- Base models (Order, Position) with type hints
- Custom exception hierarchy
- Logger setup with loguru
- .env.example template

Sprint 1, Day 1 complete"
```

---

## DAY 2 - MCP Client Integration

### Task 2.1: SymbolMapper Implementation (60 min)

**Same as original** - no changes needed, load from `config/symbols.yaml`

Create `mtquant/mcp_integration/managers/symbol_mapper.py`

**Verification:**
- [ ] SymbolMapper loads config correctly
- [ ] Bidirectional mapping works (standard ↔ broker)
- [ ] Raises SymbolNotFoundError appropriately

---

### Task 2.2: MT5 MCP Client (120 min)

**Cursor AI Prompt:**
```
Implement mtquant/mcp_integration/clients/mt5_mcp_client.py for MT5 integration through MCP server.

CRITICAL: Use MCP Protocol, NOT direct MetaTrader5 package import.

Required imports:
```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
import pandas as pd
from typing import Optional, Dict, List
from mtquant.utils.logger import get_logger
from mtquant.utils.exceptions import (
    BrokerConnectionError,
    BrokerTimeoutError,
    BrokerAPIError,
    MarketDataError
)
```

Class: MT5MCPClient

Architecture:
```
MT5MCPClient → MCP Protocol (stdio) → MCP Server Process → MetaTrader5 Package → MT5 Terminal
```

Initialization:
```python
class MT5MCPClient:
    """
    MCP Client for MetaTrader 5 integration.
    
    Communicates with mcp-metatrader5-server via MCP protocol.
    Does NOT import MetaTrader5 directly - all operations through MCP tools.
    """
    
    def __init__(self, broker_id: str, config: Dict):
        self.broker_id = broker_id
        self.config = config
        self.logger = get_logger(__name__)
        self.session: Optional[ClientSession] = None
        self.server_params = StdioServerParameters(
            command="uv",
            args=[
                "run",
                "--directory", config['mcp_server_path'],
                "mt5mcp"
            ],
            env={
                "MT5_ACCOUNT": str(config['account']),
                "MT5_PASSWORD": config['password'],
                "MT5_SERVER": config['server']
            }
        )
```

Core Methods:

1. Connection Management:
```python
async def connect(self) -> bool:
    """
    Connect to MCP server and initialize MT5 terminal.
    
    Steps:
    1. Start MCP server process via stdio
    2. Call 'initialize' tool
    3. Call 'login' tool with credentials
    4. Verify connection successful
    
    Returns:
        True if connected successfully
        
    Raises:
        BrokerConnectionError: If connection fails
        BrokerTimeoutError: If login times out
    """
    try:
        # Start MCP server process
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                
                # Initialize MT5
                init_result = await session.call_tool(
                    "initialize",
                    arguments={}
                )
                self.logger.info(f"MT5 initialize: {init_result.content[0].text}")
                
                # Login
                login_result = await session.call_tool(
                    "login",
                    arguments={
                        "account": self.config['account'],
                        "password": self.config['password'],
                        "server": self.config['server']
                    }
                )
                
                response_text = login_result.content[0].text.lower()
                if "success" in response_text or "logged in" in response_text:
                    self.logger.info(f"Connected to MT5: {self.broker_id}")
                    return True
                else:
                    raise BrokerConnectionError(f"Login failed: {response_text}")
                    
    except asyncio.TimeoutError as e:
        raise BrokerTimeoutError(f"Connection timeout: {e}")
    except Exception as e:
        self.logger.exception("MT5 MCP connection error")
        raise BrokerConnectionError(f"Failed to connect: {e}")

async def disconnect(self) -> None:
    """Shutdown MT5 connection via MCP."""
    if self.session:
        try:
            await self.session.call_tool("shutdown", arguments={})
            self.logger.info(f"Disconnected from MT5: {self.broker_id}")
        except Exception as e:
            self.logger.warning(f"Disconnect error (non-fatal): {e}")
        finally:
            self.session = None

async def health_check(self) -> bool:
    """Check if MCP connection is alive."""
    if not self.session:
        return False
    
    try:
        # Try to get symbols as health check
        result = await self.session.call_tool(
            "get_symbols",
            arguments={}
        )
        return "symbols" in result.content[0].text.lower()
    except Exception as e:
        self.logger.warning(f"Health check failed: {e}")
        return False
```

2. Market Data Methods:
```python
async def get_symbols(self) -> List[str]:
    """Get list of available symbols via MCP."""
    if not self.session:
        raise BrokerConnectionError("Not connected")
    
    try:
        result = await self.session.call_tool(
            "get_symbols",
            arguments={}
        )
        # Parse response - format depends on MCP server implementation
        # Expected: comma-separated string or JSON array
        symbols_text = result.content[0].text
        return symbols_text.split(",") if "," in symbols_text else []
    except Exception as e:
        raise MarketDataError(f"Failed to get symbols: {e}")

async def get_market_data(
    self,
    symbol: str,
    timeframe: str = 'H1',
    bars: int = 100
) -> pd.DataFrame:
    """
    Fetch OHLCV data via MCP 'copy_rates_from_pos' tool.
    
    Args:
        symbol: Broker-specific symbol (pre-mapped)
        timeframe: M1, M5, M15, H1, H4, D1
        bars: Number of bars to fetch
        
    Returns:
        DataFrame with columns: time, open, high, low, close, tick_volume, spread, real_volume
    """
    if not self.session:
        raise BrokerConnectionError("Not connected")
    
    # Map timeframe to MT5 constant value
    TIMEFRAME_MAP = {
        'M1': 1, 'M5': 5, 'M15': 15, 'M30': 30,
        'H1': 1*60, 'H4': 4*60, 'D1': 24*60
    }
    
    if timeframe not in TIMEFRAME_MAP:
        raise ValueError(f"Invalid timeframe: {timeframe}")
    
    try:
        result = await self.session.call_tool(
            "copy_rates_from_pos",
            arguments={
                "symbol": symbol,
                "timeframe": TIMEFRAME_MAP[timeframe],
                "start_pos": 0,
                "count": bars
            }
        )
        
        # Parse MCP response into DataFrame
        # Response format: JSON array of OHLCV bars
        import json
        data = json.loads(result.content[0].text)
        df = pd.DataFrame(data)
        
        # Rename columns to standard format
        df.rename(columns={
            'time': 'timestamp',
            'tick_volume': 'volume'
        }, inplace=True)
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        
        self.logger.debug(f"Fetched {len(df)} bars for {symbol} {timeframe}")
        return df
        
    except Exception as e:
        raise MarketDataError(f"Failed to fetch market data: {e}")

async def get_tick_data(self, symbol: str, count: int = 10) -> pd.DataFrame:
    """Get recent tick data via MCP 'get_symbol_info_tick' tool."""
    if not self.session:
        raise BrokerConnectionError("Not connected")
    
    try:
        result = await self.session.call_tool(
            "get_symbol_info_tick",
            arguments={"symbol": symbol}
        )
        
        # Parse tick data
        import json
        tick_data = json.loads(result.content[0].text)
        
        return pd.DataFrame([tick_data])  # Single tick
        
    except Exception as e:
        raise MarketDataError(f"Failed to get tick data: {e}")
```

3. Trading Operations:
```python
async def place_order(self, order: Order) -> str:
    """
    Place order via MCP 'order_send' tool.
    
    Args:
        order: Order object (already validated)
        
    Returns:
        order_id: Broker's order ticket number (as string)
        
    Raises:
        OrderExecutionError: If order fails
    """
    if not self.session:
        raise BrokerConnectionError("Not connected")
    
    from mtquant.utils.exceptions import OrderExecutionError
    
    try:
        # Convert Order to MT5 request format
        mt5_request = {
            "action": "TRADE_ACTION_DEAL",  # Market execution
            "symbol": order.symbol,
            "volume": order.quantity,
            "type": "ORDER_TYPE_BUY" if order.side == "buy" else "ORDER_TYPE_SELL",
            "price": order.price if order.price else 0.0,  # 0 for market orders
            "sl": order.stop_loss if order.stop_loss else 0.0,
            "tp": order.take_profit if order.take_profit else 0.0,
            "deviation": 20,  # Max deviation in points
            "magic": 234000,  # Magic number for identification
            "comment": f"MTQuant-{order.agent_id}",
            "type_time": "ORDER_TIME_GTC",
            "type_filling": "ORDER_FILLING_IOC"
        }
        
        result = await self.session.call_tool(
            "order_send",
            arguments={"request": mt5_request}
        )
        
        # Parse response
        import json
        response = json.loads(result.content[0].text)
        
        if response.get("retcode") == 10009:  # TRADE_RETCODE_DONE
            order_id = str(response.get("order"))
            self.logger.info(f"Order placed: {order_id} - {order.symbol} {order.side} {order.quantity}")
            return order_id
        else:
            error_msg = response.get("comment", "Unknown error")
            raise OrderExecutionError(f"Order rejected: {error_msg}")
            
    except Exception as e:
        self.logger.exception("Order placement error")
        raise OrderExecutionError(f"Failed to place order: {e}")

async def get_positions(self) -> List[Position]:
    """Get open positions via MCP 'positions_get' tool."""
    if not self.session:
        raise BrokerConnectionError("Not connected")
    
    try:
        result = await self.session.call_tool(
            "positions_get",
            arguments={}
        )
        
        import json
        positions_data = json.loads(result.content[0].text)
        
        # Convert to Position objects
        positions = []
        for pos in positions_data:
            position = Position(
                position_id=str(pos['ticket']),
                agent_id="unknown",  # Will be mapped from comment field
                symbol=pos['symbol'],
                side='long' if pos['type'] == 0 else 'short',
                quantity=pos['volume'],
                entry_price=pos['price_open'],
                current_price=pos['price_current'],
                stop_loss=pos.get('sl'),
                take_profit=pos.get('tp'),
                unrealized_pnl=pos['profit'],
                opened_at=pd.to_datetime(pos['time'], unit='s'),
                broker_id=self.broker_id
            )
            positions.append(position)
        
        return positions
        
    except Exception as e:
        self.logger.error(f"Failed to get positions: {e}")
        return []

async def close_position(self, position_id: str) -> bool:
    """Close position via MCP order_send (reverse order)."""
    # Implementation: send opposite order to close
    # Similar to place_order but with opposite side
    pass

async def get_account_info(self) -> Dict:
    """Get account info via MCP 'account_info' tool."""
    if not self.session:
        raise BrokerConnectionError("Not connected")
    
    try:
        result = await self.session.call_tool(
            "account_info",
            arguments={}
        )
        
        import json
        account_data = json.loads(result.content[0].text)
        
        return {
            'balance': account_data['balance'],
            'equity': account_data['equity'],
            'margin': account_data['margin'],
            'free_margin': account_data['margin_free'],
            'profit': account_data['profit'],
            'leverage': account_data['leverage']
        }
        
    except Exception as e:
        self.logger.error(f"Failed to get account info: {e}")
        return {}
```

Implementation Notes:
- NEVER import MetaTrader5 directly - all operations through MCP
- Use asyncio.timeout for all MCP calls (5 second default)
- Parse MCP tool responses (usually JSON strings)
- Comprehensive error handling with custom exceptions
- Log all operations (DEBUG for data, INFO for trades)
- Type hints for all methods
- Docstrings for all public methods

Error Handling Pattern:
```python
try:
    result = await asyncio.wait_for(
        self.session.call_tool(tool_name, arguments=args),
        timeout=5.0
    )
    # Parse and return
except asyncio.TimeoutError:
    raise BrokerTimeoutError(f"{tool_name} timed out")
except Exception as e:
    self.logger.exception(f"MCP tool error: {tool_name}")
    raise BrokerAPIError(f"{tool_name} failed: {e}")
```
```

**Manual Steps - Test MCP Client:**
```powershell
# Start MT5 MCP server (separate terminal)
cd mcp_servers\mt5\server
uv run mt5mcp dev

# Test in Python (main terminal)
python

import asyncio
from mtquant.mcp_integration.clients.mt5_mcp_client import MT5MCPClient

config = {
    'mcp_server_path': r'C:\FULL_PATH\mtquant\mcp_servers\mt5\server',
    'account': 12345678,
    'password': 'yourpass',
    'server': 'ICMarkets-Demo'
}

client = MT5MCPClient('ic_markets_demo', config)

# Test connection
async def test():
    connected = await client.connect()
    print(f"Connected: {connected}")
    
    # Get symbols
    symbols = await client.get_symbols()
    print(f"Symbols: {symbols[:5]}")
    
    # Get market data
    data = await client.get_market_data('EURUSD', 'H1', bars=10)
    print(data.head())
    
    # Disconnect
    await client.disconnect()

asyncio.run(test())
```

**Verification:**
- [ ] MT5MCPClient class implemented
- [ ] Uses MCP SDK (NO direct MetaTrader5 import)
- [ ] All methods async with proper error handling
- [ ] MCP server starts and accepts connections
- [ ] Can initialize and login to MT5 demo
- [ ] Can fetch market data through MCP
- [ ] Comprehensive logging present

---

### Task 2.3: MT4 MCP Client (90 min)

**Cursor AI Prompt:**
```
Implement mtquant/mcp_integration/clients/mt4_mcp_client.py for MT4 integration.

MT4 uses HTTP-based MCP server (Node.js), NOT stdio like MT5.

Architecture:
```
MT4MCPClient → HTTP Requests → MT4 MCP Server (Node.js) → File I/O → MT4 Expert Advisor → MT4 Terminal
```

Required imports:
```python
import httpx
import asyncio
import pandas as pd
from typing import Optional, Dict, List
from mtquant.utils.logger import get_logger
from mtquant.utils.exceptions import (
    BrokerConnectionError,
    BrokerAPIError,
    MarketDataError
)
```

Class: MT4MCPClient

Initialization:
```python
class MT4MCPClient:
    """
    MCP Client for MetaTrader 4 integration.
    
    Communicates with metatrader-4-mcp server via HTTP/REST API.
    Uses file-based exchange with MT4 Expert Advisor.
    """
    
    def __init__(self, broker_id: str, config: Dict):
        self.broker_id = broker_id
        self.config = config
        self.logger = get_logger(__name__)
        self.base_url = config.get('mcp_endpoint', 'http://localhost:3000')
        self.client = httpx.AsyncClient(timeout=10.0)
```

Core Methods (similar structure to MT5 but HTTP-based):
```python
async def connect(self) -> bool:
    """
    Connect to MT4 via HTTP MCP server.
    
    Steps:
    1. POST /initialize with credentials
    2. Verify response
    3. Wait for MT4 EA to confirm connection
    """
    try:
        response = await self.client.post(
            f"{self.base_url}/initialize",
            json={
                "account": self.config['account'],
                "password": self.config['password'],
                "server": self.config['server']
            }
        )
        response.raise_for_status()
        
        result = response.json()
        if result.get('status') == 'success':
            self.logger.info(f"Connected to MT4: {self.broker_id}")
            return True
        else:
            raise BrokerConnectionError(f"MT4 init failed: {result.get('message')}")
            
    except httpx.HTTPError as e:
        raise BrokerConnectionError(f"HTTP error: {e}")

async def get_market_data(
    self,
    symbol: str,
    timeframe: str = 'H1',
    bars: int = 100
) -> pd.DataFrame:
    """Fetch OHLCV via HTTP GET /market_data/<symbol>."""
    try:
        response = await self.client.get(
            f"{self.base_url}/market_data/{symbol}",
            params={'timeframe': timeframe, 'bars': bars}
        )
        response.raise_for_status()
        
        data = response.json()
        df = pd.DataFrame(data['bars'])
        
        return df
        
    except Exception as e:
        raise MarketDataError(f"Failed to fetch data: {e}")

# ... similar methods for trading, positions, account_info
```

Implementation Notes:
- HTTP-based communication (not stdio)
- Higher latency than MT5 MCP (file-based I/O)
- Requires MT4 terminal with Expert Advisor running
- Polling interval: 100-500ms for file checks
- More error-prone - implement robust retry logic
```

**Verification:**
- [ ] MT4MCPClient implemented with HTTP client
- [ ] Can connect to Node.js MCP server
- [ ] Market data fetch works
- [ ] Error handling for HTTP failures

---

### Task 2.4: Broker Adapters (90 min)

**Cursor AI Prompt:**
```
Implement broker adapters that wrap MCP clients and add symbol mapping.

Create mtquant/mcp_integration/adapters/mt5_adapter.py:

```python
from mtquant.mcp_integration.clients.mt5_mcp_client import MT5MCPClient
from mtquant.mcp_integration.managers.symbol_mapper import SymbolMapper
from mtquant.mcp_integration.models import Order, Position
from mtquant.utils.logger import get_logger

class MT5BrokerAdapter:
    """
    Adapter for MT5 broker with symbol mapping.
    
    Wraps MT5MCPClient and adds:
    - Symbol mapping (standard ↔ broker symbols)
    - Order validation
    - Position conversion
    """
    
    def __init__(self, broker_id: str, config: Dict):
        self.broker_id = broker_id
        self.mcp_client = MT5MCPClient(broker_id, config)
        self.symbol_mapper = SymbolMapper
        self.logger = get_logger(__name__)
    
    async def connect(self) -> bool:
        """Connect to broker via MCP."""
        return await self.mcp_client.connect()
    
    async def disconnect(self) -> None:
        """Disconnect from broker."""
        await self.mcp_client.disconnect()
    
    async def place_order(self, order: Order) -> str:
        """
        Place order with symbol mapping.
        
        Steps:
        1. Map standard symbol to broker symbol
        2. Validate order
        3. Place via MCP client
        4. Log for audit
        """
        # Map symbol
        broker_symbol = self.symbol_mapper.to_broker_symbol(
            order.symbol, self.broker_id
        )
        
        # Create order copy with broker symbol
        broker_order = order.copy()
        broker_order.symbol = broker_symbol
        
        # Place order via MCP
        order_id = await self.mcp_client.place_order(broker_order)
        
        self.logger.info(
            f"Order placed: {order_id} | {order.symbol}->{broker_symbol} | {order.side} {order.quantity}"
        )
        
        return order_id
    
    async def get_positions(self) -> List[Position]:
        """
        Get positions with symbol unmapping.
        
        Maps broker symbols back to standard symbols.
        """
        broker_positions = await self.mcp_client.get_positions()
        
        # Unmap symbols
        for pos in broker_positions:
            try:
                pos.symbol = self.symbol_mapper.to_standard_symbol(
                    pos.symbol, self.broker_id
                )
            except Exception as e:
                self.logger.warning(f"Symbol unmapping failed: {pos.symbol} - {e}")
        
        return broker_positions
    
    async def get_market_data(
        self,
        symbol: str,  # STANDARD symbol
        timeframe: str = 'H1',
        bars: int = 100
    ) -> pd.DataFrame:
        """
        Fetch market data with symbol mapping.
        """
        # Map to broker symbol
        broker_symbol = self.symbol_mapper.to_broker_symbol(symbol, self.broker_id)
        
        # Fetch via MCP
        df = await self.mcp_client.get_market_data(broker_symbol, timeframe, bars)
        
        # Add standard symbol column
        df['standard_symbol'] = symbol
        
        return df
    
    async def health_check(self) -> Dict:
        """Check adapter health."""
        is_connected = await self.mcp_client.health_check()
        
        return {
            'broker_id': self.broker_id,
            'is_connected': is_connected,
            'timestamp': pd.Timestamp.now()
        }
```

Create similar adapter for MT4: `mt4_adapter.py`

Implementation notes:
- Adapters provide unified interface (MT5/MT4 differences hidden)
- Symbol mapping at adapter level
- Position/order conversion
- Health monitoring
```

**Verification:**
- [ ] MT5BrokerAdapter wraps MT5MCPClient
- [ ] MT4BrokerAdapter wraps MT4MCPClient
- [ ] Symbol mapping works in both directions
- [ ] Health check returns status

---

### Task 2.5: Integration Tests (60 min)

**Cursor AI Prompt:**
```
Create tests/integration/test_mcp_integration.py for MCP client testing.

IMPORTANT: These tests require:
1. MT5 terminal running and logged in to demo
2. MT5 MCP server running (uv run mt5mcp dev)

Test Setup:
```python
import pytest
import asyncio
from mtquant.mcp_integration.clients.mt5_mcp_client import MT5MCPClient
from mtquant.mcp_integration.adapters.mt5_adapter import MT5BrokerAdapter
import os
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture
async def mt5_client():
    """Create MT5 MCP client connected to demo."""
    config = {
        'mcp_server_path': os.getenv('MT5_MCP_SERVER_PATH'),
        'account': int(os.getenv('MT5_DEMO_ACCOUNT')),
        'password': os.getenv('MT5_DEMO_PASSWORD'),
        'server': os.getenv('MT5_DEMO_SERVER')
    }
    
    client = MT5MCPClient('ic_markets_demo', config)
    
    # Connect
    connected = await client.connect()
    assert connected, "Failed to connect to MT5 MCP server"
    
    yield client
    
    # Cleanup
    await client.disconnect()

@pytest.fixture
async def mt5_adapter(mt5_client):
    """Create MT5 adapter."""
    config = {
        'mcp_server_path': os.getenv('MT5_MCP_SERVER_PATH'),
        'account': int(os.getenv('MT5_DEMO_ACCOUNT')),
        'password': os.getenv('MT5_DEMO_PASSWORD'),
        'server': os.getenv('MT5_DEMO_SERVER')
    }
    
    adapter = MT5BrokerAdapter('ic_markets', config)
    await adapter.connect()
    
    yield adapter
    
    await adapter.disconnect()
```

Tests:
```python
@pytest.mark.asyncio
async def test_mcp_connection(mt5_client):
    """Test basic MCP connection."""
    health = await mt5_client.health_check()
    assert health is True

@pytest.mark.asyncio
async def test_get_symbols_via_mcp(mt5_client):
    """Test fetching symbols through MCP."""
    symbols = await mt5_client.get_symbols()
    
    assert isinstance(symbols, list)
    assert len(symbols) > 0
    assert 'EURUSD' in symbols or 'EURUSD.pro' in symbols

@pytest.mark.asyncio
async def test_fetch_market_data_via_mcp(mt5_client):
    """Test market data fetch through MCP."""
    data = await mt5_client.get_market_data('EURUSD', 'H1', bars=50)
    
    assert not data.empty
    assert len(data) == 50
    assert 'close' in data.columns
    assert 'timestamp' in data.columns

@pytest.mark.asyncio
async def test_get_account_info_via_mcp(mt5_client):
    """Test account info through MCP."""
    info = await mt5_client.get_account_info()
    
    assert 'balance' in info
    assert 'equity' in info
    assert info['balance'] > 0

@pytest.mark.asyncio
async def test_symbol_mapping_adapter(mt5_adapter):
    """Test symbol mapping in adapter."""
    # Fetch with STANDARD symbol
    data = await mt5_adapter.get_market_data('XAUUSD', 'H1', bars=10)
    
    assert not data.empty
    assert 'standard_symbol' in data.columns
    assert data['standard_symbol'].iloc[0] == 'XAUUSD'

@pytest.mark.asyncio
async def test_adapter_health_check(mt5_adapter):
    """Test adapter health monitoring."""
    health = await mt5_adapter.health_check()
    
    assert health['is_connected'] is True
    assert health['broker_id'] == 'ic_markets'

@pytest.mark.asyncio
async def test_get_positions_via_mcp(mt5_client):
    """Test getting positions (should be empty on fresh demo)."""
    positions = await mt5_client.get_positions()
    
    assert isinstance(positions, list)
    # Fresh demo should have no positions
```

Run tests:
```bash
# Start MT5 MCP server first
cd mcp_servers/mt5/server
uv run mt5mcp dev

# In another terminal, run tests
pytest tests/integration/test_mcp_integration.py -v -s
```
```

**Manual Steps:**
```powershell
# Terminal 1: Start MT5 MCP server
cd mcp_servers\mt5\server
uv run mt5mcp dev

# Terminal 2: Run tests
pytest tests\integration\test_mcp_integration.py -v -s

# Expected output:
# test_mcp_connection PASSED
# test_get_symbols_via_mcp PASSED
# test_fetch_market_data_via_mcp PASSED
# test_get_account_info_via_mcp PASSED
# test_symbol_mapping_adapter PASSED
# test_adapter_health_check PASSED
```

**Verification:**
- [ ] MT5 MCP server running
- [ ] All 6+ integration tests PASS
- [ ] Can fetch market data through MCP
- [ ] Symbol mapping works end-to-end
- [ ] Health checks functional

---

### Task 2.6: Day 2 Commit (15 min)

```powershell
git add .
git commit -m "feat: MCP integration for MT5 and MT4

- MT5MCPClient using MCP SDK (stdio communication)
- MT4MCPClient using HTTP/REST (Node.js server)
- MT5/MT4 BrokerAdapters with symbol mapping
- Integration tests for MCP connections
- Market data fetch through MCP tools
- Health monitoring for MCP servers

Tests: 6/6 passing
Sprint 1, Day 2 complete"
```

---

## DAY 3 - Connection Pool & Broker Manager

### Task 3.1: Connection Pool (60 min)

**Same as original Day 3, Task 3.1** - no changes needed

Create `mtquant/mcp_integration/managers/connection_pool.py`

**Key additions for MCP:**
- Track MCP server process health
- Monitor stdio/HTTP connection status
- Automatic MCP server restart on failure

**Verification:**
- [ ] ConnectionPool manages multiple adapters
- [ ] Health monitoring works
- [ ] Failover logic implemented

---

### Task 3.2: Broker Manager (75 min)

**Same as original Day 3, Task 3.2** - minimal changes

Create `mtquant/mcp_integration/managers/broker_manager.py`

**MCP-specific considerations:**
- Initialize MCP clients (start server processes)
- Handle MCP server lifecycle
- Monitor both MT5 (stdio) and MT4 (HTTP) connections

**Verification:**
- [ ] BrokerManager orchestrates multiple brokers
- [ ] Can place orders through MCP
- [ ] Intelligent routing works

---

### Task 3.3: Integration Tests (45 min)

Create `tests/integration/test_broker_manager.py`

**Key tests:**
- Manager initialization with MCP servers
- Market data fetch through manager
- Multi-broker aggregation
- MCP server failover

**Verification:**
- [ ] All broker manager tests pass
- [ ] MCP servers managed properly
- [ ] Failover works when MCP server stops

---

### Task 3.4: Day 3 Commit (15 min)

```powershell
git add .
git commit -m "feat: broker management layer with MCP lifecycle

- ConnectionPool for MCP server management
- Health monitoring with MCP process tracking
- BrokerManager with MCP-aware routing
- Integration tests for multi-broker MCP setup
- Automatic MCP server restart on failure

Tests: 11/11 passing
Sprint 1, Day 3 complete"
```

---

## DAYS 4-5 - Risk Management Foundation

**NO CHANGES** - Same as original Sprint 1, Days 4-5:

- Task 4.1: PreTradeChecker
- Task 4.2: PositionSizer
- Task 4.3: CircuitBreaker
- Task 4.4: Unit Tests
- Task 4.5: Commit

**Verification:**
- [ ] All risk management components implemented
- [ ] Unit tests pass (>25 tests)
- [ ] Coverage >80%

---

## DAYS 6-7 - First RL Agent & End-to-End Test

**NO CHANGES** - Same as original Sprint 1, Days 6-7:

- Task 6.1: Trading Environment (FinRL)
- Task 6.2: PPO Agent Training Script
- Task 6.3: End-to-End Test
- Task 6.4: Final Commit

**Verification:**
- [ ] Trading environment works
- [ ] PPO agent trains successfully
- [ ] End-to-end test: Agent → BrokerManager → MCP → MT5 → Order Execution

---

## Sprint 1 Summary

### Deliverables
✅ Complete project structure with MCP integration
✅ MT5 MCP Client (stdio-based)
✅ MT4 MCP Client (HTTP-based)
✅ Broker adapters with symbol mapping
✅ Connection pooling with health monitoring
✅ Broker Manager with intelligent routing
✅ Risk management system (3-tier defense)
✅ First RL agent (PPO) with trading environment
✅ Integration tests (11+ passing)
✅ Unit tests (25+ passing, >80% coverage)

### Architecture Achieved

```
MTQuant Application (Python)
    ├── Agent Manager (PPO/SAC agents)
    ├── Risk Manager (Pre-trade, Position Sizer, Circuit Breaker)
    └── Broker Manager
            ├── Connection Pool
            │   ├── MT5 Adapter → MT5 MCP Client → MCP Server → MT5 Terminal
            │   └── MT4 Adapter → MT4 MCP Client → MCP Server → MT4 Terminal
            └── Symbol Mapper (standard ↔ broker symbols)
```

### Next Steps (Sprint 2)
1. Expand to 8 instruments (XAUUSD, BTCUSD, USDJPY, EURUSD, GBPUSD, SPX, ETHUSD, WTI)
2. Multi-agent training (one agent per instrument)
3. Central Risk Manager coordination
4. React UI development (dashboard, charts)
5. WebSocket real-time updates
6. Paper trading validation (30 days)

### Critical Notes
- **MCP Servers MUST be running** for all operations
- MT5 MCP: `uv run mt5mcp dev` (stdio communication)
- MT4 MCP: `npm start` (HTTP communication)
- Always start MCP servers before running application
- Monitor MCP server health (automatic restart on failure)
- Test on demo accounts ONLY during Sprint 1

---

## Troubleshooting MCP Integration

### Issue: MCP Server Won't Start
```powershell
# MT5 Server
cd mcp_servers/mt5/server
uv --version  # Verify uv installed
uv run mt5mcp dev --help  # Test command

# MT4 Server
cd mcp_servers/mt4/server
node --version  # Verify Node.js 18+
npm install  # Re-install dependencies
npm start
```

### Issue: MCP Client Can't Connect
```python
# Test MCP connection manually
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio

async def test_mcp():
    params = StdioServerParameters(
        command="uv",
        args=["run", "--directory", r"C:\FULL_PATH\mcp_servers\mt5\server", "mt5mcp"]
    )
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            result = await session.call_tool("initialize", arguments={})
            print(result.content[0].text)

asyncio.run(test_mcp())
```

### Issue: Symbol Mapping Fails
- Check `config/symbols.yaml` has mapping for broker
- Verify broker_id matches config
- Test with SymbolMapper directly

### Issue: Market Data Empty
- Verify MT5 terminal has symbol loaded
- Check timeframe spelling (H1, not 1H)
- Ensure bars count reasonable (<10000)

---

**END OF SPRINT 1**