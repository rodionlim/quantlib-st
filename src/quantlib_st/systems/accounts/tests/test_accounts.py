import pytest

from quantlib_st.sysdata.sim.csv_futures_sim_test_data import CsvFuturesSimTestData
from quantlib_st.config.configdata import Config
from quantlib_st.systems.provided.futures_chapter15.basesystem import futures_system


@pytest.fixture(scope="module")
def system():
    """Minimal system fixture using Account stage only."""
    system = futures_system(
        data=CsvFuturesSimTestData(),
        config=Config("systems.provided.config.test_account_config.yaml"),
    )
    return system


def test_account_costs_minimal(system):
    """Minimal smoke test for Account stage costs using two instruments."""
    edollar_cost = system.accounts.get_SR_cost_per_trade_for_instrument("EDOLLAR")
    us10_cost = system.accounts.get_SR_cost_per_trade_for_instrument("US10")

    assert isinstance(edollar_cost, float)
    assert isinstance(us10_cost, float)
    assert edollar_cost >= 0.0
    assert us10_cost >= 0.0
