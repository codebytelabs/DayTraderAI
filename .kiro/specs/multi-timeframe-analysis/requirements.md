# Requirements Document

## Introduction

This document specifies the requirements for a Multi-Timeframe Analysis (MTA) system that enhances the DayTraderAI trading bot by incorporating signals from multiple timeframes (1-minute, 5-minute, 15-minute, and daily) to improve trade entry decisions, increase win rate, and reduce losses. Research shows that multi-timeframe analysis can improve win rates from 45% to 62%+ and risk-adjusted returns by 23%.

## Glossary

- **MTA_System**: The Multi-Timeframe Analysis system that aggregates and weights signals from multiple timeframes
- **Higher_Timeframe (HTF)**: Timeframes larger than the execution timeframe (5-min, 15-min, daily) used for trend confirmation
- **Lower_Timeframe (LTF)**: The 1-minute execution timeframe used for precise entry timing
- **Timeframe_Alignment**: Condition where signals from multiple timeframes agree on direction
- **Trend_Bias**: The dominant market direction determined by higher timeframes
- **MTF_Confidence**: A weighted confidence score combining signals from all analyzed timeframes
- **Support_Resistance_Zone**: Price levels identified on higher timeframes where price has historically reversed
- **Timeframe_Weight**: The relative importance assigned to each timeframe in the final signal calculation

## Requirements

### Requirement 1

**User Story:** As a trader, I want the system to fetch and analyze data from multiple timeframes (1-min, 5-min, 15-min, daily), so that I can make better-informed trading decisions based on the bigger picture.

#### Acceptance Criteria

1. WHEN the MTA_System initializes THEN the MTA_System SHALL fetch historical bars for 1-minute, 5-minute, 15-minute, and daily timeframes for all watchlist symbols
2. WHEN the MTA_System updates market data THEN the MTA_System SHALL refresh 5-minute bars every 5 minutes, 15-minute bars every 15 minutes, and daily bars once per trading day
3. WHEN fetching multi-timeframe data THEN the MTA_System SHALL cache the data efficiently to minimize API calls and latency
4. WHEN a timeframe data fetch fails THEN the MTA_System SHALL use the most recent cached data and log a warning
5. WHEN calculating indicators THEN the MTA_System SHALL compute EMA, RSI, MACD, ADX, and VWAP for each timeframe independently

### Requirement 2

**User Story:** As a trader, I want the system to determine the primary trend direction from higher timeframes, so that I only trade in the direction of the dominant trend.

#### Acceptance Criteria

1. WHEN analyzing the 15-minute timeframe THEN the MTA_System SHALL determine trend direction using EMA(50) and EMA(200) relationship
2. WHEN the 15-minute EMA(50) is above EMA(200) THEN the MTA_System SHALL classify the Trend_Bias as bullish
3. WHEN the 15-minute EMA(50) is below EMA(200) THEN the MTA_System SHALL classify the Trend_Bias as bearish
4. WHEN the 15-minute EMAs are within 0.1% of each other THEN the MTA_System SHALL classify the Trend_Bias as neutral
5. WHEN a 1-minute signal contradicts the 15-minute Trend_Bias THEN the MTA_System SHALL reject the signal
6. WHEN the daily trend aligns with the 15-minute trend THEN the MTA_System SHALL increase the MTF_Confidence by 15 points

### Requirement 3

**User Story:** As a trader, I want the system to confirm momentum alignment across timeframes before entering a trade, so that I avoid false signals and whipsaws.

#### Acceptance Criteria

1. WHEN evaluating a buy signal THEN the MTA_System SHALL require RSI above 50 on at least two of three timeframes (1-min, 5-min, 15-min)
2. WHEN evaluating a sell signal THEN the MTA_System SHALL require RSI below 50 on at least two of three timeframes (1-min, 5-min, 15-min)
3. WHEN MACD histogram is positive on 5-minute and 15-minute timeframes THEN the MTA_System SHALL add bullish momentum confirmation
4. WHEN MACD histogram is negative on 5-minute and 15-minute timeframes THEN the MTA_System SHALL add bearish momentum confirmation
5. WHEN momentum indicators conflict across timeframes THEN the MTA_System SHALL reduce MTF_Confidence by 20 points
6. WHEN all three timeframes show aligned momentum THEN the MTA_System SHALL increase MTF_Confidence by 25 points

### Requirement 4

**User Story:** As a trader, I want the system to identify support and resistance levels from higher timeframes, so that I can set better stop losses and profit targets.

#### Acceptance Criteria

1. WHEN analyzing the 15-minute chart THEN the MTA_System SHALL identify swing highs and swing lows from the last 50 bars as Support_Resistance_Zones
2. WHEN analyzing the daily chart THEN the MTA_System SHALL identify the previous day's high, low, and close as key levels
3. WHEN a buy entry is near a 15-minute resistance level (within 0.3%) THEN the MTA_System SHALL reduce position size by 30%
4. WHEN a sell entry is near a 15-minute support level (within 0.3%) THEN the MTA_System SHALL reduce position size by 30%
5. WHEN setting stop loss THEN the MTA_System SHALL place stops beyond the nearest 15-minute support/resistance level
6. WHEN setting profit target THEN the MTA_System SHALL use the next 15-minute support/resistance level as the primary target

### Requirement 5

**User Story:** As a trader, I want the system to calculate a weighted confidence score from all timeframes, so that I can prioritize high-probability setups.

#### Acceptance Criteria

1. WHEN calculating MTF_Confidence THEN the MTA_System SHALL weight timeframes as: 15-min (40%), 5-min (35%), 1-min (25%)
2. WHEN the 15-minute trend is strong (ADX > 25) THEN the MTA_System SHALL increase the 15-minute weight to 50%
3. WHEN all timeframes align on direction THEN the MTA_System SHALL add a 20-point alignment bonus to MTF_Confidence
4. WHEN MTF_Confidence is below 60 THEN the MTA_System SHALL reject the trade signal
5. WHEN MTF_Confidence is above 80 THEN the MTA_System SHALL allow increased position sizing up to 1.5x normal
6. WHEN MTF_Confidence is between 60-70 THEN the MTA_System SHALL reduce position size to 0.7x normal

### Requirement 6

**User Story:** As a trader, I want the system to analyze volume patterns across timeframes, so that I can confirm genuine price movements.

#### Acceptance Criteria

1. WHEN evaluating a signal THEN the MTA_System SHALL compare current volume to the 20-period average on each timeframe
2. WHEN 5-minute volume is above 1.5x average during a signal THEN the MTA_System SHALL add volume confirmation
3. WHEN 15-minute volume is below 0.7x average THEN the MTA_System SHALL reduce MTF_Confidence by 10 points
4. WHEN volume is increasing on higher timeframes while price moves in signal direction THEN the MTA_System SHALL add 10 points to MTF_Confidence
5. WHEN volume diverges from price (price up, volume down) THEN the MTA_System SHALL flag potential reversal risk

### Requirement 7

**User Story:** As a trader, I want the system to detect timeframe conflicts and handle them appropriately, so that I avoid entering trades during uncertain market conditions.

#### Acceptance Criteria

1. WHEN 1-minute signal is bullish but 15-minute trend is bearish THEN the MTA_System SHALL reject the signal
2. WHEN 5-minute momentum conflicts with 15-minute momentum THEN the MTA_System SHALL wait for alignment before entry
3. WHEN more than one timeframe shows ranging/choppy conditions (ADX < 20) THEN the MTA_System SHALL reduce position size by 40%
4. WHEN all timeframes show trending conditions (ADX > 25) THEN the MTA_System SHALL allow full position sizing
5. WHEN timeframe conflict is detected THEN the MTA_System SHALL log the conflict details for analysis

### Requirement 8

**User Story:** As a trader, I want the system to provide clear logging of multi-timeframe analysis, so that I can understand why trades were taken or rejected.

#### Acceptance Criteria

1. WHEN a signal is generated THEN the MTA_System SHALL log the trend direction from each timeframe
2. WHEN a signal is rejected due to timeframe conflict THEN the MTA_System SHALL log which timeframes conflicted and why
3. WHEN MTF_Confidence is calculated THEN the MTA_System SHALL log the contribution from each timeframe
4. WHEN a trade is entered THEN the MTA_System SHALL log the Support_Resistance_Zones used for stops and targets
5. WHEN the system updates higher timeframe data THEN the MTA_System SHALL log the refresh timestamp and data quality

### Requirement 9

**User Story:** As a trader, I want the system to be configurable, so that I can enable/disable multi-timeframe analysis and adjust weights.

#### Acceptance Criteria

1. WHEN the configuration has ENABLE_MTF_ANALYSIS set to False THEN the MTA_System SHALL bypass multi-timeframe checks and use single-timeframe logic
2. WHEN the configuration specifies custom timeframe weights THEN the MTA_System SHALL use those weights instead of defaults
3. WHEN the configuration specifies a minimum MTF_Confidence threshold THEN the MTA_System SHALL use that threshold for trade filtering
4. WHEN the configuration enables MTF_STRICT_MODE THEN the MTA_System SHALL require all timeframes to align before entry
5. WHEN the configuration is updated THEN the MTA_System SHALL apply changes without requiring a restart
