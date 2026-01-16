# Systems: Rules, TradingRules, SystemStage, System

The key idea of an entire System is a _pipeline_ that turns raw data into forecasts, positions, and P&L through composable stages.

## Mental Model (High Level)

Think of a trading system as a production line:

1. **Rule Logic**: A pure Python function that calculates a signal (forecast).
2. **TradingRule (Singular)**: A _specification_. It wraps the logic function with specific parameters (e.g., "Trend with a 32-day window").
3. **Rules (Plural/Stage)**: A _collection_ (dictionary) of `TradingRule` objects. This is the stage that manages all your signals.
4. **SystemStage**: A pipeline step that consumes outputs from earlier stages and produces new outputs.
5. **System**: The orchestrator that wires stages together into a full strategy.

## What is a TradingRule? (The Specification)

A `TradingRule` is NOT a time series. It is a **template** for a signal. It answers the question: _"How do I calculate this signal for any instrument I'm given?"_

It consists of:

- **Logic**: The Python function to call.
- **Data Req**: What the function needs (e.g., "give me daily prices").
- **Parameters**: The settings for this specific version (e.g., `window=32`).

**Mental Model**: If a "Moving Average Crossover" is a recipe, a `TradingRule` is a **printed copy of that recipe** with specific quantities written in.

## What is Rules? (The Collection/Stage)

The `Rules` stage (the `Rules` class) is a `SystemStage`. It contains a dictionary that maps **Names** to `TradingRule` objects. You don't usually have multiple different "Rules Stages" in one system; you have one Rules stage that contains every signal you might ever want to use for any instrument.

- **What are "Names"?**: These are arbitrary labels you invent to identify a signal. For example: `"ewmac_8_32"`, `"carry"`, or `"my_fancy_signal"`. These names are used later when you want to look up a specific signal's performance.
- **Relationship**: The `Rules` stage acts as a "Box of Recipes".
- **Instruments**: One instrument (e.g., Gold) is passed through **every recipe in the box**.
- **The Result**: If you have 3 trading rules in your stage, Gold will have 3 different signals. These 3 signals are later weighted and combined into a single forecast for Gold.

### How is it linked to SystemStage?

1. **`Rules` is a `SystemStage`**: Like all stages, it sits inside the `System`.
2. **Data Flow**: The `System` tells the `Rules` stage: _"I need the forecast for Gold using the 'ewmac_8_32' rule."_
3. **Execution**: The `Rules` stage looks up that **Name**, finds the corresponding `TradingRule` object, and executes it using Gold's price data.

| Component         | Nature         | Example                                                   |
| :---------------- | :------------- | :-------------------------------------------------------- |
| **Name**          | Key (String)   | `"trend_fast"`                                            |
| **`TradingRule`** | Value (Object) | A template saying: "Use EWMA logic with window 32."       |
| **`Rules` Stage** | Map (Dict)     | `{ "trend_fast": <TradingRule>, "carry": <TradingRule> }` |

## Where are Rules and Collections defined? (The Config)

The definition of rules and which rules belong to which instrument happens in the **System Config** (usually a `.yaml` file or a Python dictionary).

### 1. Global Rule Definitions

In the config under `trading_rules`, you define the names and logic for every signal in your strategy. This is a **Global Collection**.

```yaml
trading_rules:
  ewmac_8_32:
    function: systems.provided.rules.ewmac
    args: { Llookback: 32, Slookback: 8 }
  carry:
    function: systems.provided.rules.carry
```

### 2. Instrument-Specific Weights

Under `forecast_weights`, you define which rules from the global collection apply to which instrument.

```yaml
forecast_weights:
  GOLD:
    ewmac_8_32: 0.5 # Gold uses these two rules
    carry: 0.5
  CORN:
    ewmac_8_32: 1.0 # Corn only uses the trend rule
```

### 3. Summary of Storage and Execution

- **Storage**: We store **one collection** of `TradingRule` objects for the whole `System`.
- **Filtering**: We do NOT store a separate collection per instrument. Instead, we use the `forecast_weights` as a filter.
- **Execution (On Demand)**: The system is "lazy". It only calculates a rule's forecast for Gold if Gold has a non-zero weight for that rule in the config.

**Mental Model**:

- **The Rules Stage**: A generic factory that knows how to make all types of signals.
- **The Config**: A manager that says, "For Gold, I want 50% of the Fast Trend signal and 50% of the Carry signal."
- **The System**: On demand, it fetches the prices for Gold, asks the Factory for those specific signals, and combines them.

## What is a SystemStage?

A **SystemStage** is a processing step that takes inputs from earlier stages and produces outputs for later stages.

Typical stages include:

- **Raw data** → cleaned prices, returns
- **Forecasting** → rule outputs
- **Scaling/capping** → standardized forecasts
- **Position sizing** → risk-targeted positions
- **P&L accounting** → account curves

Each stage is _stateless_ in the sense that it does not own the whole system. It only knows its inputs and outputs.

**Example mental model**: “A stage is a node in a DAG that transforms data.”

## What is a System?

A **System** is the orchestrator that:

- Instantiates all stages
- Wires dependencies between stages
- Provides a single user-facing API

It’s responsible for ensuring that outputs are computed in the right order and cached where appropriate.

**Example mental model**: “A workflow manager that runs the entire trading pipeline.”

## How it all fits together

```
Rule (signal logic)  ->  TradingRules (signal collection)
                         |
                         v
SystemStage (Forecasting) -> SystemStage (Scaling) -> SystemStage (Position) -> SystemStage (P&L)
System (orchestrator)
```

## Why this design?

- **Separation of concerns**: Each component does one thing well.
- **Extensibility**: Add a new Rule or Stage without rewriting the pipeline.
- **Testability**: Rules and Stages can be tested independently.
- **Reusability**: Same rules can feed multiple systems or portfolios.

## Where to look next

- [stage.py](stage.py): Base abstraction for pipeline stages
- [forecasting.py](forecasting.py): Forecast generation stage
- [basesystem.py](basesystem.py): System orchestration
- [accounts/](accounts/): P&L and curve logic
