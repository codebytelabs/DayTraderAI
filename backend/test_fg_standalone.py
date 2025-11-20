#!/usr/bin/env python3
"""
Standalone test for Fear & Greed Index - Multi-source validation
"""

import requests
from datetime import datetime
from statistics import median
import re

def test_cnn_api():
    """Test CNN Fear & Greed API (primary)"""
    print("\n🧪 Testing CNN API (Primary)")
    print("-" * 60)
    
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'fear_and_greed' in data:
            current_data = data['fear_and_greed']
            if current_data and len(current_data) > 0:
                latest = current_data[-1]
                score = int(latest['y'])
                print(f"✅ CNN API: {score}/100 ({classify_score(score)})")
                return score
        
        print("❌ CNN API: No data")
        return None
        
    except Exception as e:
        print(f"❌ CNN API: {e}")
        return None

def test_cnn_graphdata():
    """Test CNN Fear & Greed API (alternative)"""
    print("\n🧪 Testing CNN Graphdata (Alternative)")
    print("-" * 60)
    
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        url = f"https://production.dataviz.cnn.io/index/fearandgreed/graphdata/{today}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'fear_and_greed' in data:
            fg_data = data['fear_and_greed']
            
            # Try score field
            if isinstance(fg_data, dict) and 'score' in fg_data:
                score = int(fg_data['score'])
                print(f"✅ CNN Graphdata: {score}/100 ({classify_score(score)})")
                return score
            
            # Try array format
            elif isinstance(fg_data, list) and len(fg_data) > 0:
                latest = fg_data[-1]
                if 'y' in latest:
                    score = int(latest['y'])
                    print(f"✅ CNN Graphdata: {score}/100 ({classify_score(score)})")
                    return score
        
        print("❌ CNN Graphdata: No data")
        return None
        
    except Exception as e:
        print(f"❌ CNN Graphdata: {e}")
        return None

def test_feargreedindex_org():
    """Test feargreedindex.org"""
    print("\n🧪 Testing FearGreedIndex.org")
    print("-" * 60)
    
    try:
        url = "https://feargreedindex.org/"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html = response.text
        
        # Try pattern 1: "score":34
        pattern1 = r'"score"\s*:\s*(\d{1,3})'
        match = re.search(pattern1, html)
        if match:
            score = int(match.group(1))
            if 0 <= score <= 100:
                print(f"✅ FearGreedIndex.org: {score}/100 ({classify_score(score)})")
                return score
        
        # Try pattern 2: data-score="34"
        pattern2 = r'data-score="(\d{1,3})"'
        match = re.search(pattern2, html)
        if match:
            score = int(match.group(1))
            if 0 <= score <= 100:
                print(f"✅ FearGreedIndex.org: {score}/100 ({classify_score(score)})")
                return score
        
        print("❌ FearGreedIndex.org: No score found")
        return None
        
    except Exception as e:
        print(f"❌ FearGreedIndex.org: {e}")
        return None

def classify_score(score):
    """Classify score"""
    if score <= 25:
        return 'extreme_fear'
    elif score <= 45:
        return 'fear'
    elif score <= 55:
        return 'neutral'
    elif score <= 75:
        return 'greed'
    else:
        return 'extreme_greed'

def show_trading_impact(score):
    """Show trading impact"""
    print(f"\n🎯 Trading Impact for {score}/100:")
    print("-" * 60)
    
    if score < 15:
        print(f"   ⛔ Extreme fear - All shorts blocked")
    elif score < 35:
        print(f"   ⚠️  Fear - Shorts need 3+ confirmations")
    elif score < 55:
        print(f"   ✅ Neutral - Normal trading")
    elif score < 75:
        print(f"   📈 Greed - Favorable for shorts")
    else:
        print(f"   🚀 Extreme greed - Very favorable for shorts")

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 Multi-Source Fear & Greed Index Test")
    print("=" * 60)
    
    scores = []
    sources = []
    
    # Test all sources
    score1 = test_cnn_api()
    if score1 is not None:
        scores.append(score1)
        sources.append('CNN API')
    
    score2 = test_cnn_graphdata()
    if score2 is not None:
        scores.append(score2)
        sources.append('CNN Graphdata')
    
    score3 = test_feargreedindex_org()
    if score3 is not None:
        scores.append(score3)
        sources.append('FearGreedIndex.org')
    
    # Show results
    print("\n" + "=" * 60)
    print("📊 Results Summary")
    print("=" * 60)
    
    if len(scores) >= 2:
        consensus = int(median(scores))
        print(f"\n✅ Consensus Score: {consensus}/100 ({classify_score(consensus)})")
        print(f"   Sources: {len(scores)}/3 working")
        print(f"   All scores: {scores}")
        print(f"   Sources used: {', '.join(sources)}")
        show_trading_impact(consensus)
    elif len(scores) == 1:
        print(f"\n⚠️  Single Source: {scores[0]}/100 ({classify_score(scores[0])})")
        print(f"   Source: {sources[0]}")
        show_trading_impact(scores[0])
    else:
        print(f"\n❌ All sources failed - would use default neutral (50/100)")
        show_trading_impact(50)
    
    print("\n" + "=" * 60)
