import pytest

from quantlib_st.config.configdata import Config

from quantlib_st.sysdata.sim.csv_futures_sim_test_data import CsvFuturesSimTestData

from quantlib_st.systems.basesystem import System
from quantlib_st.systems.forecasting import Rules
from quantlib_st.systems.provided.futures_chapter15.basesystem import futures_system


@pytest.fixture
def system() -> System:
    """Minimal system fixture that can be parametrized with trading rules."""
    system = futures_system(
        trading_rules=Rules(),
        data=CsvFuturesSimTestData(),
        config=Config("systems.provided.config.test_forecast_config.yaml"),
    )
    return system


@pytest.fixture
def system_defaults() -> System:
    """Fetch system defaults for forecast scaling and capping config."""
    cfg = Config("systems.provided.config.test_forecast_config.yaml")
    del cfg.forecast_cap
    system = futures_system(
        trading_rules=Rules(),
        data=CsvFuturesSimTestData(),
        config=cfg,
    )
    return system


def test_get_raw_forecast(system):
    # Check 2015-12-11 to ensure consistency with historical pysystemtrade benchmarks
    ans = system.forecastScaleCap.get_raw_forecast("EDOLLAR", "ewmac8")
    val_2015 = ans.loc["2015-12-11"]
    assert abs(val_2015 - 0.191395) < 1e-6


def test_get_forecast_cap(system, system_defaults):
    ans = system.forecastScaleCap.get_forecast_cap()
    assert ans == 21.0

    ans = system_defaults.forecastScaleCap.get_forecast_cap()
    assert ans == 20.0


def test_get_forecast_scalar(system):
    # 1. From config (ewmac8 has 5.3 in the yaml)
    ans = system.forecastScaleCap.get_forecast_scalar("EDOLLAR", "ewmac8")
    assert (ans == 5.3).all()

    # 2. default (if missing from config, should be 1.0)
    cfg_no_scalar = Config(
        "quantlib_st.systems.provided.config.test_forecast_config.yaml"
    )
    del cfg_no_scalar.trading_rules["ewmac8"]["forecast_scalar"]

    system_default_scalar = futures_system(
        trading_rules=Rules(),
        data=CsvFuturesSimTestData(),
        config=cfg_no_scalar,
    )

    ans = system_default_scalar.forecastScaleCap.get_forecast_scalar(
        "EDOLLAR", "ewmac8"
    )
    assert (ans == 1.0).all()

    # 3. other config location (using .forecast_scalars dict)
    cfg_other_loc = Config(
        "quantlib_st.systems.provided.config.test_forecast_config.yaml"
    )
    # Must remove from trading_rules first as it takes precedence
    del cfg_other_loc.trading_rules["ewmac8"]["forecast_scalar"]
    cfg_other_loc.forecast_scalars = dict(ewmac8=11.0)

    system_other_loc = futures_system(
        trading_rules=Rules(),
        data=CsvFuturesSimTestData(),
        config=cfg_other_loc,
    )

    ans = system_other_loc.forecastScaleCap.get_forecast_scalar("EDOLLAR", "ewmac8")
    assert (ans == 11.0).all()
