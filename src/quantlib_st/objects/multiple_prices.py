from copy import copy
from dataclasses import dataclass
from typing import Optional

import datetime as datetime
import pandas as pd

from quantlib_st.core.exceptions import missingData
from quantlib_st.init.futures.build_multiple_prices_from_raw_data import (
    create_multiple_price_stack_from_raw_data,
)
from quantlib_st.objects.dict_of_named_futures_per_contract_prices import (
    list_of_price_column_names,
    list_of_contract_column_names,
    contract_column_names,
    setOfNamedContracts,
    contract_name_from_column_name,
    futuresNamedContractFinalPricesWithContractID,
    dictFuturesNamedContractFinalPricesWithContractID,
    price_column_names,
    price_name,
    carry_name,
    forward_name,
)

from quantlib_st.objects.dict_of_futures_per_contract_prices import (
    dictFuturesContractFinalPrices,
)


@dataclass
class singleRowMultiplePrices:
    price: Optional[float] = None
    carry: Optional[float] = None
    forward: Optional[float] = None
    price_contract: Optional[str] = None
    carry_contract: Optional[str] = None
    forward_contract: Optional[str] = None

    def concat_with_multiple_prices(self, multiple_prices, timedelta_seconds=1):
        new_time_index = multiple_prices.index[-1] + datetime.timedelta(
            seconds=timedelta_seconds
        )
        new_df_row = self.as_aligned_pd_row(new_time_index)

        combined_df = pd.concat([pd.DataFrame(multiple_prices), new_df_row], axis=0)

        new_multiple_prices = futuresMultiplePrices(combined_df)

        return new_multiple_prices

    def as_aligned_pd_row(self, time_index: datetime.timedelta) -> pd.DataFrame:
        new_dict = {
            price_name: self.price,
            carry_name: self.carry,
            forward_name: self.forward,
            contract_name_from_column_name(price_name): self.price_contract,
            contract_name_from_column_name(carry_name): self.carry_contract,
            contract_name_from_column_name(forward_name): self.forward_contract,
        }

        new_dict_with_nones_removed = dict(
            [(key, value) for key, value in new_dict.items() if value is not None]
        )

        new_df_row = pd.DataFrame(new_dict_with_nones_removed, index=[time_index])

        return new_df_row


class futuresMultiplePrices(pd.DataFrame):
    def __init__(self, data):
        _check_valid_multiple_price_data(data)
        super().__init__(data)  # type: ignore

        data.index.name = "index"  # arctic compatible

    @classmethod
    ## NOT TYPE CHECKING OF ROLL_CALENDAR AS WOULD CAUSE CIRCULAR IMPORT
    def create_from_raw_data(
        futuresMultiplePrices,
        roll_calendar,
        dict_of_futures_contract_closing_prices: dictFuturesContractFinalPrices,
    ):
        """

        :param roll_calendar: rollCalendar
        :param dict_of_futures_closing_contract_prices: dictFuturesContractPrices with only one column

        :return: pd.DataFrame with the 6 columns PRICE, CARRY, FORWARD, PRICE_CONTRACT, CARRY_CONTRACT, FORWARD_CONTRACT
        """

        all_price_data_stack = create_multiple_price_stack_from_raw_data(
            roll_calendar, dict_of_futures_contract_closing_prices
        )

        multiple_prices = futuresMultiplePrices(all_price_data_stack)
        multiple_prices._is_empty = False

        return multiple_prices

    @classmethod
    def create_empty(futuresMultiplePrices):
        """
        Our graceful fail is to return an empty, but valid, dataframe
        """

        data = pd.DataFrame(columns=multiple_data_columns)

        multiple_prices = futuresMultiplePrices(data)

        return multiple_prices

    def inverse(self):
        new_version = copy(self)
        for colname in list_of_price_column_names:
            new_version[colname] = 1 / self[colname]

        return futuresMultiplePrices(new_version)

    def add_offset_to_prices(self, offset: float):
        new_version = copy(self)
        for colname in list_of_price_column_names:
            new_version[colname] = self[colname] + offset

        return futuresMultiplePrices(new_version)

    def current_contract_dict(self) -> setOfNamedContracts:
        if len(self) == 0:
            raise missingData

        final_row = self.iloc[-1]
        contract_dict = dict(
            [(key, final_row[value]) for key, value in contract_column_names.items()]
        )
        contract_dict = setOfNamedContracts(contract_dict)

        return contract_dict

    def as_dict(self) -> dictFuturesNamedContractFinalPricesWithContractID:
        """
        Split up and transform into dict

        :return: dictFuturesContractFinalPricesWithContractID, keys PRICE, FORWARD, CARRY
        """

        self_as_dict = {}
        for price_column_name in list_of_price_column_names:
            contract_column_name = contract_name_from_column_name(price_column_name)
            self_as_dict[price_column_name] = (
                futuresNamedContractFinalPricesWithContractID(
                    self[price_column_name],
                    self[contract_column_name],
                    price_column_name=price_column_name,
                )
            )  # type: ignore

        self_as_dict = dictFuturesNamedContractFinalPricesWithContractID(self_as_dict)

        return self_as_dict

    @classmethod
    def from_merged_dict(
        futuresMultiplePrices,
        prices_dict: dictFuturesNamedContractFinalPricesWithContractID,
    ):
        """
        Re-create from dict, eg results of _as_dict

        :param prices_dict: dictFuturesContractFinalPricesWithContractID keys PRICE, CARRY, FORWARD
        :return: object
        """

        multiple_prices_list = []
        for key_name in price_column_names.keys():
            try:
                relevant_data = prices_dict[key_name]

            except KeyError:
                raise Exception(
                    "Create multiple prices as dict needs %s as key" % key_name
                )

            multiple_prices_list.append(relevant_data.as_pd())

        multiple_prices_data_frame = pd.concat(multiple_prices_list, axis=1)

        # Now it's possible we have more price data for some things than others
        # so we forward fill contract_ids; not prices
        multiple_prices_data_frame[list_of_contract_column_names] = (
            multiple_prices_data_frame[list_of_contract_column_names].ffill()
        )

        multiple_prices_object = futuresMultiplePrices(multiple_prices_data_frame)

        return multiple_prices_object

    def sort_index(self):  # type: ignore
        df = pd.DataFrame(self)
        sorted_df = df.sort_index()

        return futuresMultiplePrices(sorted_df)


multiple_data_columns = list_of_price_column_names + list_of_contract_column_names


def _check_valid_multiple_price_data(df):
    if len(df.columns) == 0:
        return

    missing_columns = [
        colname for colname in multiple_data_columns if colname not in df.columns
    ]

    if len(missing_columns) > 0:
        raise Exception(
            "futuresMultiplePrices requires columns %s but is missing %s"
            % (str(multiple_data_columns), str(missing_columns))
        )
