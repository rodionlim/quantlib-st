from __future__ import annotations

import numpy as np
import pandas as pd

from quantlib_st.costs.config import InstrumentCostConfig


def calculate_annualized_volatility(
    prices: pd.Series, days_per_year: int = 256, vol_lookback: int = 35
) -> float:
    """
    Calculate annualized volatility from a price series.
    Matches the logic in pysystemtrade:
    1. Calculate absolute price changes.
    2. Calculate EWMA volatility (span=35).
    3. Take the mean of that volatility over the last year (256 days).
    4. Annualize it by multiplying by sqrt(256).
    """
    daily_returns = prices.diff().dropna()

    # EWMA volatility of absolute returns
    daily_vol = daily_returns.ewm(span=vol_lookback, adjust=True, min_periods=10).std()

    # Average over the last year (256 business days)
    recent_daily_vol = daily_vol.tail(days_per_year).mean()

    # Annualize
    return float(recent_daily_vol * np.sqrt(days_per_year))


def calculate_recent_average_price(
    prices: pd.Series, days_per_year: int = 256
) -> float:
    """
    Calculate the average price over the last year (256 business days).
    Matches _recent_average_price in pysystemtrade.
    """
    return float(prices.tail(days_per_year).mean())


def calculate_sr_cost(
    cost_config: InstrumentCostConfig,
    price: float,
    ann_stdev_price_units: float,
    blocks_traded: float = 1.0,
) -> float:
    """
    Calculates the expected reduction in Sharpe Ratio due to costs.
    Ported from pysystemtrade sysobjects.instruments.instrumentCosts.calculate_sr_cost
    """
    cost_instrument_currency = calculate_cost_instrument_currency(
        cost_config, blocks_traded=blocks_traded, price=price
    )

    # Annualized stdev in instrument currency (price units * point size)
    ann_stdev_instrument_currency = ann_stdev_price_units * cost_config.point_size

    if ann_stdev_instrument_currency == 0:
        return 0.0

    return cost_instrument_currency / ann_stdev_instrument_currency


def calculate_cost_instrument_currency(
    cost_config: InstrumentCostConfig,
    blocks_traded: float,
    price: float,
    include_slippage: bool = True,
) -> float:
    """
    Ported from pysystemtrade sysobjects.instruments.instrumentCosts.calculate_cost_instrument_currency
    """
    value_per_block = price * cost_config.point_size

    if include_slippage:
        slippage = (
            abs(blocks_traded) * cost_config.price_slippage * cost_config.point_size
        )
    else:
        slippage = 0.0

    commission = calculate_total_commission(
        cost_config, blocks_traded=blocks_traded, value_per_block=value_per_block
    )

    return slippage + commission


def calculate_total_commission(
    cost_config: InstrumentCostConfig, blocks_traded: float, value_per_block: float
) -> float:
    """
    Ported from pysystemtrade sysobjects.instruments.instrumentCosts.calculate_total_commission
    """
    per_trade_commission = cost_config.per_trade_commission
    per_block_commission = abs(blocks_traded) * cost_config.per_block_commission
    percentage_commission = (
        cost_config.percentage_commission * abs(blocks_traded) * value_per_block
    )

    return max([per_block_commission, per_trade_commission, percentage_commission])


def calculate_cost_percentage_terms(
    cost_config: InstrumentCostConfig, blocks_traded: float, price: float
) -> float:
    """
    Ported from pysystemtrade sysobjects.instruments.instrumentCosts.calculate_cost_percentage_terms
    """
    cost_in_currency = calculate_cost_instrument_currency(
        cost_config, blocks_traded=blocks_traded, price=price
    )
    total_value = abs(blocks_traded) * price * cost_config.point_size

    if total_value == 0:
        return 0.0

    return cost_in_currency / total_value
