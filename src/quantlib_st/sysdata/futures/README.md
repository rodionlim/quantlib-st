# Futures Contract Price Data Implementation Guide

This directory contains the base class and implementations for handling per-contract futures price data.

To implement a new data source (e.g., an API-based provider like Bloomberg, Reuters, or an internal database), you should inherit from `futuresContractPriceData` in `futures_per_contract_prices.py`.

## Core Implementation Requirements

When creating a new subclass, you must implement the following "no checking" internal methods which the base class uses to satisfy public API requests.

### 1. Data Retrieval (Mandatory)

#### `_get_merged_prices_for_contract_object_no_checking(self, contract_object: futuresContract) -> futuresContractPrices`

Fetches all available price data for a specific contract.

- **Input**: A `futuresContract` object (contains `instrument_code` and `date_str`).
- **Output**: A `futuresContractPrices` object.

#### `_get_prices_at_frequency_for_contract_object_no_checking(self, contract_object: futuresContract, frequency: Frequency) -> futuresContractPrices`

Fetches price data at a specific granularity (Daily, Hourly, etc.).

- **Input**: `futuresContract` object and a `Frequency` enum.
- **Output**: A `futuresContractPrices` object.

### 2. Discovery Methods (Mandatory)

#### `get_contracts_with_merged_price_data(self) -> listOfFuturesContracts`

Returns a complete list of all contracts available in the data source.

#### `get_contracts_with_price_data_for_frequency(self, frequency: Frequency) -> listOfFuturesContracts`

Returns a list of all contracts available for a specific frequency.

## The `listOfFuturesContracts` Object

Methods that return contract lists must return a `listOfFuturesContracts` object (from `quantlib_st.objects.contracts`). This is a specialized list of `futuresContract` objects that provides utility methods for filtering.

### Creating the list

To implement these methods, you typically create a standard Python list of `futuresContract` objects and then wrap it:

```python
from quantlib_st.objects.contracts import futuresContract, listOfFuturesContracts

def get_contracts_with_merged_price_data(self) -> listOfFuturesContracts:
    # 1. Logic to get your ticker list (e.g. from an API or database)
    all_tickers = [('CRUDE_OIL', '20240600'), ('CRUDE_OIL', '20240900')]

    # 2. Convert to futuresContract objects
    contract_list = [
        futuresContract(instr, date_id)
        for instr, date_id in all_tickers
    ]

    # 3. Return as the specialized collection
    return listOfFuturesContracts(contract_list)
```

### Why use `listOfFuturesContracts`?

The system relies on this object's helper methods, such as:

- `.unique_list_of_instrument_codes()`: To see which instruments have data.
- `.contracts_in_list_for_instrument_code(code)`: To filter contracts for a single instrument.
- `.list_of_dates()`: To get a list of YYYYMMDD strings.

### 3. Data Persistence (Optional)

If your data source supports writing or deleting data, you should also implement:

- `_write_merged_prices_for_contract_object_no_checking`
- `_write_prices_at_frequency_for_contract_object_no_checking`
- `_delete_merged_prices_for_contract_object_with_no_checks_be_careful`
- `_delete_prices_at_frequency_for_contract_object_with_no_checks_be_careful`

## Data Format

The `futuresContractPrices` object is a specialized `pd.DataFrame`. Your implementation must return a DataFrame with the following columns:

- `OPEN` (float): Opening price.
- `HIGH` (float): High price.
- `LOW` (float): Low price.
- `FINAL` (float): Closing or settlement price (Mandatory).
- `VOLUME` (float): Traded volume.

The index of the DataFrame must be a `DatetimeIndex` named `index`.

## Implementation Hint for APIs

For API-based implementations, it is common to:

1. Maintain or fetch a mapping of `instrument_code` (e.g., 'CRUDE_OIL') to specific vendor tickers (e.g., 'CL1 Comdty', 'CLM24 Comdty').
2. Use the `contract_object.date_str` (YYYYMMDD) or `contract_object.instrument` to construct the necessary API request.
3. Handle missing data gracefully by returning `futuresContractPrices.create_empty()`.

Refer to `csvFuturesContractPriceData` in `csv/csv_futures_contract_prices.py` for a reference implementation using local files.

## Roll Parameters Explanation

The `rollParameters` object (and corresponding configuration files like `rollconfig.csv`) controls how we construct continuous price series and manage position rolling. These parameters are critical for both backtesting (simulating realistic rolls) and production (generating correct signals).

### `hold_rollcycle`

**What it is:** A string of contract letter codes (e.g., `"HMUZ"` for March, June, Sept, Dec) representing the contracts we are allowed to hold positions in.
**Why it is needed:**

- **Liquidity:** Most futures markets have valid prices for many months, but liquidity is often concentrated in quarterly contracts. Rolling into an illiquid "serial" month (like August for S&P 500) would incur massive transaction costs (slippage).
- **Execution:** This forces the system to skip illiquid months and stick to the "major" contracts where execution is cheap.

### `priced_rollcycle`

**What it is:** A string of all contract letter codes (e.g., `"FGHJKMNQUVXZ"` for all months) where the market provides valid, reliable pricing data.
**Why it is needed:**

- **Information Density:** We use this to calculate "Carry" (the shape of the futures curve). Even if we only _trade_ quarterly (`hold_rollcycle="HMUZ"`), checking the prices of monthly contracts (`priced_rollcycle="...All..."`) gives us a smoother, more granular signal of the curve's slope.
- **Curve Smoother:** It prevents the carry signal from being "steppy" or "blocky" by allowing us to measure the roll yield over shorter timeframes (e.g., Mar vs Apr) rather than just long ones (Mar vs Jun).

### `roll_offset_day`

**What it is:** An integer indicating the target day to roll relative to the contract's expiry. Negative values mean days _before_ expiry.
**Why it is needed:**

- **Avoid Delivery:** Systematic trend following strategies never want to take physical delivery of commodities. We must exit before First Notice Day.
- **Liquidity Management:** We want to roll when volume is high but before the "liquidity cliff" that occurs right at expiry. Rolling 5 days early (`-5`) is a common standard to balance liquidity vs. holding period.

### `carry_offset`

**What it is:** An integer defining which neighbor contract to use for calculating the Carry signal.

- `+1`: Compare the contract we hold to the **Next** contract in the `priced_rollcycle`.
- `-1`: Compare to the **Previous** contract.
  **Why it is needed:**
- **Yield Calculation:** Carry is calculated as a spread. To get an annualized roll yield, we need a pair of prices.
- **Adjustment:** In the vast majority of cases (and in `rollconfig.csv`), this is set to **`1`**. This means "Compare the contract we are holding (Near) to the next one out (Far)".
  - _Note:_ The code default in `rollParameters` handles `carry_offset` = `-1` (Previous) as a fallback, but the configuration usually overrides this to `1` to implement the standard `Near - Next` carry calculation (rolling down the curve).

### `approx_expiry_offset`

**What it is:** An integer (1-31) representing the approximate day of the month that contracts expire.
**Why it is needed:**

- **Calculation Simplification:** To calculate an annualized return, we need to know the time difference (in days) between two contracts.
- **Heuristic:** Instead of maintaining a complex, maintenance-heavy database of every single exchange's exact Last Trading Day / First Notice Day rules (which change constantly), we approximate. Assuming all contracts expire on the "15th" (or whatever the offset is) is sufficient to calculate a statistically valid carry signal without the engineering headache of exact calendar management.
