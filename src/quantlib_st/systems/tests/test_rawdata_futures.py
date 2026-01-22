import datetime
import numpy as np
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
        data=CsvFuturesSimTestData(end_date=datetime.datetime(2024, 3, 28)),
        config=Config("systems.provided.config.test_forecast_config.yaml"),
    )
    return system


"""
PRICE_CONTRACT: The contract currently held in the portfolio for trading.
CARRY_CONTRACT: The adjacent contract used as a benchmark to determine the curve slope (roll).

### Calculation Logic
`Raw Roll = PRICE - CARRY`

### Interpretation
- **Negative Roll**: Occurs in **Contango** (e.g., RUBBER where Front Price < Back Carry). This represents a "cost of carry" for long positions.
- **Positive Roll**: Occurs in **Backwardation** (e.g., Price > Carry). This represents a "gain" from the roll.

*Note for STIRs (e.g., SOFR):* Since prices are inversed ($100 - Rate$), if the held forward contract (`PRICE`) is more expensive than the front contract (`CARRY`), the value is expected to drift down toward the spot price as it approaches expiry, resulting in a negative carry.
"""


def test_get_instrument_raw_carry_data(system):
    carry_values = system.rawdata.get_instrument_raw_carry_data("RUBBER").tail(1)
    assert carry_values.CARRY.values[0] == 163.4
    assert carry_values.CARRY_CONTRACT.values[0] == "20240700"
    assert carry_values.PRICE.values[0] == 162.9
    assert carry_values.PRICE_CONTRACT.values[0] == "20240600"


def test_raw_futures_roll(system):
    roll = system.rawdata.raw_futures_roll("RUBBER").ffill().tail(1)
    roll_value = roll.values[0]
    assert roll_value == (162.9 - 163.4)


def test_roll_differentials(system):
    roll = system.rawdata.roll_differentials("RUBBER").ffill().tail(1)
    roll_diff = roll.values[0]
    assert np.isclose(roll_diff, 0.083333, atol=1e-6)  # +ve


def test_annualised_roll(system):
    roll = system.rawdata.annualised_roll("RUBBER").ffill().tail(1)
    roll_value = roll.values[0]
    assert np.isclose(roll_value, -6, atol=1e-6)  # -ve


def test_get_instrument_raw_carry_data_not_nearest_contract(system):
    carry_values = system.rawdata.get_instrument_raw_carry_data("SOFR").tail(1)
    assert carry_values.CARRY.values[0] == 96.415
    assert carry_values.CARRY_CONTRACT.values[0] == "20260900"
    assert carry_values.PRICE.values[0] == 96.42
    assert carry_values.PRICE_CONTRACT.values[0] == "20261200"


def test_raw_futures_roll_not_nearest_contract(system):
    roll = system.rawdata.raw_futures_roll("SOFR").ffill().tail(1)
    roll_value = roll.values[0]
    assert roll_value == (96.42 - 96.415)


def test_roll_differentials_not_nearest_contract(system):
    roll = system.rawdata.roll_differentials("SOFR").ffill().tail(1)
    roll_diff = roll.values[0]
    assert np.isclose(roll_diff, -0.25, atol=1e-6)  # +ve


def test_annualised_roll_not_nearest_contract(system):
    roll = system.rawdata.annualised_roll("SOFR").ffill().tail(1)
    roll_value = roll.values[0]
    assert np.isclose(roll_value, -0.0199999, atol=1e-6)  # -ve
