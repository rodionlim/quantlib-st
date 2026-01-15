# Systems: Rules, TradingRules, SystemStage, System

This folder mirrors the core architecture from `systems/` in the original codebase. The key idea is a *pipeline* that turns raw data into forecasts, positions, and P&L through composable stages.

## Mental Model (High Level)

Think of a trading system as a production line:

1. **Rules**: Pure functions that transform market data into *signals* (e.g., trend, carry).
2. **TradingRules**: A registry/wrapper that manages a *set of Rules* and exposes a consistent interface.
3. **SystemStage**: A pipeline step that consumes outputs from earlier stages and produces new outputs.
4. **System**: The orchestrator that wires stages together into a full strategy.

## What is a Rule?

A **Rule** is the smallest unit of trading logic. It takes price data (and possibly other inputs) and returns a *forecast series*.

- Input: prices, instrument metadata, config params
- Output: a forecast (typically normalized and capped)
- Purpose: create a predictive signal in isolation

**Example mental model**: “If the 64-day moving average is above the 256-day average, produce a positive forecast.”

## What is TradingRules?

**TradingRules** is a container for multiple Rule functions, providing:

- A single interface to run or retrieve specific rules
- Metadata (names, parameters)
- Consistent access patterns for the pipeline

**Example mental model**: “A toolbox that holds all my signals and lets the system query them by name.”

## What is a SystemStage?

A **SystemStage** is a processing step that takes inputs from earlier stages and produces outputs for later stages.

Typical stages include:

- **Raw data** → cleaned prices, returns
- **Forecasting** → rule outputs
- **Scaling/capping** → standardized forecasts
- **Position sizing** → risk-targeted positions
- **P&L accounting** → account curves

Each stage is *stateless* in the sense that it does not own the whole system. It only knows its inputs and outputs.

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
