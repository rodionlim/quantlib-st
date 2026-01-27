# Futures Example: External API Stub

This folder contains a minimal, working example that shows how to implement a futures data source for carry and backadjustment.

## Files

- [futures_simplified.py](futures_simplified.py) — A mock implementation of `futuresSimData` that returns synthetic prices for one instrument (`BRT`) with pre-built `PRICE/CARRY/FORWARD` series.
- [futures_simplified_with_roll.py](futures_simplified_with_roll.py) — A mock implementation that derives `PRICE/CARRY/FORWARD` from per-contract prices using roll calendars and roll parameters.

## What you need to implement

The example class `MockApiFuturesSimData` in [futures_simplified.py](futures_simplified.py) shows how to implement the abstract methods from `futuresSimData`:

1. **Instrument catalog**
   - `get_instrument_list()`
   - `get_instrument_asset_classes()`

2. **Costs + metadata**
   - `get_spread_cost()`
   - `get_instrument_meta_data()`
   - `get_instrument_object_with_meta_data()`

3. **Roll setup**
   - `get_roll_parameters()`

4. **Core price methods**
   - `get_multiple_prices_from_start_date()`
   - `get_backadjusted_futures_price()` (usually calls the helper `_get_backadjusted_futures_price_from_multiple_prices`)

## What to replace with API calls

In the examples, the following are mock implementations:

- `get_multiple_prices_from_start_date()` in [futures_simplified.py](futures_simplified.py) → replace with your API call to fetch:
  - price series for the traded contract (PRICE)
  - price series for the carry contract (CARRY)
  - price series for the forward contract (FORWARD)
  - the corresponding contract IDs (`PRICE_CONTRACT`, `CARRY_CONTRACT`, `FORWARD_CONTRACT`)

- `_mock_contract_prices()` in [futures_simplified_with_roll.py](futures_simplified_with_roll.py) → replace with your API call to fetch per-contract final prices:
  - one price series per contract (keyed by `YYYYMM`)
  - these are used to build a roll calendar and derive `PRICE/CARRY/FORWARD`

The example uses `BRT` with contract IDs `202512`, `202511`, `202510`, etc., purely as placeholders.

## Data shape required for futuresMultiplePrices

Your API output must be converted into a `futuresMultiplePrices` object with a `DatetimeIndex` and these columns:

- `PRICE`
- `CARRY`
- `FORWARD`
- `PRICE_CONTRACT`
- `CARRY_CONTRACT`
- `FORWARD_CONTRACT`

Once you have this, `futuresSimData` can compute:

- **Carry metrics** (roll, annualised roll)
- **Backadjusted futures prices** using `_get_backadjusted_futures_price_from_multiple_prices`

## When you might need per-contract data

If your API provides raw per-contract data (one contract per ticker), you can also implement a data source that inherits from `futuresContractPriceData`.

See:

- [sysdata/futures/README.md](../futures/README.md)
- [sysdata/futures/futures_per_contract_prices.py](../futures/futures_per_contract_prices.py)
- [objects/dict_of_futures_per_contract_prices.py](../../objects/dict_of_futures_per_contract_prices.py)

These per-contract classes are **optional** for carry/backadjustment if you already have continuous `PRICE`, `CARRY`, and `FORWARD` series.
