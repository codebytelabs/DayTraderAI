# Requirements Document

## Introduction

This spec addresses three critical runtime issues in the DayTraderAI application that prevent proper functionality: markdown rendering in the copilot chat, portfolio equity curve display, and empty Trade Analysis & Live Logs panels. The backend is running and serving data correctly (23 portfolio history points, positions, orders, logs, advisories, analyses), but the frontend is not properly rendering or displaying this data to the user.

## Glossary

- **System**: The DayTraderAI web application
- **Backend**: The FastAPI Python server running on port 8006
- **Frontend**: The React/Vite application running on port 3000
- **Copilot Chat**: The conversational AI interface for trading operations
- **Portfolio Equity Curve**: The candlestick chart showing account value over time
- **Trade Analysis Panel**: The UI component displaying AI-generated trade rationales
- **Live Logs Panel**: The UI component showing system activity logs
- **MarkdownRenderer**: React component for rendering formatted markdown text

## Requirements

### Requirement 1: Markdown Rendering in Copilot Chat

**User Story:** As a trader, I want copilot responses to display with proper formatting (headers, lists, bold text, code blocks) so that I can easily read and understand the information.

#### Acceptance Criteria

1. WHEN THE System receives a copilot response containing markdown syntax, THE MarkdownRenderer SHALL render headers with appropriate font sizes and weights
2. WHEN THE System receives a copilot response containing markdown lists, THE MarkdownRenderer SHALL render list items with proper indentation and bullet points
3. WHEN THE System receives a copilot response containing bold or italic text, THE MarkdownRenderer SHALL apply appropriate text styling
4. WHEN THE System receives a copilot response containing inline code or code blocks, THE MarkdownRenderer SHALL render code with monospace font and distinct background color
5. WHEN THE System receives a copilot response containing links, THE MarkdownRenderer SHALL render clickable hyperlinks that open in new tabs

### Requirement 2: Portfolio Equity Curve Display

**User Story:** As a trader, I want to see my actual portfolio performance over time in a candlestick chart so that I can track my trading results visually.

#### Acceptance Criteria

1. WHEN THE Backend is running and connected, THE System SHALL fetch portfolio history data from the `/api/performance` endpoint
2. WHEN THE System receives portfolio history data, THE PerformanceChart SHALL display candlestick bars representing equity values over time
3. WHEN THE user selects a timeframe (1Min, 1H, 1D), THE System SHALL fetch and display portfolio data for that timeframe
4. WHEN THE portfolio history data is unavailable, THE System SHALL display current equity as a single data point
5. WHEN THE user hovers over a candlestick, THE System SHALL display a tooltip with open, high, low, close, P/L, win rate, and profit factor values

### Requirement 3: Trade Analysis Panel Population

**User Story:** As a trader, I want to see AI-generated analysis and rationale for each trade so that I can understand the reasoning behind trading decisions.

#### Acceptance Criteria

1. WHEN THE Backend generates a trade analysis, THE System SHALL fetch analysis data from the `/api/analyses` endpoint
2. WHEN THE System receives trade analyses, THE TradeAnalysisLog SHALL display the most recent 10 analyses in reverse chronological order
3. WHEN THE TradeAnalysisLog displays an analysis, THE System SHALL show the symbol, side (LONG/SHORT), timestamp, AI-generated rationale, and trade metrics
4. WHEN THE TradeAnalysisLog has no analyses to display, THE System SHALL show a message "Awaiting first trade signal for AI analysis..."
5. WHEN THE Backend is disconnected, THE System SHALL continue displaying previously fetched analyses

### Requirement 4: Live Logs Panel Population

**User Story:** As a trader, I want to see real-time system logs so that I can monitor trading activity and troubleshoot issues.

#### Acceptance Criteria

1. WHEN THE Backend generates log entries, THE System SHALL fetch logs from the `/api/logs` endpoint
2. WHEN THE System receives log entries, THE LogFeed SHALL display the most recent logs with timestamps, levels, and messages
3. WHEN THE System receives a new log entry via WebSocket, THE LogFeed SHALL append the entry to the display in real-time
4. WHEN THE LogFeed displays a log entry, THE System SHALL color-code the entry based on level (info, warning, error, debug)
5. WHEN THE Backend is disconnected, THE System SHALL display a message indicating logs are unavailable

### Requirement 5: WebSocket Connection Stability

**User Story:** As a trader, I want stable WebSocket connections so that I receive real-time updates without disconnections.

#### Acceptance Criteria

1. WHEN THE WebSocket connection is established, THE System SHALL handle the initial snapshot message without disconnecting
2. WHEN THE WebSocket receives large snapshot payloads, THE System SHALL process them without connection errors
3. WHEN THE WebSocket connection closes unexpectedly, THE System SHALL automatically reconnect within 5 seconds
4. WHEN THE WebSocket connection fails repeatedly, THE System SHALL fall back to HTTP polling every 10 seconds
5. WHEN THE System falls back to polling, THE System SHALL display a status indicator showing "Streaming unavailable"
