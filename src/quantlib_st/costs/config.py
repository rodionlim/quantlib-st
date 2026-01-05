from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InstrumentCostConfig:
    instrument_code: str
    point_size: float
    price_slippage: float  # Half spread in price units
    per_block_commission: float = 0.0
    percentage_commission: float = 0.0
    per_trade_commission: float = 0.0

    @classmethod
    def from_dict(cls, data: dict) -> InstrumentCostConfig:
        return cls(
            instrument_code=data["instrument_code"],
            point_size=data["point_size"],
            price_slippage=data["price_slippage"],
            per_block_commission=data.get("per_block_commission", 0.0),
            percentage_commission=data.get("percentage_commission", 0.0),
            per_trade_commission=data.get("per_trade_commission", 0.0),
        )
