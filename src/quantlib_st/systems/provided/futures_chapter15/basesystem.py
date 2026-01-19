"""
Minimal futures system for account-stage testing.

This system wires only the Account stage to keep things fast and focused.
"""

from quantlib_st.config.configdata import Config

from quantlib_st.sysdata.sim.csv_futures_sim_test_data import CsvFuturesSimTestData

from quantlib_st.systems.accounts.accounts_stage import Account
from quantlib_st.systems.basesystem import System
from quantlib_st.systems.forecast_scale_cap import ForecastScaleCap
from quantlib_st.systems.forecasting import Rules
from quantlib_st.systems.rawdata import RawData


def futures_system(
    data=None,
    config=None,
    trading_rules=None,
):
    """
    Minimal system with only Account stage.

    :param data: data object (defaults to CsvFuturesSimTestData)
    :type data: quantlib_st.sysdata.sim.sim_data.simData or compatible

    :param config: Configuration object (defaults to test_account_config.yaml)
    :type config: quantlib_st.config.configdata.Config
    """

    if data is None:
        data = CsvFuturesSimTestData()

    if config is None:
        config = Config("systems.provided.config.test_account_config.yaml")

    if isinstance(trading_rules, Rules):
        rules_stage = trading_rules
    else:
        rules_stage = Rules(trading_rules)

    stage_list = [
        Account(),
        ForecastScaleCap(),
        RawData(),
        rules_stage,
    ]

    system = System(
        stage_list,
        data,
        config,
    )

    return system


if __name__ == "__main__":
    import doctest

    doctest.testmod()
