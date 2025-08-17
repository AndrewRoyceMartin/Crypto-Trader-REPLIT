"""
Bot pricing formulas from bot.py for accurate buy/sell calculations.
Implements the exact risk-based position sizing used in the bot.
"""

import math
from typing import Tuple, Dict, Optional
from dataclasses import dataclass


@dataclass
class BotParams:
    """Bot parameters matching bot.py configuration"""
    risk_per_trade: float = 0.01    # 1% of equity per trade
    stop_loss_pct: float = 0.01     # 1% stop loss
    take_profit_pct: float = 0.02   # 2% take profit
    fee_rate: float = 0.001         # 0.1% trading fee
    slippage_pct: float = 0.0005    # 0.05% slippage


class BotPricingCalculator:
    """Implements bot.py pricing formulas for position sizing and trade calculations"""
    
    def __init__(self, params: Optional[BotParams] = None):
        self.params = params or BotParams()
    
    def calculate_position_size(self, current_price: float, equity: float) -> Tuple[float, float]:
        """
        Calculate position size using bot.py formula.
        
        Args:
            current_price: Current market price
            equity: Available trading equity
            
        Returns:
            Tuple of (quantity, dollar_amount)
        """
        # Bot.py formula: risk_per_unit = max(1e-12, px * P.sl)
        risk_per_unit = max(1e-12, current_price * self.params.stop_loss_pct)
        
        # Bot.py formula: dollars = P.risk * state.equity
        dollars = self.params.risk_per_trade * equity
        
        # Bot.py formula: raw_qty = max(0.0, dollars / risk_per_unit)
        raw_qty = max(0.0, dollars / risk_per_unit)
        
        return raw_qty, dollars
    
    def calculate_entry_price(self, market_price: float, side: str = 'buy') -> float:
        """
        Calculate entry price with slippage (bot.py: fill_px = nxt_open*(1 + P.slip))
        
        Args:
            market_price: Current market price
            side: 'buy' or 'sell'
            
        Returns:
            Entry price with slippage applied
        """
        if side.lower() == 'buy':
            # Buy higher due to slippage
            return market_price * (1 + self.params.slippage_pct)
        else:
            # Sell lower due to slippage  
            return market_price * (1 - self.params.slippage_pct)
    
    def calculate_stop_take_prices(self, entry_price: float, side: str = 'buy') -> Tuple[float, float]:
        """
        Calculate stop loss and take profit prices using bot.py formulas.
        
        Bot.py formulas:
        - stop = state.entry_price*(1 - P.sl)
        - take = state.entry_price*(1 + P.tp)
        
        Args:
            entry_price: Entry price of the position
            side: 'buy' or 'sell'
            
        Returns:
            Tuple of (stop_loss_price, take_profit_price)
        """
        if side.lower() == 'buy':
            stop_loss = entry_price * (1 - self.params.stop_loss_pct)
            take_profit = entry_price * (1 + self.params.take_profit_pct)
        else:  # sell
            stop_loss = entry_price * (1 + self.params.stop_loss_pct)
            take_profit = entry_price * (1 - self.params.take_profit_pct)
            
        return stop_loss, take_profit
    
    def calculate_pnl(self, entry_price: float, current_price: float, quantity: float, side: str = 'buy') -> Dict[str, float]:
        """
        Calculate PnL with fees using bot.py logic.
        
        Args:
            entry_price: Entry price of position
            current_price: Current market price
            quantity: Position quantity
            side: 'buy' or 'sell'
            
        Returns:
            Dictionary with gross_pnl, fees, net_pnl
        """
        if side.lower() == 'buy':
            gross_pnl = quantity * (current_price - entry_price)
        else:  # sell
            gross_pnl = quantity * (entry_price - current_price)
        
        # Calculate fees on both entry and exit
        entry_fee = self.params.fee_rate * entry_price * quantity
        exit_fee = self.params.fee_rate * current_price * quantity
        total_fees = entry_fee + exit_fee
        
        net_pnl = gross_pnl - total_fees
        
        return {
            'gross_pnl': gross_pnl,
            'fees': total_fees,
            'net_pnl': net_pnl,
            'entry_fee': entry_fee,
            'exit_fee': exit_fee
        }
    
    def validate_position_size(self, quantity: float, price: float, max_position_value: float) -> bool:
        """
        Validate position size against maximum position value.
        
        Args:
            quantity: Position quantity
            price: Price per unit
            max_position_value: Maximum allowed position value
            
        Returns:
            True if position is valid
        """
        position_value = quantity * price
        return position_value <= max_position_value and quantity > 0
    
    def calculate_scale_in_conditions(self, current_price: float, last_entry_price: float) -> bool:
        """
        Check if scale-in conditions are met (bot.py: px <= state.entry_price*(1 - SCALE_IN_GAP_PCT))
        
        Args:
            current_price: Current market price
            last_entry_price: Price of last entry
            
        Returns:
            True if scale-in conditions are met
        """
        scale_in_gap_pct = 0.007  # 0.7% gap requirement from bot.py
        return current_price <= last_entry_price * (1 - scale_in_gap_pct)
    
    def apply_bot_sizing_logic(self, 
                              current_price: float, 
                              equity: float,
                              lower_band: float,
                              upper_band: float,
                              current_position: float = 0.0) -> Dict[str, any]:
        """
        Apply complete bot.py sizing logic for buy/sell decisions.
        
        Args:
            current_price: Current market price
            equity: Available equity
            lower_band: Lower Bollinger Band
            upper_band: Upper Bollinger Band  
            current_position: Current position quantity
            
        Returns:
            Dictionary with trade recommendation
        """
        result = {
            'action': 'hold',
            'quantity': 0.0,
            'entry_price': 0.0,
            'stop_loss': 0.0,
            'take_profit': 0.0,
            'position_value': 0.0,
            'risk_amount': 0.0
        }
        
        # Bot.py entry condition: lw <= bb_lo
        if current_position == 0.0 and current_price <= lower_band:
            # Calculate position using bot formulas
            quantity, risk_amount = self.calculate_position_size(current_price, equity)
            entry_price = self.calculate_entry_price(current_price, 'buy')
            stop_loss, take_profit = self.calculate_stop_take_prices(entry_price, 'buy')
            
            result.update({
                'action': 'buy',
                'quantity': quantity,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'position_value': quantity * entry_price,
                'risk_amount': risk_amount
            })
        
        # Bot.py exit conditions: hit_stop or hit_take or (hi >= bb_up)
        elif current_position > 0.0:
            entry_price = current_price  # Would need actual entry price in real implementation
            stop_loss, take_profit = self.calculate_stop_take_prices(entry_price, 'buy')
            
            hit_stop = current_price <= stop_loss
            hit_take = current_price >= take_profit or current_price >= upper_band
            
            if hit_stop or hit_take:
                exit_price = self.calculate_entry_price(current_price, 'sell')
                result.update({
                    'action': 'sell',
                    'quantity': current_position,
                    'entry_price': exit_price,
                    'reason': 'stop_loss' if hit_stop else 'take_profit'
                })
        
        return result


def get_bot_pricing_calculator() -> BotPricingCalculator:
    """Get configured bot pricing calculator with default parameters."""
    return BotPricingCalculator()