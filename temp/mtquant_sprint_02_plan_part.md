# MTQuant Sprint 2 - Risk Management & First RL Agent

**Duration:** 7-8 dni (full-time work)  
**Goal:** Kompletny system zarządzania ryzykiem + pierwszy działający RL agent (PPO) dla XAUUSD + multi-broker support

---

## Sprint Overview

### Objectives
1. **Risk Management System** - 3-warstwowa obrona (pre-trade, intra-trade, circuit breakers)
2. **First RL Agent** - PPO agent dla XAUUSD z trading environment
3. **Multi-Broker Support** - MT4 MCP Client + BrokerManager z intelligent routing
4. **Connection Pool** - Health monitoring z automatic failover
5. **End-to-End Test** - Agent → Risk Manager → BrokerManager → MCP → MT5 → Order execution

### Prerequisites
- ✅ Sprint 1 completed (MCP integration działa)
- Python 3.11.9 zainstalowany
- MT5 MCP server działający
- Demo account credentials
- Git configured

### Architecture After Sprint 2

```
RL Agent (PPO)
    ↓ (generates signals)
Risk Manager
    ├── PreTradeChecker (<50ms)
    ├── PositionSizer (Kelly/Volatility)
    └── CircuitBreaker (3-tier)
    ↓ (validated orders)
Broker Manager
    ├── Connection Pool
    │   ├── MT5 Adapter → MT5 MCP Client → MT5 Terminal
    │   └── MT4 Adapter → MT4 MCP Client → MT4 Terminal
    └── Symbol Mapper
```

---

## DAY 1 - Risk Management Foundation

### Task 1.1: PreTradeChecker Implementation (90 min)

**Cursor AI Prompt:**
```
Implement mtquant/risk_management/pre_trade_checker.py for pre-trade risk validation.

This runs BEFORE every order execution. Must execute in <50ms.

Required imports:
```python
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from mtquant.utils.logger import get_logger
from mtquant.utils.exceptions import (
    RiskViolationError,
    PositionSizeError,
    InsufficientMarginError
)
```

Class: PreTradeChecker

Initialization:
```python
class PreTradeChecker:
    """
    Pre-trade risk validation system.
    
    Executes 6 validation checks in parallel:
    1. Price bands (±5-10% from last known)
    2. Position size limits (<5% ADV)
    3. Capital verification (sufficient margin)
    4. Portfolio exposure limits
    5. Regulatory compliance
    6. Correlation risk
    
    Target execution time: <50ms
    """
    
    def __init__(self, risk_limits: Dict):
        """
        Args:
            risk_limits: Loaded from config/risk-limits.yaml
        """
        self.limits = risk_limits
        self.logger = get_logger(__name__)
```

Core Method:
```python
async def validate(
    self, 
    order: Order, 
    portfolio: Dict,
    current_positions: List[Position],
    last_price: float
) -> ValidationResult:
    """
    Comprehensive pre-trade validation.
    
    Args:
        order: Order to validate
        portfolio: Current portfolio state (equity, positions, etc.)
        current_positions: List of open positions
        last_price: Last known market price for instrument
        
    Returns:
        ValidationResult with:
            - is_valid: bool
            - checks_passed: List[str]
            - checks_failed: List[str]
            - error_message: Optional[str]
            - execution_time_ms: float
            
    Runs all checks in parallel for speed.
    """
    start_time = asyncio.get_event_loop().time()
    
    # Run all checks in parallel
    checks = await asyncio.gather(
        self.check_price_band(order, last_price),
        self.check_position_size(order, portfolio),
        self.check_capital_availability(order, portfolio),
        self.check_portfolio_exposure(order, current_positions, portfolio),
        self.check_regulatory_limits(order),
        self.check_correlation_risk(order, current_positions),
        return_exceptions=True
    )
    
    # Process results
    checks_passed = []
    checks_failed = []
    
    for i, result in enumerate(checks):
        check_name = [
            'price_band', 'position_size', 'capital', 
            'exposure', 'regulatory', 'correlation'
        ][i]
        
        if isinstance(result, Exception):
            checks_failed.append(f"{check_name}: {str(result)}")
        else:
            checks_passed.append(check_name)
    
    execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
    
    is_valid = len(checks_failed) == 0
    
    if not is_valid:
        error_msg = f"Validation failed: {', '.join(checks_failed)}"
        self.logger.warning(error_msg)
    
    return ValidationResult(
        is_valid=is_valid,
        checks_passed=checks_passed,
        checks_failed=checks_failed,
        error_message=error_msg if not is_valid else None,
        execution_time_ms=execution_time
    )
```

Validation Methods:
```python
async def check_price_band(self, order: Order, last_price: float) -> bool:
    """
    Validate price is within reasonable band.
    
    Check: |order.price - last_price| / last_price <= price_band_pct
    
    Returns: True if valid
    Raises: ValueError if price outside band
    """
    if order.price is None:  # Market order
        return True
    
    price_band_pct = self.limits['pre_trade_checks']['price_band_pct']
    deviation = abs(order.price - last_price) / last_price
    
    if deviation > price_band_pct:
        raise ValueError(
            f"Price {order.price} deviates {deviation:.1%} from last {last_price} "
            f"(max {price_band_pct:.1%})"
        )
    
    return True

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
    limits = self.limits['position_sizing']
    
    # Min size check
    if order.quantity < limits['min_position_size']:
        raise PositionSizeError(
            f"Position {order.quantity} below minimum {limits['min_position_size']}"
        )
    
    # Max size as % of portfolio
    max_size = portfolio['equity'] * limits['max_position_size_pct']
    position_value = order.quantity * (order.price or 1.0)
    
    if position_value > max_size:
        raise PositionSizeError(
            f"Position ${position_value:.2f} exceeds max {limits['max_position_size_pct']:.1%} "
            f"of portfolio (${max_size:.2f})"
        )
    
    # TODO: Add ADV check when market data available
    
    return True

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
    # Calculate required margin (simplified - assumes 1:50 leverage)
    leverage = 50  # TODO: Get from instrument specs
    price = order.price or portfolio.get('last_prices', {}).get(order.symbol, 0)
    required_margin = (order.quantity * price) / leverage
    
    free_margin = portfolio.get('free_margin', 0)
    
    if required_margin > free_margin:
        raise InsufficientMarginError(
            f"Required margin ${required_margin:.2f} exceeds free margin ${free_margin:.2f}"
        )
    
    # Also check min account balance
    min_balance = self.limits['pre_trade_checks']['min_account_balance']
    if portfolio.get('balance', 0) < min_balance:
        raise InsufficientMarginError(
            f"Account balance ${portfolio['balance']:.2f} below minimum ${min_balance:.2f}"
        )
    
    return True

async def check_portfolio_exposure(
    self,
    order: Order,
    current_positions: List[Position],
    portfolio: Dict
) -> bool:
    """
    Check total portfolio exposure limits.
    
    Checks:
    - Total exposure (current + new order) <= max_total_exposure_pct
    - Sector/asset class exposure <= max_sector_exposure_pct
    
    Returns: True if within limits
    Raises: RiskViolationError if exceeds exposure limits
    """
    limits = self.limits['portfolio_limits']
    
    # Calculate current total exposure
    current_exposure = sum(
        abs(pos.quantity * pos.current_price) 
        for pos in current_positions
    )
    
    # Add new order exposure
    new_order_exposure = order.quantity * (order.price or 0)
    total_exposure = current_exposure + new_order_exposure
    
    max_exposure = portfolio['equity'] * limits['max_total_exposure_pct']
    
    if total_exposure > max_exposure:
        raise RiskViolationError(
            f"Total exposure ${total_exposure:.2f} exceeds max {limits['max_total_exposure_pct']:.1%} "
            f"of portfolio (${max_exposure:.2f})"
        )
    
    # TODO: Add sector/asset class exposure check
    
    return True

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
    # TODO: Implement based on jurisdiction
    # For now, simple leverage check
    
    max_leverage = self.limits['pre_trade_checks']['max_leverage']
    # Placeholder - actual implementation depends on instrument specs
    
    return True

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
    # TODO: Implement correlation matrix lookup
    # For now, simple symbol check (same symbol = high correlation)
    
    max_correlation = self.limits['portfolio_limits']['max_correlation_threshold']
    
    # Check if we already have position in same symbol
    for pos in current_positions:
        if pos.symbol == order.symbol:
            # Same symbol - check if adding or closing
            same_side = (
                (pos.side == 'long' and order.side == 'buy') or
                (pos.side == 'short' and order.side == 'sell')
            )
            
            if same_side:
                self.logger.warning(
                    f"Adding to existing {pos.side} position in {order.symbol}"
                )
    
    return True
```

Helper Class:
```python
@dataclass
class ValidationResult:
    """Result of pre-trade validation."""
    is_valid: bool
    checks_passed: List[str]
    checks_failed: List[str]
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    
    def __str__(self) -> str:
        status = "VALID" if self.is_valid else "INVALID"
        return (
            f"Validation {status} ({self.execution_time_ms:.1f}ms)\n"
            f"Passed: {', '.join(self.checks_passed)}\n"
            f"Failed: {', '.join(self.checks_failed) if self.checks_failed else 'None'}"
        )
```

Implementation Notes:
- Run checks in parallel with asyncio.gather()
- Target execution time: <50ms
- Log all failures (WARNING level)
- Log passes (DEBUG level)
- Include timing in ValidationResult

Type hints, comprehensive docstrings, error handling per .cursorrules.
```

**Manual Test:**
```python
# Test in Python REPL
python

import asyncio
from mtquant.risk_management.pre_trade_checker import PreTradeChecker
from mtquant.mcp_integration.models.order import Order
from mtquant.mcp_integration.models.position import Position
import yaml

# Load risk limits
with open('config/risk-limits.yaml') as f:
    risk_limits = yaml.safe_load(f)

checker = PreTradeChecker(risk_limits)

# Create test order
order = Order(
    agent_id='test_agent',
    symbol='XAUUSD',
    side='buy',
    order_type='market',
    quantity=0.1,
    price=2050.0,
    signal=0.8
)

# Test portfolio state
portfolio = {
    'equity': 50000,
    'balance': 50000,
    'used_margin': 5000,
    'free_margin': 45000
}

# Test validation
async def test():
    result = await checker.validate(
        order=order,
        portfolio=portfolio,
        current_positions=[],
        last_price=2050.5
    )
    
    print(result)
    assert result.is_valid
    assert result.execution_time_ms < 50

asyncio.run(test())
```

**Verification:**
- [ ] PreTradeChecker class implemented
- [ ] All 6 validation methods present
- [ ] ValidationResult dataclass defined
- [ ] Checks run in parallel (asyncio.gather)
- [ ] Execution time <50ms
- [ ] Type hints and docstrings complete
- [ ] Manual test passes

---

### Task 1.2: PositionSizer Implementation (75 min)

**Cursor AI Prompt:**
```
Implement mtquant/risk_management/position_sizer.py for intelligent position sizing.

Supports multiple strategies: Kelly Criterion, Volatility-based, Fixed Fractional.

Required imports:
```python
from typing import Literal, Optional
from mtquant.utils.logger import get_logger
```

Class: PositionSizer

Initialization:
```python
class PositionSizer:
    """
    Position sizing with multiple strategies.
    
    Methods:
    - Kelly Criterion (fractional)
    - Volatility-based (ATR)
    - Fixed fractional
    
    All methods scale by signal strength.
    """
    
    def __init__(self, config: Dict):
        """
        Args:
            config: Position sizing configuration
                - method: 'kelly' | 'volatility' | 'fixed'
                - risk_per_trade: float (e.g., 0.02 for 2%)
                - kelly_fraction: float (e.g., 0.25 for quarter Kelly)
                - max_position_size: float (cap in USD)
        """
        self.config = config
        self.logger = get_logger(__name__)
```

Core Method:
```python
async def calculate(
    self,
    signal: float,
    portfolio_equity: float,
    instrument_volatility: float,
    win_rate: Optional[float] = None,
    avg_win: Optional[float] = None,
    avg_loss: Optional[float] = None,
    method: Optional[Literal['kelly', 'volatility', 'fixed']] = None
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
    1. Validate inputs
    2. Calculate base size using selected method
    3. Scale by signal strength (abs(signal))
    4. Apply max position limit
    5. Return final size
    """
    # Validate inputs
    self.validate_inputs(signal, portfolio_equity, instrument_volatility)
    
    # Determine method
    method = method or self.config.get('method', 'volatility')
    
    # Calculate base size
    if method == 'kelly':
        if not all([win_rate, avg_win, avg_loss]):
            raise ValueError("Kelly requires win_rate, avg_win, avg_loss")
        base_size = self._kelly_criterion(
            win_rate, avg_win, avg_loss, portfolio_equity
        )
    elif method == 'volatility':
        base_size = self._volatility_based(
            self.config['risk_per_trade'],
            portfolio_equity,
            instrument_volatility
        )
    elif method == 'fixed':
        base_size = self._fixed_fractional(
            self.config['risk_per_trade'],
            portfolio_equity
        )
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Scale by signal strength
    scaled_size = self._apply_signal_scaling(base_size, signal)
    
    # Apply limits
    final_size = self._apply_limits(
        scaled_size,
        self.config.get('max_position_size', float('inf'))
    )
    
    self.logger.debug(
        f"Position size: {final_size:.4f} "
        f"(method={method}, signal={signal:.2f}, base={base_size:.4f})"
    )
    
    return final_size
```

Strategy Methods:
```python
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
    # Full Kelly percentage
    kelly_pct = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_loss
    
    # Apply fractional Kelly for safety
    kelly_fraction = self.config.get('kelly_fraction', 0.25)
    fractional_kelly = kelly_pct * kelly_fraction
    
    # Cap at max Kelly percentage
    max_kelly = self.config.get('max_kelly_pct', 0.05)
    fractional_kelly = min(fractional_kelly, max_kelly)
    
    position_size = portfolio_equity * fractional_kelly
    
    return position_size

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
        
    Returns: Position size in lots
    """
    if volatility <= 0:
        raise ValueError(f"Volatility must be > 0, got {volatility}")
    
    # Risk amount in USD
    risk_amount = portfolio_equity * risk_per_trade
    
    # Stop-loss distance
    stop_distance = volatility * atr_multiplier
    
    # Position size = Risk / Stop Distance
    position_size = risk_amount / stop_distance
    
    return position_size

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
        
    Returns: Position size in USD
    """
    return portfolio_equity * fraction

def _apply_signal_scaling(self, base_size: float, signal: float) -> float:
    """
    Scale position by signal strength.
    
    If signal = 0.5 (weak), use 50% of calculated size.
    If signal = 1.0 (strong), use 100% of calculated size.
    
    Returns: Scaled position size
    """
    return base_size * abs(signal)

def _apply_limits(self, size: float, max_size: float) -> float:
    """
    Apply max position limit.
    
    Ensures: size <= max_size
    Returns: Capped position size
    """
    return min(size, max_size)
```

Validation:
```python
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
    if not -1 <= signal <= 1:
        raise ValueError(f"Signal must be -1 to 1, got {signal}")
    
    if portfolio_equity <= 0:
        raise ValueError(f"Portfolio equity must be > 0, got {portfolio_equity}")
    
    if volatility <= 0:
        raise ValueError(f"Volatility must be > 0, got {volatility}")
```

Implementation notes:
- Type hints for all methods
- Docstrings with formulas
- Comprehensive logging (DEBUG for calculations)
- Error handling for edge cases
```

**Manual Test:**
```python
# Test position sizer
python

from mtquant.risk_management.position_sizer import PositionSizer

# Test configuration
config = {
    'method': 'volatility',
    'risk_per_trade': 0.02,
    'kelly_fraction': 0.25,
    'max_position_size': 10000.0
}

sizer = PositionSizer(config)

# Test volatility-based
import asyncio

async def test():
    size = await sizer.calculate(
        signal=0.8,  # Strong buy signal
        portfolio_equity=50000,
        instrument_volatility=20.5,
        method='volatility'
    )
    
    print(f"Position size: {size:.4f} lots")
    assert size > 0
    assert size <= config['max_position_size']

asyncio.run(test())
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

### Task 1.3: CircuitBreaker Implementation (60 min)

**Cursor AI Prompt:**
```
Implement mtquant/risk_management/circuit_breaker.py for automatic trading halts.

Three-tier circuit breaker system following .cursorrules specification.

Required imports:
```python
import asyncio
from enum import Enum
from typing import Optional, Dict
from datetime import datetime, timedelta
from mtquant.utils.logger import get_logger
from mtquant.utils.exceptions import CircuitBreakerError
```

Status Enum:
```python
class CircuitBreakerStatus(Enum):
    """Circuit breaker status levels."""
    NORMAL = "normal"
    LEVEL_1 = "level_1_warning"
    LEVEL_2 = "level_2_reduce"
    LEVEL_3 = "level_3_halt"
```

Class: CircuitBreaker

Initialization:
```python
class CircuitBreaker:
    """
    Three-tier automatic trading halt system.
    
    Levels:
    - Level 1 (5% daily loss): Warning, reduce position sizes 25%
    - Level 2 (10% daily loss): Halt new positions, close risky positions
    - Level 3 (15-20% daily loss): FULL HALT, flatten all positions
    """
    
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
```

Core Method:
```python
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
    # Determine new status
    if daily_pnl_pct <= -self.config['level_3_loss_pct']:
        new_status = CircuitBreakerStatus.LEVEL_3
        new_level = 3
    elif daily_pnl_pct <= -self.config['level_2_loss_pct']:
        new_status = CircuitBreakerStatus.LEVEL_2
        new_level = 2
    elif daily_pnl_pct <= -self.config['level_1_loss_pct']:
        new_status = CircuitBreakerStatus.LEVEL_1
        new_level = 1
    else:
        new_status = CircuitBreakerStatus.NORMAL
        new_level = 0
    
    # Check if status changed
    if new_status != self.status:
        old_status = self.status
        self.status = new_status
        self.trigger_level = new_level if new_level > 0 else None
        
        if new_level > 0:
            self.triggered_at = datetime.now()
            
            # Log trigger
            self._log_trigger(new_level, daily_pnl_pct)
            
            # Send alerts
            await self._send_alert(new_level, daily_pnl_pct, portfolio)
            
            # Execute level actions
            if new_level == 1:
                await self.level_1_activate()
            elif new_level == 2:
                await self.level_2_activate()
            elif new_level == 3:
                await self.level_3_activate()
        else:
            # Returning to normal
            self.logger.info(f"Circuit breaker reset: {old_status} -> NORMAL")
    
    return self.status
```

Level Actions:
```python
async def level_1_activate(self) -> None:
    """
    Level 1: Warning (5% daily loss)
    
    Actions:
    - Send WARNING alerts to monitoring
    - Log event
    - Reduce position sizes by 25%
    - No trading halt
    """
    self.logger.warning("Circuit Breaker LEVEL 1: Warning (5% daily loss)")
    
    # TODO: Implement position size reduction
    # For now, just log
    self.logger.warning("Action: Reduce position sizes by 25%")

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
    self.logger.error("Circuit Breaker LEVEL 2: Reduce (10% daily loss)")
    
    # TODO: Implement:
    # - Halt new positions
    # - Close risky positions
    # - Reduce sizes by 50%
    self.logger.error("Action: HALT new positions, close risky positions")

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
    self.logger.critical("Circuit Breaker LEVEL 3: FULL HALT (15% daily loss)")
    
    # TODO: Implement:
    # - Stop all agents
    # - Flatten all positions
    # - Lock system
    self.logger.critical("Action: HALT ALL TRADING, FLATTEN ALL POSITIONS")
```

Reset Method:
```python
async def reset(self) -> bool:
    """
    Reset circuit breaker to NORMAL.
    
    Conditions:
    - Can only reset if cooldown period elapsed
    - Requires manual confirmation (safety)
    
    Returns: True if reset successful
    Raises: CircuitBreakerError if reset not allowed
    """
    if self.status == CircuitBreakerStatus.NORMAL:
        self.logger.warning("Circuit breaker already NORMAL, no reset needed")
        return True
    
    # Check cooldown
    if not self._is_cooldown_elapsed():
        cooldown_mins = self.config['cooldown_minutes']
        elapsed = (datetime.now() - self.triggered_at).total_seconds() / 60
        raise CircuitBreakerError(
            f"Cannot reset: cooldown not elapsed "
            f"({elapsed:.0f}/{cooldown_mins} minutes)"
        )
    
    # Reset
    old_status = self.status
    self.status = CircuitBreakerStatus.NORMAL
    self.triggered_at = None
    self.trigger_level = None
    
    self.logger.info(f"Circuit breaker RESET: {old_status} -> NORMAL")
    
    return True

async def can_trade(self) -> bool:
    """
    Check if trading is allowed.
    
    Returns:
        - True if NORMAL or LEVEL_1
        - False if LEVEL_2 or LEVEL_3
    """
    return self.status in [CircuitBreakerStatus.NORMAL, CircuitBreakerStatus.LEVEL_1]
```

Helper Methods:
```python
def _is_cooldown_elapsed(self) -> bool:
    """Check if cooldown period has elapsed since trigger."""
    if not self.triggered_at:
        return True
    
    cooldown = timedelta(minutes=self.config['cooldown_minutes'])
    return datetime.now() >= self.triggered_at + cooldown

async def _send_alert(self, level: int, daily_pnl_pct: float, portfolio: Dict) -> None:
    """Send alert via monitoring system (placeholder for now)."""
    message = (
        f"Circuit Breaker Level {level} TRIGGERED\n"
        f"Daily P&L: {daily_pnl_pct:.2%}\n"
        f"Portfolio Equity: ${portfolio.get('equity', 0):.2f}"
    )
    
    # TODO: Integrate with alert system (email, SMS, Discord)
    self.logger.warning(f"ALERT: {message}")

def _log_trigger(self, level: int, daily_pnl_pct: float) -> None:
    """
    Log circuit breaker trigger with full context.
    """
    log_method = {
        1: self.logger.warning,
        2: self.logger.error,
        3: self.logger.critical
    }[level]
    
    log_method(
        f"Circuit Breaker Level {level} TRIGGERED: "
        f"Daily P&L {daily_pnl_pct:.2%} "
        f"(threshold: -{self.config[f'level_{level}_loss_pct']:.1%})"
    )

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
    report = {
        'status': self.status.value,
        'triggered_at': self.triggered_at,
        'trigger_level': self.trigger_level,
        'can_trade': await self.can_trade()
    }
    
    if self.triggered_at:
        elapsed = (datetime.now() - self.triggered_at).total_seconds() / 60
        report['time_since_trigger_mins'] = elapsed
        report['can_reset'] = self._is_cooldown_elapsed()
    else:
        report['time_since_trigger_mins'] = None
        report['can_reset'] = False
    
    return report
```

Implementation notes:
- Thread-safe (use asyncio.Lock for status changes)
- Comprehensive logging at each trigger
- Alert placeholders (implement with alert system later)
- Status persists until manual reset
- Type hints, docstrings everywhere
```

**Manual Test:**
```python
# Test circuit breaker
python

import asyncio
from mtquant.risk_management.circuit_breaker import CircuitBreaker, CircuitBreakerStatus

config = {
    'level_1_loss_pct': 0.05,
    'level_2_loss_pct': 0.10,
    'level_3_loss_pct': 0.15,
    'cooldown_minutes': 60
}

breaker = CircuitBreaker(config)

portfolio = {'equity': 48000, 'start_equity': 50000}

async def test():
    # Test Level 1
    status = await breaker.check(daily_pnl_pct=-0.06, portfolio=portfolio)
    assert status == CircuitBreakerStatus.LEVEL_1
    assert await breaker.can_trade() == True
    
    # Test Level 2
    status = await breaker.check(daily_pnl_pct=-0.11, portfolio=portfolio)
    assert status == CircuitBreakerStatus.LEVEL_2
    assert await breaker.can_trade() == False
    
    # Test Level 3
    status = await breaker.check(daily_pnl_pct=-0.16, portfolio=portfolio)
    assert status == CircuitBreakerStatus.LEVEL_3
    assert await breaker.can_trade() == False
    
    # Get status report
    report = await breaker.get_status_report()
    print(f"Status: {report['status']}")
    print(f"Can trade: {report['can_trade']}")

asyncio.run(test())
```

**Verification:**
- [ ] CircuitBreaker class implemented
- [ ] CircuitBreakerStatus enum defined
- [ ] Three-tier logic (5%/10%/15%) works
- [ ] Level 1: Warning + log
- [ ] Level 2: Halt new + log
- [ ] Level 3: FULL HALT + log
- [ ] Reset requires cooldown elapsed
- [ ] Status tracking and reporting works
- [ ] Manual test passes

---

### Task 1.4: Day 1 Commit (15 min)

```powershell
git add .
git commit -m "feat: risk management foundation

- PreTradeChecker with 6-layer validation (<50ms)
- PositionSizer with Kelly, volatility, and fixed methods
- CircuitBreaker with 3-tier halt system (5%/10%/15%)
- Signal-based position scaling
- Comprehensive error handling
- Unit test infrastructure

Sprint 2, Day 1 complete"
```

---

## DAY 2 - Risk Management Testing

### Task 2.1: Unit Tests for Risk Management (90 min)

**Cursor AI Prompt:**
```
Create tests/unit/test_risk_management.py for risk management unit tests.

Test all three components: PreTradeChecker, PositionSizer, CircuitBreaker.

Mock data - no external dependencies.

Required imports:
```python
import pytest
import asyncio
from datetime import datetime, timedelta
from mtquant.risk_management.pre_trade_checker import PreTradeChecker, ValidationResult
from mtquant.risk_management.position_sizer import PositionSizer
from mtquant.risk_management.circuit_breaker import CircuitBreaker, CircuitBreakerStatus
from mtquant.mcp_integration.models.order import Order
from mtquant.mcp_integration.models.position import Position
from mtquant.utils.exceptions import (
    RiskViolationError,
    PositionSizeError,
    InsufficientMarginError
)
```

Fixtures:
```python
@pytest.fixture
def risk_limits():
    """Risk limits configuration."""
    return {
        'position_sizing': {
            'min_position_size': 0.01,
            'max_position_size_pct': 0.10,
            'max_position_size': 100.0
        },
        'pre_trade_checks': {
            'price_band_pct': 0.10,
            'min_account_balance': 1000.0,
            'max_leverage': 50
        },
        'portfolio_limits': {
            'max_total_exposure_pct': 1.50,
            'max_sector_exposure_pct': 0.40,
            'max_correlation_threshold': 0.7
        },
        'circuit_breaker': {
            'level_1_loss_pct': 0.05,
            'level_2_loss_pct': 0.10,
            'level_3_loss_pct': 0.15,
            'cooldown_minutes': 60
        }
    }

@pytest.fixture
def portfolio():
    """Test portfolio state."""
    return {
        'equity': 50000,
        'balance': 50000,
        'used_margin': 5000,
        'free_margin': 45000,
        'start_equity': 50000
    }

@pytest.fixture
def test_order():
    """Test order."""
    return Order(
        order_id=None,
        agent_id='test_agent',
        symbol='XAUUSD',
        side='buy',
        order_type='market',
        quantity=0.1,
        price=2050.0,
        stop_loss=2000.0,
        take_profit=2100.0,
        signal=0.8,
        created_at=datetime.now(),
        status='pending'
    )
```

PreTradeChecker Tests:
```python
@pytest.mark.asyncio
async def test_price_band_validation(risk_limits, test_order):
    """Test price must be within ±10% of last known price."""
    checker = PreTradeChecker(risk_limits)
    
    # Valid price (within band)
    result = await checker.check_price_band(test_order, last_price=2050.0)
    assert result is True
    
    # Invalid price (outside band)
    with pytest.raises(ValueError):
        await checker.check_price_band(test_order, last_price=1500.0)

@pytest.mark.asyncio
async def test_position_size_limits(risk_limits, test_order, portfolio):
    """Test position size limits enforced."""
    checker = PreTradeChecker(risk_limits)
    
    # Within limits
    result = await checker.check_position_size(test_order, portfolio)
    assert result is True
    
    # Exceeds max size
    large_order = Order(
        agent_id='test',
        symbol='XAUUSD',
        side='buy',
        order_type='market',
        quantity=10.0,  # Large position
        price=2050.0,
        signal=1.0,
        created_at=datetime.now(),
        status='pending'
    )
    
    with pytest.raises(PositionSizeError):
        await checker.check_position_size(large_order, portfolio)

@pytest.mark.asyncio
async def test_capital_availability(risk_limits, test_order, portfolio):
    """Test sufficient margin check."""
    checker = PreTradeChecker(risk_limits)
    
    # Sufficient margin
    result = await checker.check_capital_availability(test_order, portfolio)
    assert result is True
    
    # Insufficient margin
    broke_portfolio = portfolio.copy()
    broke_portfolio['free_margin'] = 10.0
    
    with pytest.raises(InsufficientMarginError):
        await checker.check_capital_availability(test_order, broke_portfolio)

@pytest.mark.asyncio
async def test_comprehensive_validation(risk_limits, test_order, portfolio):
    """Test full validation with all checks."""
    checker = PreTradeChecker(risk_limits)
    
    # All checks pass
    result = await checker.validate(
        order=test_order,
        portfolio=portfolio,
        current_positions=[],
        last_price=2050.0
    )
    
    assert isinstance(result, ValidationResult)
    assert result.is_valid is True
    assert result.execution_time_ms < 50
    assert len(result.checks_passed) == 6
    assert len(result.checks_failed) == 0
```

PositionSizer Tests:
```python
def test_kelly_criterion():
    """Test Kelly Criterion calculation."""
    config = {
        'method': 'kelly',
        'kelly_fraction': 0.25,
        'max_kelly_pct': 0.05,
        'max_position_size': 10000.0
    }
    
    sizer = PositionSizer(config)
    
    # With 60% win rate, avg win 100, avg loss 50
    # Expected: Kelly% = (0.6*100 - 0.4*50)/50 = 0.8
    # Fractional (0.25x) = 0.2
    # Capped at max_kelly_pct = 0.05
    
    size = sizer._kelly_criterion(
        win_rate=0.6,
        avg_win=100,
        avg_loss=50,
        portfolio_equity=50000
    )
    
    # Should be capped at 5% = 2500
    assert size == 50000 * 0.05

def test_volatility_based_sizing():
    """Test volatility-based position sizing."""
    config = {
        'method': 'volatility',
        'risk_per_trade': 0.02,
        'max_position_size': 10000.0
    }
    
    sizer = PositionSizer(config)
    
    # Portfolio: $50k, Risk: 2%, ATR: 20
    # Expected: (50000 * 0.02) / (20 * 2) = 25
    
    size = sizer._volatility_based(
        risk_per_trade=0.02,
        portfolio_equity=50000,
        volatility=20.0,
        atr_multiplier=2.0
    )
    
    assert size == 25.0

@pytest.mark.asyncio
async def test_signal_scaling():
    """Test position scaled by signal strength."""
    config = {
        'method': 'fixed',
        'risk_per_trade': 0.02,
        'max_position_size': 10000.0
    }
    
    sizer = PositionSizer(config)
    
    # Base size with signal = 1.0
    full_size = await sizer.calculate(
        signal=1.0,
        portfolio_equity=50000,
        instrument_volatility=20.0,
        method='fixed'
    )
    
    # Half size with signal = 0.5
    half_size = await sizer.calculate(
        signal=0.5,
        portfolio_equity=50000,
        instrument_volatility=20.0,
        method='fixed'
    )
    
    assert abs(half_size - full_size / 2) < 0.01

@pytest.mark.asyncio
async def test_position_limits_applied():
    """Test max position limit enforced."""
    config = {
        'method': 'fixed',
        'risk_per_trade': 0.10,  # 10% - large
        'max_position_size': 3000.0  # Cap at $3k
    }
    
    sizer = PositionSizer(config)
    
    size = await sizer.calculate(
        signal=1.0,
        portfolio_equity=50000,
        instrument_volatility=20.0,
        method='fixed'
    )
    
    # Should be capped at max_position_size
    assert size == 3000.0
```

CircuitBreaker Tests:
```python
@pytest.mark.asyncio
async def test_circuit_breaker_levels(risk_limits, portfolio):
    """Test circuit breaker triggers at correct levels."""
    breaker = CircuitBreaker(risk_limits['circuit_breaker'])
    
    # -3% loss -> NORMAL
    status = await breaker.check(-0.03, portfolio)
    assert status == CircuitBreakerStatus.NORMAL
    
    # -6% loss -> LEVEL_1
    status = await breaker.check(-0.06, portfolio)
    assert status == CircuitBreakerStatus.LEVEL_1
    
    # -11% loss -> LEVEL_2
    status = await breaker.check(-0.11, portfolio)
    assert status == CircuitBreakerStatus.LEVEL_2
    
    # -16% loss -> LEVEL_3
    status = await breaker.check(-0.16, portfolio)
    assert status == CircuitBreakerStatus.LEVEL_3

@pytest.mark.asyncio
async def test_circuit_breaker_reset(risk_limits):
    """Test reset conditions."""
    breaker = CircuitBreaker(risk_limits['circuit_breaker'])
    
    # Trigger Level 3
    await breaker.check(-0.16, {'equity': 42000})
    assert breaker.status == CircuitBreakerStatus.LEVEL_3
    
    # Cannot reset immediately
    from mtquant.utils.exceptions import CircuitBreakerError
    with pytest.raises(CircuitBreakerError):
        await breaker.reset()
    
    # Simulate cooldown elapsed
    breaker.triggered_at = datetime.now() - timedelta(minutes=61)
    
    # Can reset now
    result = await breaker.reset()
    assert result is True
    assert breaker.status == CircuitBreakerStatus.NORMAL

@pytest.mark.asyncio
async def test_trading_allowed(risk_limits, portfolio):
    """Test can_trade() logic."""
    breaker = CircuitBreaker(risk_limits['circuit_breaker'])
    
    # NORMAL -> True
    assert await breaker.can_trade() is True
    
    # LEVEL_1 -> True (warning only)
    await breaker.check(-0.06, portfolio)
    assert await breaker.can_trade() is True
    
    # LEVEL_2 -> False (halt new positions)
    await breaker.check(-0.11, portfolio)
    assert await breaker.can_trade() is False
    
    # LEVEL_3 -> False (full halt)
    await breaker.check(-0.16, portfolio)
    assert await breaker.can_trade() is False
```

Run with:
```bash
pytest tests/unit/test_risk_management.py -v --cov=mtquant/risk_management
```
```

**Manual Steps:**
```powershell
# Run unit tests
pytest tests/unit/test_risk_management.py -v --cov=mtquant/risk_management

# Expected output:
# test_price_band_validation PASSED
# test_position_size_limits PASSED
# test_capital_availability PASSED
# test_comprehensive_validation PASSED
# test_kelly_criterion PASSED
# test_volatility_based_sizing PASSED
# test_signal_scaling PASSED
# test_position_limits_applied PASSED
# test_circuit_breaker_levels PASSED
# test_circuit_breaker_reset PASSED
# test_trading_allowed PASSED
# 
# Coverage: >80%
```

**Verification:**
- [ ] All PreTradeChecker tests pass
- [ ] All PositionSizer tests pass
- [ ] All CircuitBreaker tests pass
- [ ] Coverage >80% for risk_management module
- [ ] No external dependencies in unit tests
- [ ] All tests run in <10 seconds

---

### Task 2.2: Day 2 Commit (15 min)

```powershell
git add .
git commit -m "test: comprehensive unit tests for risk management

- PreTradeChecker tests (price, size, capital, exposure)
- PositionSizer tests (Kelly, volatility, fixed, scaling)
- CircuitBreaker tests (levels, reset, trading allowed)
- 11+ tests passing
- Coverage >80% for risk_management module

Sprint 2, Day 2 complete"
```

---

## DAY 3-4 - First RL Agent (PPO)

### Task 3.1: Trading Environment (FinRL-compatible) (120 min)

**[Day 3 continues with RL agent implementation...]**

---

## Sprint 2 Timeline Summary

| Day | Tasks | Deliverables |
|-----|-------|--------------|
| 1 | Risk Management Foundation | PreTradeChecker, PositionSizer, CircuitBreaker |
| 2 | Unit Tests | 11+ tests, >80% coverage |
| 3-4 | RL Agent | Trading Environment, PPO Agent, Training |
| 5-6 | Multi-Broker | MT4 Client, BrokerManager, Connection Pool |
| 7 | Integration | End-to-end test, Documentation |
| 8 | Buffer | Bug fixes, polish, Sprint review |

---

## Success Criteria

- [ ] All risk management components working
- [ ] Unit tests >80% coverage
- [ ] First PPO agent trained (XAUUSD)
- [ ] Multi-broker support (MT4 + MT5)
- [ ] Connection pool with failover
- [ ] End-to-end test passing
- [ ] Documentation updated

**END OF SPRINT 2 PREVIEW**

*Full Day 3-8 details available upon request*