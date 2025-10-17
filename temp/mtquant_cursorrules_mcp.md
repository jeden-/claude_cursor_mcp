---
alwaysApply: true
---
# MTQuant Project Rules - MCP Architecture

## 🎯 Project Context

You are working on **MTQuant** - a production-grade multi-agent AI trading system using Reinforcement Learning with **Model Context Protocol (MCP) integration** for broker connectivity.

### Core Technologies
- **Backend**: Python 3.11+, FastAPI, FinRL, Stable Baselines3
- **Broker Integration**: MCP (Model Context Protocol) - NO direct MetaTrader5 package import
- **Frontend**: React 18+, TypeScript, Tailwind CSS, TradingView Lightweight Charts
- **Databases**: QuestDB (time-series), PostgreSQL (transactional), Redis (hot data)
- **MCP Servers**: 
  - MT5: Qoyyuum/mcp-metatrader5-server (stdio-based, FastMCP)
  - MT4: 8nite/metatrader-4-mcp (HTTP-based, Node.js)
- **Deployment**: Docker, docker-compose

### System Architecture
- **Multi-Agent**: Independent RL agents per instrument (XAUUSD, BTCUSD, USDJPY, EURUSD, etc.)
- **Centralized Risk**: Risk Manager coordinates all agents, enforces portfolio-level limits
- **Hybrid Design**: RL generates signals, rule-based systems handle position sizing & risk
- **MCP Integration**: All broker operations through MCP protocol (never direct imports)
- **Production Focus**: Safety-first, regulatory-compliant, audit-ready

### Target Use Cases
- Live trading (primary), paper trading (validation), backtesting (development)
- Day trading, swing trading, position trading (configurable per agent)
- Multi-broker support (MT4/MT5 through MCP abstraction)

---

## 🚨 CRITICAL MCP INTEGRATION RULES

### NEVER Import MetaTrader5 Directly in Application Code

**❌ FORBIDDEN:**
```python
import MetaTrader5 as MT5  # NEVER DO THIS IN mtquant/

class MT5Client:
    def connect(self):
        MT5.initialize()  # WRONG - violates MCP architecture
        MT5.login(...)
```

**✅ CORRECT - Use MCP Protocol:**
```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MT5MCPClient:
    """Client communicates with MT5 via MCP server process."""
    
    def __init__(self, broker_id: str, config: Dict):
        self.server_params = StdioServerParameters(
            command="uv",
            args=["run", "--directory", config['mcp_server_path'], "mt5mcp"],
            env={
                "MT5_ACCOUNT": str(config['account']),
                "MT5_PASSWORD": config['password'],
                "MT5_SERVER": config['server']
            }
        )
    
    async def connect(self) -> bool:
        """Connect to MCP server process."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                
                # Call MCP tools
                result = await session.call_tool("initialize", arguments={})
                
                login_result = await session.call_tool(
                    "login",
                    arguments={
                        "account": self.config['account'],
                        "password": self.config['password'],
                        "server": self.config['server']
                    }
                )
                return "success" in login_result.content[0].text.lower()
```

### MCP Architecture Layers

```
MTQuant Application (Python)
    ↓ (MCP Protocol)
MCP Server Process
    ├── MT5 Server (stdio-based, FastMCP)
    │   ↓ (MetaTrader5 Python package)
    │   MT5 Terminal
    │
    └── MT4 Server (HTTP-based, Node.js)
        ↓ (File I/O with Expert Advisor)
        MT4 Terminal
```

**Key Points:**
- MCP servers run as **separate processes**
- MT5 server: Started with `uv run mt5mcp dev`
- MT4 server: Started with `npm start` (Node.js)
- Application communicates via **MCP protocol only**
- MetaTrader5 package is **ONLY used inside MCP server**, never in application

---

## 🚨 CRITICAL SAFETY REQUIREMENTS

### Trading System Safety (HIGHEST PRIORITY)

**NEVER execute trades without:**
1. ✅ Pre-trade risk validation (capital, limits, price sanity)
2. ✅ Position size calculation (Kelly Criterion, volatility-based, or fixed fractional)
3. ✅ Stop-loss and take-profit defined
4. ✅ Transaction cost inclusion (0.2-0.3% minimum)
5. ✅ Audit logging (who, what, when, why)
6. ✅ MCP server health check (verify connection alive)

**Example pattern to ALWAYS follow:**
```python
async def execute_trade(order: Order) -> TradeResult:
    """Execute trade with full safety checks.
    
    SAFETY CHECKLIST:
    - MCP server health check ✓
    - Pre-trade validation ✓
    - Position sizing ✓
    - Risk limits ✓
    - Audit logging ✓
    """
    # 0. Verify MCP connection
    if not await mcp_client.health_check():
        raise BrokerConnectionError("MCP server not responding")
    
    # 1. Pre-trade validation
    await pre_trade_checker.validate(order)
    
    # 2. Position sizing with risk consideration
    position_size = position_sizer.calculate(
        signal=order.signal,
        portfolio_equity=portfolio.equity,
        instrument_volatility=market_data.atr
    )
    
    # 3. Risk checks
    if not risk_manager.check_limits(position_size):
        raise RiskViolationError("Position exceeds limits")
    
    # 4. Execute via MCP
    try:
        result = await broker_adapter.place_order(order)
    except BrokerError as e:
        logger.error(f"MCP order failed: {e}")
        await alert_manager.send_critical_alert(e)
        raise
    finally:
        # 5. Audit trail
        await audit_logger.log_trade(order, result)
    
    return result
```

### Risk Management Rules
- **Pre-trade checks**: Execute in <50ms
  - Price bands validation (±5-10% from last known)
  - Position size limits (<5% Average Daily Volume)
  - Capital verification (sufficient margin available)
  - Regulatory compliance (max leverage, instrument restrictions)

- **Circuit breakers**: Three-tier automatic halt
  - Level 1 (5% daily loss): Warning alerts, reduce position sizes
  - Level 2 (10% daily loss): Halt new positions, close risky positions
  - Level 3 (15-20% daily loss): Full trading halt, flatten all positions

- **Portfolio limits**:
  - Max total exposure: 120-150% gross exposure
  - Max per instrument: 10-15% of portfolio
  - Correlation monitoring: reduce positions if ρ > 0.7 between agents
  - Max daily loss: 5% (configurable in risk-limits.yaml)

### Error Handling Patterns

**MCP Communication:**
```python
async def mcp_operation() -> Result:
    max_retries = 3
    retry_delay = 1.0  # seconds
    
    for attempt in range(max_retries):
        try:
            # All MCP calls with timeout
            result = await asyncio.wait_for(
                session.call_tool(tool_name, arguments=args),
                timeout=5.0
            )
            return result
            
        except asyncio.TimeoutError as e:
            logger.warning(f"MCP timeout (attempt {attempt+1}/{max_retries}): {e}")
            await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
            
        except ConnectionError as e:
            logger.error(f"MCP connection lost: {e}")
            await restart_mcp_server()
            
        except Exception as e:
            logger.exception("Unexpected MCP error")
            raise BrokerAPIError(f"MCP tool failed: {e}")
    
    raise BrokerError(f"MCP operation failed after {max_retries} attempts")
```

---

## 🏗️ Architecture Patterns

### 1. MCP Integration Layer

**MCP Client Pattern (MANDATORY):**
```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import Optional, Dict, List
import asyncio

class BaseMCPClient(ABC):
    """Base class for all MCP broker clients."""
    
    def __init__(self, broker_id: str, config: Dict):
        self.broker_id = broker_id
        self.config = config
        self.session: Optional[ClientSession] = None
        self.logger = get_logger(__name__)
    
    @abstractmethod
    def _get_server_params(self) -> StdioServerParameters:
        """Return MCP server parameters."""
        pass
    
    async def connect(self) -> bool:
        """Connect to MCP server."""
        try:
            params = self._get_server_params()
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    self.session = session
                    return await self._initialize_connection()
        except Exception as e:
            logger.exception("MCP connection failed")
            raise BrokerConnectionError(f"Failed to connect: {e}")
    
    async def _initialize_connection(self) -> bool:
        """Initialize broker connection via MCP tools."""
        # Implementation specific to MT5/MT4
        pass
    
    async def health_check(self) -> bool:
        """Check if MCP connection is alive."""
        if not self.session:
            return False
        
        try:
            # Quick MCP tool call to verify connection
            result = await asyncio.wait_for(
                self.session.call_tool("get_symbols", arguments={}),
                timeout=2.0
            )
            return True
        except Exception:
            return False

class MT5MCPClient(BaseMCPClient):
    """MT5 MCP client using stdio communication."""
    
    def _get_server_params(self) -> StdioServerParameters:
        return StdioServerParameters(
            command="uv",
            args=[
                "run",
                "--directory", self.config['mcp_server_path'],
                "mt5mcp"
            ],
            env={
                "MT5_ACCOUNT": str(self.config['account']),
                "MT5_PASSWORD": self.config['password'],
                "MT5_SERVER": self.config['server']
            }
        )
    
    async def get_market_data(self, symbol: str, timeframe: str, bars: int) -> pd.DataFrame:
        """Fetch OHLCV via MCP."""
        if not self.session:
            raise BrokerConnectionError("Not connected to MCP server")
        
        try:
            result = await asyncio.wait_for(
                self.session.call_tool(
                    "copy_rates_from_pos",
                    arguments={
                        "symbol": symbol,
                        "timeframe": self._timeframe_to_mt5(timeframe),
                        "start_pos": 0,
                        "count": bars
                    }
                ),
                timeout=5.0
            )
            
            # Parse MCP response
            import json
            data = json.loads(result.content[0].text)
            return pd.DataFrame(data)
            
        except asyncio.TimeoutError:
            raise BrokerTimeoutError("MCP tool timeout")
        except Exception as e:
            raise MarketDataError(f"Failed to fetch data via MCP: {e}")

class MT4MCPClient(BaseMCPClient):
    """MT4 MCP client using HTTP communication."""
    
    def __init__(self, broker_id: str, config: Dict):
        super().__init__(broker_id, config)
        self.base_url = config.get('mcp_endpoint', 'http://localhost:3000')
        self.http_client = httpx.AsyncClient(timeout=10.0)
    
    async def connect(self) -> bool:
        """Connect to MT4 HTTP MCP server."""
        try:
            response = await self.http_client.post(
                f"{self.base_url}/initialize",
                json={
                    "account": self.config['account'],
                    "password": self.config['password'],
                    "server": self.config['server']
                }
            )
            response.raise_for_status()
            return response.json().get('status') == 'success'
        except Exception as e:
            raise BrokerConnectionError(f"MT4 MCP connection failed: {e}")
```

**Broker Adapter Pattern (wraps MCP clients):**
```python
class BrokerAdapter(ABC):
    """Unified interface for all brokers (MT5/MT4)."""
    
    @abstractmethod
    async def connect(self) -> bool:
        pass
    
    @abstractmethod
    async def place_order(self, order: Order) -> str:
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        pass
    
    @abstractmethod
    async def get_market_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        pass

class MT5BrokerAdapter(BrokerAdapter):
    """MT5 adapter with symbol mapping and validation."""
    
    def __init__(self, broker_id: str, config: Dict):
        self.broker_id = broker_id
        self.mcp_client = MT5MCPClient(broker_id, config)  # MCP client
        self.symbol_mapper = SymbolMapper
        self.logger = get_logger(__name__)
    
    async def place_order(self, order: Order) -> str:
        """Place order with symbol mapping."""
        # 1. Map standard symbol to broker symbol
        broker_symbol = self.symbol_mapper.to_broker_symbol(
            order.symbol, self.broker_id
        )
        
        # 2. Create order with broker symbol
        broker_order = order.copy()
        broker_order.symbol = broker_symbol
        
        # 3. Place via MCP client
        order_id = await self.mcp_client.place_order(broker_order)
        
        # 4. Log for audit
        self.logger.info(
            f"Order via MCP: {order_id} | {order.symbol}->{broker_symbol}"
        )
        
        return order_id
```

**Symbol Mapping (centralized):**
```python
class SymbolMapper:
    """Centralized symbol mapping: standard ↔ broker-specific."""
    
    SYMBOL_MAP = {
        'XAUUSD': {
            'oanda': 'GOLD.pro',
            'ic_markets': 'XAUUSD',
            'exness': 'XAUUSDm',
        },
        # ... complete mapping
    }
    
    @classmethod
    def to_broker_symbol(cls, standard: str, broker_id: str) -> str:
        """Convert standard symbol to broker-specific."""
        return cls.SYMBOL_MAP[standard][broker_id]
    
    @classmethod
    def to_standard_symbol(cls, broker_symbol: str, broker_id: str) -> str:
        """Reverse lookup: broker-specific → standard."""
        for standard, mappings in cls.SYMBOL_MAP.items():
            if mappings.get(broker_id) == broker_symbol:
                return standard
        raise SymbolNotFoundError(f"Unknown: {broker_symbol} @ {broker_id}")
```

### 2. RL Agent Structure

**State Space Design:**
```python
class AgentState:
    """RL agent state representation."""
    
    def __init__(self, market_data: pd.DataFrame, position: Position):
        # ✅ CORRECT: Use log returns (stationary)
        self.log_returns = np.log(market_data['close'] / market_data['close'].shift(1))
        
        # ✅ Normalized technical indicators
        self.rsi = self._normalize(market_data['rsi'], 0, 100)
        self.macd = self._normalize(market_data['macd'], -5, 5)
        
        # ✅ Position state
        self.holdings = position.quantity / max_position_size
        self.unrealized_pnl = position.unrealized_pnl / portfolio_equity
        self.position_age = min(position.duration_hours / 24, 1.0)
        
        # ✅ Risk metrics
        self.portfolio_volatility = portfolio.rolling_volatility(20)
        self.current_drawdown = portfolio.drawdown_pct
        
        # ❌ NEVER use raw prices (non-stationary)
        # self.price = market_data['close']  # DON'T DO THIS!
```

**Reward Function:**
```python
def calculate_reward(
    returns: float,
    risk_free_rate: float,
    downside_volatility: float,
    transaction_cost: float
) -> float:
    """Risk-adjusted reward (Sortino ratio - transaction costs)."""
    sortino = (returns - risk_free_rate) / downside_volatility
    cost_penalty = transaction_cost * 100
    return sortino - cost_penalty
```

### 3. Risk Management Architecture

**Multi-layered Defense:**
```python
class RiskManager:
    """Three-tier risk management."""
    
    def __init__(self):
        self.pre_trade_checker = PreTradeChecker()
        self.intra_trade_monitor = IntraTradeMonitor()
        self.portfolio_controller = PortfolioController()
        self.circuit_breaker = CircuitBreaker()
    
    async def validate_trade(self, order: Order) -> ValidationResult:
        """Layer 1: Pre-trade checks (<50ms)."""
        checks = [
            self.pre_trade_checker.validate_price(order.price),
            self.pre_trade_checker.validate_position_size(order.quantity),
            self.pre_trade_checker.validate_capital(order.required_margin),
            self.pre_trade_checker.validate_regulatory(order),
        ]
        return all(checks)
```

---

## 💻 Code Standards

### Python (Backend)

**Type Hints (MANDATORY):**
```python
from typing import Optional, List, Dict, Union, Literal
from dataclasses import dataclass
from datetime import datetime

# ✅ Use Python 3.11+ union syntax
def process_order(order: Order | None) -> str | None:
    pass

# ✅ Dataclasses for models
@dataclass
class Position:
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    opened_at: datetime
    agent_id: str
```

**Async/Await for ALL I/O Operations:**
```python
# ✅ Async for MCP operations
async def fetch_via_mcp(symbol: str) -> pd.DataFrame:
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            result = await session.call_tool("copy_rates_from_pos", ...)
            return pd.DataFrame(...)

# ✅ Async database operations
async def save_trade(trade: Trade):
    async with db_pool.acquire() as conn:
        await conn.execute("INSERT INTO trades ...")

# ❌ DON'T block event loop
def bad_fetch():
    response = requests.get("...")  # Blocking!
```

---

## 🧪 Testing Requirements

### Integration Tests (MCP)
```python
import pytest
from mtquant.mcp_integration.clients.mt5_mcp_client import MT5MCPClient

@pytest.fixture
async def mt5_mcp_client():
    """MCP client fixture - requires MCP server running."""
    config = {
        'mcp_server_path': os.getenv('MT5_MCP_SERVER_PATH'),
        'account': int(os.getenv('MT5_DEMO_ACCOUNT')),
        'password': os.getenv('MT5_DEMO_PASSWORD'),
        'server': os.getenv('MT5_DEMO_SERVER')
    }
    
    client = MT5MCPClient('ic_markets_demo', config)
    
    # Start MCP server and connect
    connected = await client.connect()
    assert connected, "Failed to connect to MCP server"
    
    yield client
    
    # Cleanup
    await client.disconnect()

@pytest.mark.asyncio
@pytest.mark.integration
async def test_mcp_market_data(mt5_mcp_client):
    """Test fetching market data through MCP."""
    data = await mt5_mcp_client.get_market_data('EURUSD', 'H1', bars=50)
    
    assert not data.empty
    assert len(data) == 50
    assert 'close' in data.columns

@pytest.mark.asyncio
@pytest.mark.integration
async def test_mcp_connection_resilience(mt5_mcp_client):
    """Test MCP reconnection after server restart."""
    # Simulate server failure
    # ... test reconnection logic
```

**Coverage Requirements:**
- Minimum 70% overall coverage
- 100% coverage for risk management code
- 90%+ coverage for MCP client code
- Run: `pytest --cov=mtquant --cov-report=html`

---

## 🔒 Security & Compliance

### Credential Management
```python
# ✅ Use environment variables
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    mt5_mcp_server_path: str
    mt5_account: int
    mt5_password: str
    mt5_server: str
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

settings = Settings()
```

### Audit Logging
```python
class AuditLogger:
    """Comprehensive audit trail for regulatory compliance."""
    
    async def log_mcp_trade(self, order: Order, result: TradeResult):
        """Log every trade with MCP server info."""
        await db.execute("""
            INSERT INTO audit_log (
                event_type, user_id, agent_id, symbol,
                action, mcp_server, details, timestamp
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
        """, 
            'TRADE_EXECUTED_VIA_MCP', 
            "system", 
            order.agent_id, 
            order.symbol,
            f"{order.side} {order.quantity} @ {order.price}",
            result.mcp_server_id,
            json.dumps({
                'order': order.dict(),
                'result': result.dict(),
                'broker': result.broker_id
            })
        )
```

---

## 📁 File Structure Awareness

```
mtquant/
├── mtquant/
│   ├── mcp_integration/        # MCP-specific code
│   │   ├── clients/
│   │   │   ├── mt5_mcp_client.py    # MT5 via MCP
│   │   │   ├── mt4_mcp_client.py    # MT4 via MCP
│   │   │   └── base_client.py
│   │   ├── adapters/           # Broker adapters
│   │   │   ├── mt5_adapter.py
│   │   │   └── mt4_adapter.py
│   │   └── managers/
│   │       ├── broker_manager.py
│   │       ├── connection_pool.py
│   │       └── symbol_mapper.py
│   ├── agents/
│   ├── risk_management/
│   └── utils/
├── mcp_servers/                # MCP server installations
│   ├── mt5/
│   │   └── server/             # Qoyyuum/mcp-metatrader5-server
│   └── mt4/
│       └── server/             # 8nite/metatrader-4-mcp
└── config/
    ├── brokers.yaml            # Includes mcp_server_path
    └── symbols.yaml
```

---

## 🎯 When Suggesting Code

**Always consider:**
1. ✅ **MCP integration** - Is this communicating through MCP or direct import?
2. ✅ **Safety implications** - Is this safe for live trading with real money?
3. ✅ **Error handling** - What if MCP server crashes? Connection lost?
4. ✅ **Type hints** - Are all parameters and returns properly typed?
5. ✅ **Logging** - Will we know what happened if MCP fails?
6. ✅ **Testing** - How can this be tested? MCP mocks needed?
7. ✅ **Performance** - Is this async where needed? MCP latency acceptable?
8. ✅ **Security** - Any credential exposure? MCP server authentication?

**Ask clarifying questions when:**
- MCP server setup unclear ("Which MCP server version?")
- Trading logic ambiguous ("What should happen if MCP timeout?")
- Risk parameters undefined ("What's the max MCP reconnection attempts?")
- Performance requirements vague ("What's acceptable MCP latency?")

**Suggest improvements when:**
- Direct MetaTrader5 import detected (suggest MCP client)
- Missing MCP health checks
- Lack of MCP retry logic
- Synchronous code that should be async
- Missing MCP server lifecycle management

---

## 📝 MCP Server Management

**Always ensure MCP servers are running:**

```python
class MCPServerManager:
    """Manage MCP server lifecycle."""
    
    async def start_mt5_server(self, server_path: str):
        """Start MT5 MCP server process."""
        process = await asyncio.create_subprocess_exec(
            "uv", "run", "--directory", server_path, "mt5mcp", "dev",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for server ready
        await asyncio.sleep(2)
        return process
    
    async def health_check_server(self, client: BaseMCPClient) -> bool:
        """Check if MCP server is responsive."""
        try:
            return await asyncio.wait_for(client.health_check(), timeout=2.0)
        except asyncio.TimeoutError:
            return False
    
    async def restart_server_on_failure(self, server_path: str):
        """Automatic restart on MCP server crash."""
        self.logger.warning("MCP server crashed, restarting...")
        await self.start_mt5_server(server_path)
```

---

## 🚀 Quick Reference Commands

**Development:**
```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start MCP servers (REQUIRED)
cd mcp_servers/mt5/server && uv run mt5mcp dev  # Terminal 1
cd mcp_servers/mt4/server && npm start          # Terminal 2

# Run tests
pytest tests/ -v --cov=mtquant

# Run backend
uvicorn api.main:app --reload --port 8000

# Type checking
mypy mtquant/
```

---

**Remember**: 
- **NEVER import MetaTrader5 directly** in application code
- **ALL broker operations** go through MCP protocol
- **MCP servers must be running** before starting application
- **Test on demo accounts** with MCP servers first
- When in doubt about MCP integration - ask before implementing! 🛡️