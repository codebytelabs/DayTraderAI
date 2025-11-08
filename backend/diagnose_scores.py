"""Diagnose opportunity scores for current watchlist."""

import asyncio
from core.state import trading_state
from scanner.opportunity_scorer import OpportunityScorer
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def diagnose_scores():
    """Check scores for all symbols in watchlist."""
    
    watchlist = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMD', 'GOOG', 'AMZN', 'META']
    
    print("\n" + "="*80)
    print("OPPORTUNITY SCORE DIAGNOSIS")
    print("="*80)
    
    for symbol in watchlist:
        features = trading_state.get_features(symbol)
        
        if not features:
            print(f"\n{symbol}: No features available")
            continue
        
        scores = OpportunityScorer.calculate_total_score(features)
        
        print(f"\n{symbol}: {scores['total_score']:.1f}/110 (Grade: {scores['grade']})")
        print(f"  Technical:  {scores['technical_score']:.1f}/40")
        print(f"  Momentum:   {scores['momentum_score']:.1f}/25")
        print(f"  Volume:     {scores['volume_score']:.1f}/20")
        print(f"  Volatility: {scores['volatility_score']:.1f}/15")
        print(f"  Regime:     {scores['regime_score']:.1f}/10")
        
        # Show key features
        print(f"  Key metrics:")
        print(f"    EMA diff: {features.get('ema_diff_pct', 0):.2f}%")
        print(f"    RSI: {features.get('rsi', 0):.1f}")
        print(f"    ADX: {features.get('adx', 0):.1f}")
        print(f"    Volume ratio: {features.get('volume_ratio', 0):.2f}x")
        print(f"    Regime: {features.get('market_regime', 'unknown')}")
    
    print("\n" + "="*80)
    print(f"Minimum score needed: 60.0")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(diagnose_scores())
