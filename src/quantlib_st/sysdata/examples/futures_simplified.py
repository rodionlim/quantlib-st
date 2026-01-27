"""
Example: Minimal futuresSimData implementation with mock data.

This module is intended as a template for plugging in an external API that returns
per-contract futures prices. Replace the mock data generators with API calls.
"""

from __future__ import annotations

import datetime as dt
import numpy as np
import pandas as pd

from quantlib_st.objects.instruments import (
    assetClassesAndInstruments,
    futuresInstrument,
    futuresInstrumentWithMetaData,
    instrumentMetaData,
)
from quantlib_st.objects.multiple_prices import futuresMultiplePrices
from quantlib_st.objects.dict_of_named_futures_per_contract_prices import (
    price_name,
    carry_name,
    forward_name,
    contract_name_from_column_name,
)
from quantlib_st.objects.adjusted_prices import futuresAdjustedPrices
from quantlib_st.objects.rolls import rollParameters
from quantlib_st.sysdata.sim.futures_sim_data import futuresSimData

price_contract_name = contract_name_from_column_name(price_name)
carry_contract_name = contract_name_from_column_name(carry_name)
forward_contract_name = contract_name_from_column_name(forward_name)


class MockApiFuturesSimData(futuresSimData):
    """
    Minimal, end-to-end futuresSimData example.

    Replace the mock methods with your external API calls.
    """

    def __init__(self, start_date: dt.datetime | None = None):
        super().__init__()
        self._start_date_for_data_from_config = start_date or dt.datetime(2024, 1, 2)

    def get_instrument_list(self) -> list[str]:
        return ["BRT"]

    def get_instrument_asset_classes(self) -> assetClassesAndInstruments:
        series = pd.Series({"BRT": "Energy"})
        return assetClassesAndInstruments.from_pd_series(series)

    def get_spread_cost(self, instrument_code: str) -> float:
        return 0.01

    def get_roll_parameters(self, instrument_code: str) -> rollParameters:
        return rollParameters(
            hold_rollcycle="FGHJKMNQUVXZ",
            priced_rollcycle="FGHJKMNQUVXZ",
            roll_offset_day=0,
            carry_offset=-1,
            approx_expiry_offset=0,
        )

    def get_instrument_meta_data(
        self, instrument_code: str
    ) -> futuresInstrumentWithMetaData:
        instrument = futuresInstrument(instrument_code)
        meta = instrumentMetaData(
            Description="Brent Crude Oil (Mock)",
            Pointsize=1000.0,
            Currency="USD",
            AssetClass="Energy",
            PerBlock=0.0,
            Percentage=0.0,
            PerTrade=0.0,
            Region="Global",
        )
        return futuresInstrumentWithMetaData(instrument, meta)

    def get_instrument_object_with_meta_data(
        self, instrument_code: str
    ) -> futuresInstrumentWithMetaData:
        return self.get_instrument_meta_data(instrument_code)

    def get_backadjusted_futures_price(
        self, instrument_code: str
    ) -> futuresAdjustedPrices:
        return self._get_backadjusted_futures_price_from_multiple_prices(
            instrument_code,
            backadjust_methodology="diff_adjusted",
        )

    def get_multiple_prices_from_start_date(
        self, instrument_code: str, start_date: dt.datetime
    ) -> futuresMultiplePrices:
        """
        Mock implementation using synthetic prices and a rolling contract schedule.

        Replace `_mock_multiple_prices` with API calls returning the raw contract
        prices and contract IDs.
        """
        if instrument_code != "BRT":
            return futuresMultiplePrices.create_empty()

        return self._mock_multiple_prices(start_date)

    def _mock_multiple_prices(
        self, start_date: dt.datetime, days: int = 15
    ) -> futuresMultiplePrices:
        index = pd.date_range(start=start_date, periods=days, freq="B")

        # Synthetic price series
        base_price = 75.0 + np.linspace(0, 1.4, num=days)
        price_series = pd.Series(base_price, index=index)
        carry_series = price_series + 0.2
        forward_series = price_series + 0.4

        # Mock contract IDs (YYYYMM) that change over time
        contract_schedule = ["202512", "202511", "202510"]
        chunk = int(np.ceil(days / len(contract_schedule)))
        price_contracts = (
            [contract for contract in contract_schedule for _ in range(chunk)]
        )[:days]

        contract_map = {
            "202512": ("202511", "202510"),
            "202511": ("202510", "202509"),
            "202510": ("202509", "202508"),
        }
        carry_contracts = [contract_map[c][0] for c in price_contracts]
        forward_contracts = [contract_map[c][1] for c in price_contracts]

        data = pd.DataFrame(
            {
                price_name: price_series,
                carry_name: carry_series,
                forward_name: forward_series,
                price_contract_name: price_contracts,
                carry_contract_name: carry_contracts,
                forward_contract_name: forward_contracts,
            },
            index=index,
        )

        return futuresMultiplePrices(data)


if __name__ == "__main__":
    data = MockApiFuturesSimData()
    multiple_prices = data.get_multiple_prices("BRT")
    backadjusted = data.get_backadjusted_futures_price("BRT")
    print(multiple_prices.tail(3))
    print(backadjusted.tail(3))
