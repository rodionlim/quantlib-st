from __future__ import annotations

import json
from abc import ABC, abstractmethod
from quantlib_st.costs.config import InstrumentCostConfig


class CostDataSource(ABC):
    @abstractmethod
    def get_cost_config(self, instrument_code: str) -> InstrumentCostConfig:
        pass


class ConfigFileCostDataSource(CostDataSource):
    def __init__(self, config_path: str):
        with open(config_path, "r") as f:
            self.config_data = json.load(f)

    def get_cost_config(self, instrument_code: str) -> InstrumentCostConfig:
        # Assuming the config file is a list of instrument configs or a dict keyed by code
        if isinstance(self.config_data, list):
            for item in self.config_data:
                if item["instrument_code"] == instrument_code:
                    return InstrumentCostConfig.from_dict(item)
        elif isinstance(self.config_data, dict):
            if instrument_code in self.config_data:
                return InstrumentCostConfig.from_dict(self.config_data[instrument_code])
            elif (
                "instrument_code" in self.config_data
                and self.config_data["instrument_code"] == instrument_code
            ):
                return InstrumentCostConfig.from_dict(self.config_data)

        raise ValueError(f"No cost config found for instrument: {instrument_code}")


class IBKRCostDataSource(CostDataSource):
    """
    Stub for future IBKR API integration.
    """

    def get_cost_config(self, instrument_code: str) -> InstrumentCostConfig:
        # TODO: Implement IBKR API calls to fetch real-time/historical spreads and commissions
        raise NotImplementedError(
            "IBKR API integration not yet implemented. Please use --config for now."
        )
