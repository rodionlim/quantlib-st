import pytest

from quantlib_st.sysdata.sim.csv_futures_sim_test_data import CsvFuturesSimTestData
from quantlib_st.config.configdata import Config
from quantlib_st.systems.provided.futures_chapter15.basesystem import futures_system
from quantlib_st.systems.basesystem import System


@pytest.fixture
def system(request) -> System:
    """Minimal system fixture that can be parametrized with trading rules."""
    trading_rules = getattr(request, "param", None)
    system = futures_system(
        trading_rules=trading_rules,
        data=CsvFuturesSimTestData(),
        config=Config("systems.provided.config.test_account_config.yaml"),
    )
    return system


@pytest.mark.parametrize(
    "system",
    [
        dict(
            rule0="systems.provided.rules.ewmac.ewmac_forecast_with_defaults",
            rule1="systems.provided.rules.breakout.breakout",
            rule2="systems.provided.rules.carry.carry",
        )
    ],
    indirect=True,
)
def test_get_raw_forecast_minimal(system: System):
    """Minimal smoke test for forecasting rule."""
    ans = system.rules.get_raw_forecast("EDOLLAR", "rule0")
    assert abs(ans.iloc[-1] - (-2.784115)) < 0.00001

    ans = system.rules.get_raw_forecast("EDOLLAR", "rule1")
    assert abs(ans.iloc[-1] - (-19.617574)) < 0.00001
