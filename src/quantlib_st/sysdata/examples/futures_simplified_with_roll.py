"""
Example: futuresSimData implementation using roll calendars derived from per-contract prices.

This shows how to:
1) Provide per-contract final prices (dictFuturesContractFinalPrices)
2) Build a roll calendar from roll parameters
3) Build multiple prices (PRICE/CARRY/FORWARD) from that calendar

Replace the mock price generation with API calls.
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
from quantlib_st.objects.dict_of_futures_per_contract_prices import (
    dictFuturesContractFinalPrices,
)
from quantlib_st.objects.multiple_prices import futuresMultiplePrices
from quantlib_st.objects.adjusted_prices import futuresAdjustedPrices
from quantlib_st.objects.rolls import rollParameters
from quantlib_st.objects.roll_calendars import rollCalendar
from quantlib_st.sysdata.sim.futures_sim_data import futuresSimData


class MockApiFuturesSimDataWithRoll(futuresSimData):
    """
    Example implementation that derives PRICE/CARRY/FORWARD from per-contract prices.

    Replace `_mock_contract_prices` with calls to your external API.
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
        if instrument_code != "BRT":
            return futuresMultiplePrices.create_empty()

        # 1) Build per-contract final prices (mocked here)
        contract_prices = self._mock_contract_prices(start_date)

        # 2) Build roll calendar based on roll parameters + available contracts
        roll_params = self.get_roll_parameters(instrument_code)
        calendar = rollCalendar.create_from_prices(contract_prices, roll_params)

        # 3) Convert per-contract data into multiple prices (PRICE/CARRY/FORWARD)
        multiple_prices = futuresMultiplePrices.create_from_raw_data(
            calendar, contract_prices
        )

        # Ensure we respect the requested start date
        filtered = pd.DataFrame(multiple_prices).loc[start_date:]
        return futuresMultiplePrices(filtered)

    def _mock_contract_prices(
        self, start_date: dt.datetime, days: int = 30
    ) -> dictFuturesContractFinalPrices:
        index = pd.date_range(start=start_date, periods=days, freq="B")

        # Mock contract list (YYYYMM)
        contract_ids = ["202510", "202511", "202512", "202601"]

        price_dict = {}
        for i, contract_id in enumerate(contract_ids):
            # Each contract series is a smooth trend with a small offset
            base = 75.0 + (i * 0.5)
            series = pd.Series(base + np.linspace(0, 1.0, num=len(index)), index=index)
            price_dict[contract_id] = series

        return dictFuturesContractFinalPrices(price_dict)


if __name__ == "__main__":
    data = MockApiFuturesSimDataWithRoll()
    mp = data.get_multiple_prices("BRT")
    backadj = data.get_backadjusted_futures_price("BRT")
    print(mp.tail(3))
    print(backadj.tail(3))
