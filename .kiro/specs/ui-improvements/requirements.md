# Requirements Document

## Introduction

This document outlines requirements for improving the DayTraderAI user interface by removing unnecessary frontend model configuration displays and implementing a proper portfolio equity curve chart that displays real account equity data from Alpaca with multiple timeframe options.

## Glossary

- **Frontend**: The React-based user interface of the DayTraderAI application
- **Backend**: The Python FastAPI server that manages trading operations and AI model selection
- **Header Component**: The top navigation bar displaying connection statuses and settings
- **Portfolio Equity Curve**: A candlestick chart showing the account equity over time with OHLC (Open, High, Low, Close) data
- **Alpaca API**: The trading platform API that provides real-time and historical account data
- **Timeframe**: The interval for aggregating equity data (1 minute, 1 hour, 1 day)
- **PerformanceChart Component**: The React component that renders the portfolio equity visualization

## Requirements

### Requirement 1

**User Story:** As a user, I want the header to only show relevant connection statuses without displaying AI model configuration details, so that the interface is cleaner and focuses on what I need to monitor.

#### Acceptance Criteria

1. WHEN the Header Component renders, THE Frontend SHALL display connection status indicators for Alpaca, Supabase, Perplexity, and OpenRouter services
2. THE Frontend SHALL NOT display the active AI model provider label in the header
3. THE Frontend SHALL NOT display model names in the header
4. THE Frontend SHALL maintain the Settings button for accessing configuration options
5. THE Frontend SHALL preserve all existing connection status indicator functionality

### Requirement 2

**User Story:** As a trader, I want to see my actual portfolio equity history from Alpaca displayed as a candlestick chart, so that I can visualize my account performance over time with accurate data.

#### Acceptance Criteria

1. WHEN the Backend receives a request for performance data, THE Backend SHALL fetch real account portfolio history from the Alpaca API
2. THE Backend SHALL transform Alpaca portfolio history into OHLC format with timestamp, open, high, low, close equity values
3. THE Backend SHALL return portfolio equity data with associated metrics including daily P/L, win rate, and profit factor
4. THE Frontend SHALL display the portfolio equity data as a candlestick chart in the PerformanceChart Component
5. IF Alpaca portfolio history is unavailable, THEN THE Backend SHALL return the current equity as a single data point

### Requirement 3

**User Story:** As a trader, I want to switch between different timeframes (1 minute, 1 hour, 1 day) for viewing my portfolio equity curve, so that I can analyze my performance at different granularities.

#### Acceptance Criteria

1. THE Frontend SHALL display timeframe selector buttons with options for "1min", "1H", and "1D" intervals
2. WHEN a user clicks a timeframe button, THE Frontend SHALL request performance data for the selected timeframe from the Backend
3. THE Backend SHALL accept a timeframe parameter in the performance endpoint
4. THE Backend SHALL fetch and aggregate Alpaca portfolio history according to the requested timeframe
5. THE Frontend SHALL default to displaying the "1D" (1 day) timeframe on initial load
6. THE Frontend SHALL visually indicate which timeframe is currently selected
7. THE PerformanceChart Component SHALL update to display data for the selected timeframe without page refresh
