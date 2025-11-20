# Property Portfolio Strategy Dashboard

A Streamlit-based dashboard designed to help property investors model and visualize complex portfolio strategies. This tool allows you to simulate scenarios such as demolishing an existing property to build, refinancing, and purchasing new assets, while tracking cash flow, equity, and LVR (Loan to Value Ratio) over time.

## Features

- **Portfolio Inputs**: Easily input current asset values, debt, and future strategy parameters (build costs, new purchase price).
- **Strategy Simulation**: Model a "Build & Buy" strategy and see the impact on your total assets and debt.
- **Cash Flow Analysis**:
    - Compare Interest Only vs. Principal & Interest repayments.
    - Calculate the "Rental Gap" (shortfall) between estimated rent and loan repayments.
    - **Buffer Strategy**: Visualize how long a borrowed cash buffer will last to cover negative gearing shortfalls.
- **Risk Simulation (Capitalizing Interest)**:
    - Simulate a "Debt Spiral" vs "Growth" scenario over 5-20 years.
    - Visualize Asset vs. Debt growth and LVR projections.
    - Warnings for high LVR and negative equity growth.
- **Real-time Metrics**: Instant feedback on Net Equity, Future LVR, and Total Debt.

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management, but can also be run with standard `pip`.

### Prerequisites

- Python 3.12+

### Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd property-intelligence
    ```

2.  **Install dependencies:**

    Using `uv` (Recommended):
    ```bash
    uv sync
    ```

    Using `pip`:
    ```bash
    pip install streamlit pandas
    ```

## Usage

Run the Streamlit application:

```bash
streamlit run app.py
```

The dashboard will open in your default web browser (usually at `http://localhost:8501`).

## Disclaimer

**Educational Purpose Only**: This tool is for educational and informational purposes only. It does not constitute financial advice. Property investment involves significant risk. You should always consult with a qualified financial advisor, mortgage broker, and accountant before making any investment decisions.
