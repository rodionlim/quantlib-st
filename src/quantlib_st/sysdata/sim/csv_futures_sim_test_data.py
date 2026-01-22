import pandas as pd
from datetime import datetime
from typing import Optional

from quantlib_st.sysdata.csv.csv_multiple_prices import csvFuturesMultiplePricesData
from quantlib_st.sysdata.csv.csv_adjusted_prices import csvFuturesAdjustedPricesData
from quantlib_st.sysdata.csv.csv_spot_fx import csvFxPricesData
from quantlib_st.sysdata.csv.csv_instrument_data import csvFuturesInstrumentData
from quantlib_st.sysdata.csv.csv_roll_parameters import csvRollParametersData
from quantlib_st.sysdata.csv.csv_spread_costs import csvSpreadCostData

from quantlib_st.sysdata.data_blob import dataBlob
from quantlib_st.objects.spot_fx_prices import fxPrices
from quantlib_st.objects.adjusted_prices import futuresAdjustedPrices
from quantlib_st.objects.multiple_prices import futuresMultiplePrices

from quantlib_st.sysdata.sim.futures_sim_data_with_data_blob import (
    genericBlobUsingFuturesSimData,
)
from quantlib_st.logging.logger import get_logger
from quantlib_st.core.dateutils import ARBITRARY_START


class CsvFuturesSimTestData(genericBlobUsingFuturesSimData):
    """
    Specialisation of futuresSimData that allows start and end dates to be configured.
    Useful for unit tests, so that new data added to the CSV price files doesn't mess with
    assertions, or if a test is needed at a certain date/time or period.
    """

    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    # Latest in CSV at time of writing
    DEFAULT_END_DATE = datetime.strptime("2021-03-08 20:00:00", DATE_FORMAT)

    def __init__(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        log=get_logger("csvFuturesSimTestData"),
    ):
        data = dataBlob(
            log=log,
            csv_data_paths=dict(
                csvFuturesAdjustedPricesData="quantlib_st.data.test.adjusted_prices_csv",
                csvFuturesInstrumentData="quantlib_st.data.test.csvconfig",
                csvFuturesMultiplePricesData="quantlib_st.data.futures.multiple_prices_csv",
                csvRollParametersData="quantlib_st.data.futures.roll_calendars_csv",
                csvSpreadCostData="quantlib_st.data.test.csvconfig",
            ),
            class_list=[
                csvFuturesAdjustedPricesData,
                csvFuturesMultiplePricesData,
                csvFuturesInstrumentData,
                csvFxPricesData,
                csvRollParametersData,
                csvSpreadCostData,
            ],
        )

        super().__init__(data=data)

        if start_date is not None:
            self._start_date = start_date
        else:
            self._start_date = ARBITRARY_START

        if end_date is not None:
            self._end_date = end_date
        else:
            self._end_date = self.DEFAULT_END_DATE

    def __repr__(self):
        return (
            f"csvFuturesSimTestData with {self.get_instrument_list()} instruments, "
            f"start date {self.start_date.strftime(self.DATE_FORMAT)}, "
            f"end date {self.end_date.strftime(self.DATE_FORMAT)}"
        )

    @property
    def start_date(self):
        return self._start_date

    @property
    def end_date(self):
        return self._end_date

    def get_backadjusted_futures_price(
        self, instrument_code: str
    ) -> futuresAdjustedPrices:
        data = super().db_futures_adjusted_prices_data.get_adjusted_prices(
            instrument_code
        )
        date_adjusted = data[self.start_date : self.end_date]
        return date_adjusted  # type: ignore

    def get_multiple_prices(self, instrument_code: str) -> futuresMultiplePrices:
        data = super().get_multiple_prices(instrument_code)
        date_adjusted = data[self.start_date : self.end_date]
        return date_adjusted

    def get_fx_for_instrument(
        self, instrument_code: str, base_currency: str
    ) -> fxPrices:
        data = super().get_fx_for_instrument(instrument_code, base_currency)
        date_adjusted = data[self.start_date : self.end_date]
        return date_adjusted  # type: ignore

    def daily_prices(self, instrument_code: str) -> pd.Series:
        data = super().daily_prices(instrument_code)
        date_adjusted = data[self.start_date : self.end_date]
        return date_adjusted

    def get_instrument_raw_carry_data(self, instrument_code: str) -> pd.DataFrame:
        data = super().get_instrument_raw_carry_data(instrument_code)
        date_adjusted = data[self.start_date : self.end_date]
        return date_adjusted

    def get_current_and_forward_price_data(self, instrument_code: str) -> pd.DataFrame:
        data = super().get_current_and_forward_price_data(instrument_code)
        date_adjusted = data[self.start_date : self.end_date]
        return date_adjusted
