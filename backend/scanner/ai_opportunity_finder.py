"""AI-Driven Opportunity Finder using Perplexity AI.

Uses Perplexity to research market conditions and identify the best trading opportunities.
"""

import asyncio
import json
import re
from typing import List, Dict, Optional
from datetime import datetime
from advisory.perplexity import PerplexityClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AIOpportunityFinder:
    """Use Perplexity AI to discover trading opportunities."""
    
    def __init__(self):
        self.perplexity = PerplexityClient()
        self.last_discovery_time = None
        self.last_opportunities = []
        self.last_opportunities_detailed = []  # Store full metadata
        self._cache_duration = 900  # 15 minutes cache
        
        # Sentiment data from combined query
        self.last_sentiment_score = None
        self.last_sentiment_class = None
        
        logger.info("AI Opportunity Finder initialized with multi-cap support")
    
    def _extract_sentiment(self, content: str) -> tuple:
        """Extract sentiment score and classification from AI response."""
        import re
        
        sentiment_score = 50  # Default neutral
        sentiment_class = "neutral"
        
        try:
            # CRITICAL: Extract the ACTUAL CNN score, not reference numbers or other metrics
            # The score should be a simple integer 0-100
            
            score_patterns = [
                # Pattern 1: "**18**" (markdown bold)
                r'\*\*(\d+)\*\*\s*\((?:Extreme Fear|Extreme Greed|Fear|Greed|Neutral)\)',
                # Pattern 2: "Score:** **18**"
                r'[Ss]core[:\s*]+\*\*(\d+)\*\*',
                # Pattern 3: "PRIMARY SCORE: 18"
                r'PRIMARY\s+SCORE[:\s*]+(\d+)',
                # Pattern 4: "Fear and Greed Index is 18" or "Index: 18"
                r'(?:Fear\s*(?:and|&)\s*Greed\s+)?Index\s+is\s+(\d+)',
                # Pattern 5: "score: 18" or "rating: 18"
                r'(?:score|rating)[:\s]+(\d+)(?:\s|$|[^\d])',
                # Pattern 6: "18/100"
                r'(\d+)/100',
                # Pattern 7: "18 out of 100"
                r'(\d+)\s+out of 100',
                # Pattern 8: Number followed by classification (e.g., "18 - Extreme Fear")
                r'(\d+)\s*[-–—]\s*(?:Extreme Fear|Extreme Greed|Fear|Greed|Neutral)',
            ]
            
            for i, pattern in enumerate(score_patterns, 1):
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    extracted = int(match.group(1))
                    # Validate: Fear & Greed is 0-100
                    if 0 <= extracted <= 100:
                        sentiment_score = extracted
                        logger.info(f"✅ Extracted score {sentiment_score} using pattern {i}: '{match.group(0)}'")
                        break
                    else:
                        logger.warning(f"⚠️  Pattern {i} extracted {extracted} (out of range 0-100), trying next pattern")
            
            # Try to extract classification
            class_patterns = [
                r'(Extreme Fear|Extreme Greed|Fear|Greed|Neutral)',
            ]
            
            for pattern in class_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    sentiment_class = match.group(1).lower().replace(' ', '_')
                    break
            
            logger.info(f"✅ Final sentiment: {sentiment_score}/100 ({sentiment_class})")
            
        except Exception as e:
            logger.error(f"Error extracting sentiment: {e}")
        
        return sentiment_score, sentiment_class
    
    def get_current_sentiment(self) -> dict:
        """Get current market sentiment from last AI discovery."""
        return {
            'score': self.last_sentiment_score or 50,
            'classification': self.last_sentiment_class or 'neutral',
            'timestamp': self.last_discovery_time.isoformat() if self.last_discovery_time else None
        }
    
    def _is_cache_valid(self) -> bool:
        """Check if cached opportunities are still valid."""
        if not self.last_discovery_time or not self.last_opportunities:
            return False
        
        # Check if cache has expired
        time_since_last = (datetime.now() - self.last_discovery_time).total_seconds()
        return time_since_last < self._cache_duration
    
    async def discover_opportunities(self, max_symbols: int = 20, allowed_caps: Dict = None) -> List[str]:
        """
        Use AI to discover the best trading opportunities right now.
        
        Args:
            max_symbols: Maximum number of symbols to return
            allowed_caps: Dict of allowed market caps {'large_caps': True, 'mid_caps': False, 'small_caps': False}
            
        Returns:
            List of stock symbols recommended by AI
        """
        try:
            from config import settings
            
            # Check cache first
            if self._is_cache_valid():
                logger.info(f"🔄 Using cached opportunities ({len(self.last_opportunities)} symbols)")
                return self.last_opportunities[:max_symbols]
            
            logger.info("🤖 AI discovering trading opportunities (Perplexity for real-time web search)...")
            
            # Build comprehensive research query with market cap filtering
            query = self._build_discovery_query(allowed_caps=allowed_caps)
            
            result = None
            primary_failed = False
            
            # OPPORTUNITY DISCOVERY ALWAYS USES PERPLEXITY (real-time web search)
            # Primary: Perplexity via OpenRouter (perplexity/sonar-pro)
            # Fallback: Native Perplexity API (sonar-pro)
            #
            # NOTE: OpenRouter's Grok/GPT models do NOT have real-time data access
            # Only Perplexity has web search capability for finding current catalysts
            
            # PRIMARY: Perplexity via OpenRouter
            try:
                from advisory.openrouter_client import OpenRouterClient
                perplexity_model = getattr(settings, 'openrouter_perplexity_model', 'perplexity/sonar-pro')
                logger.info(f"🤖 AI discovering opportunities using OPENROUTER ({perplexity_model})...")
                openrouter_perplexity = OpenRouterClient()
                # Override model for this request to use Perplexity's sonar-pro
                openrouter_perplexity.model = perplexity_model
                result = await openrouter_perplexity.search(query)
                    
                if not result or not result.get('content'):
                    logger.warning("OpenRouter Perplexity returned no content")
                    primary_failed = True
                else:
                    # Quick check if response has any stock symbols
                    # Even if Perplexity adds disclaimers, we can still extract symbols
                    content = result['content']
                    quick_symbols = re.findall(r'\b([A-Z]{2,5})\b', content)
                    # Filter out common non-stock words
                    non_stocks = {'THE', 'AND', 'FOR', 'WITH', 'FROM', 'THIS', 'THAT', 'HAVE', 'ARE', 'NOT', 
                                  'BUT', 'CAN', 'ALL', 'HAS', 'HAD', 'WAS', 'WILL', 'MAY', 'FDA', 'CEO', 
                                  'IPO', 'ETF', 'NYSE', 'SEC', 'AI', 'ML', 'API', 'USA', 'USD', 'EPS'}
                    valid_symbols = [s for s in quick_symbols if s not in non_stocks and len(s) >= 2]
                    
                    if len(valid_symbols) < 3:
                        logger.warning(f"⚠️ OpenRouter Perplexity returned only {len(valid_symbols)} symbols - trying native fallback")
                        primary_failed = True
                    else:
                        logger.info(f"✅ OpenRouter Perplexity found {len(valid_symbols)} potential symbols")
                    
            except Exception as e:
                logger.error(f"OpenRouter Perplexity failed: {e}")
                primary_failed = True
            
            # FALLBACK: Native Perplexity API
            if primary_failed:
                logger.info("🔄 Attempting fallback via NATIVE PERPLEXITY API...")
                try:
                    result = await self.perplexity.search(query)
                        
                    if not result or not result.get('content'):
                        logger.error("Native Perplexity also failed")
                        return self._get_fallback_symbols()
                    
                    # Quick check if response has any stock symbols
                    content = result['content']
                    quick_symbols = re.findall(r'\b([A-Z]{2,5})\b', content)
                    non_stocks = {'THE', 'AND', 'FOR', 'WITH', 'FROM', 'THIS', 'THAT', 'HAVE', 'ARE', 'NOT', 
                                  'BUT', 'CAN', 'ALL', 'HAS', 'HAD', 'WAS', 'WILL', 'MAY', 'FDA', 'CEO', 
                                  'IPO', 'ETF', 'NYSE', 'SEC', 'AI', 'ML', 'API', 'USA', 'USD', 'EPS'}
                    valid_symbols = [s for s in quick_symbols if s not in non_stocks and len(s) >= 2]
                    
                    if len(valid_symbols) < 3:
                        logger.warning(f"⚠️ Native Perplexity returned only {len(valid_symbols)} symbols - using fallback")
                        return self._get_fallback_symbols()
                        
                    logger.info(f"✅ Native Perplexity found {len(valid_symbols)} potential symbols")
                    
                except Exception as e:
                    logger.error(f"Native Perplexity failed: {e}")
                    return self._get_fallback_symbols()
            
            logger.info(f"✅ Got AI response: {len(result['content'])} chars")
            
            # Log AI response analysis
            self._log_ai_response_analysis(result)
            
            content = result['content']
            citations = result.get('citations', [])
            
            logger.info(f"AI research completed with {len(citations)} sources")
            
            # Extract sentiment from the same response
            sentiment_score, sentiment_class = self._extract_sentiment(content)
            
            # Extract symbols from AI response
            symbols = self._extract_symbols(content)
            
            if not symbols:
                logger.warning("No symbols extracted from AI response")
                return self._get_fallback_symbols()
            
            # CRITICAL: If AI returns too few symbols, merge with fallback
            # We want at least 15 symbols for proper opportunity scanning
            MIN_SYMBOLS = 15
            if len(symbols) < MIN_SYMBOLS:
                logger.warning(f"⚠️ AI returned only {len(symbols)} symbols - merging with fallback to reach {MIN_SYMBOLS}")
                fallback = self._get_fallback_symbols()
                # Add fallback symbols that aren't already in the list
                for fb_symbol in fallback:
                    if fb_symbol not in symbols:
                        symbols.append(fb_symbol)
                    if len(symbols) >= max_symbols:
                        break
                logger.info(f"✅ Merged to {len(symbols)} symbols (AI + fallback)")
            
            # Limit to max symbols
            symbols = symbols[:max_symbols]
            
            # Cache results (both opportunities and sentiment)
            self.last_discovery_time = datetime.now()
            self.last_opportunities = symbols  # Store just the symbol list for caching
            self.last_sentiment_score = sentiment_score
            self.last_sentiment_class = sentiment_class
            
            logger.info(f"📊 Market Sentiment: {sentiment_score}/100 ({sentiment_class})")
            logger.info(f"✅ AI discovered {len(symbols)} opportunities: {', '.join(symbols)}")
            
            return symbols
            
        except Exception as e:
            logger.error(f"Error in AI opportunity discovery: {e}")
            return self._get_fallback_symbols()
    
    def _build_discovery_query(self, allowed_caps: Dict = None) -> str:
        """Build optimized discovery query that works with Perplexity's capabilities.
        
        OPTIMIZED 2025-12-01:
        - Focus on NEWS and CATALYSTS (what Perplexity excels at)
        - Don't ask for real-time prices/volume (Perplexity doesn't have this)
        - Simple format that gets more symbols extracted
        """
        
        # Default: allow all caps
        if allowed_caps is None:
            allowed_caps = {'large_caps': True, 'mid_caps': True, 'small_caps': True}
        
        # Build cap filter text
        cap_focus = []
        if allowed_caps.get('large_caps', True):
            cap_focus.append("large-cap")
        if allowed_caps.get('mid_caps', True):
            cap_focus.append("mid-cap")
        if allowed_caps.get('small_caps', True):
            cap_focus.append("small-cap")
        caps_str = " and ".join(cap_focus) if cap_focus else "all"
        
        # NEWS-FOCUSED PROMPT - asks for concrete data Perplexity can find
        # This version got 51 symbols in testing
        query = f"""What stocks are in the news today? Search for:

1. Stocks with earnings releases this week
2. Stocks with analyst rating changes
3. Stocks with FDA/regulatory news
4. Stocks with unusual volume or price moves
5. Stocks mentioned in financial news headlines
6. Pre-market top gainers and losers

Focus on {caps_str} stocks.

List each stock as:
TICKER: reason it's newsworthy

Provide at least 20 different stock tickers."""

        return query
    
    def _extract_symbols(self, content: str) -> List[str]:
        """
        Extract stock symbols from AI response with tier and direction info.
        
        Args:
            content: AI response text
            
        Returns:
            List of stock symbols with metadata
        """
        all_opportunities = []
        
        try:
            content_upper = content.upper()
            
            # Define tier patterns (handle markdown formatting)
            tiers = {
                'large_cap': ['**LARGE-CAP LONG:**', 'LARGE-CAP LONG:', 'LARGE-CAP LONG', 'LARGE CAP LONG', 'TIER 1 LONG'],
                'mid_cap': ['**MID-CAP LONG:**', 'MID-CAP LONG:', 'MID-CAP LONG', 'MID CAP LONG', 'TIER 2 LONG'],
                'small_cap': ['**SMALL-CAP LONG:**', 'SMALL-CAP LONG:', 'SMALL-CAP LONG', 'SMALL CAP LONG', 'TIER 3 LONG']
            }
            
            # Extract opportunities by tier and direction
            for tier_name, patterns in tiers.items():
                # Find LONG section for this tier
                long_section = self._find_section(content, content_upper, patterns)
                if long_section:
                    long_opps = self._parse_opportunities_with_metadata(long_section, tier_name, 'LONG')
                    all_opportunities.extend(long_opps)
                    logger.info(f"📈 {tier_name.upper()} LONG: {len(long_opps)} opportunities")
                
                # Find SHORT section for this tier
                short_patterns = [p.replace('LONG', 'SHORT') for p in patterns]
                short_section = self._find_section(content, content_upper, short_patterns)
                if short_section:
                    short_opps = self._parse_opportunities_with_metadata(short_section, tier_name, 'SHORT')
                    all_opportunities.extend(short_opps)
                    logger.info(f"📉 {tier_name.upper()} SHORT: {len(short_opps)} opportunities")
            
            # If no tier-specific extraction worked, fallback to old method
            if not all_opportunities:
                logger.warning("Tier-specific extraction failed, using fallback")
                symbols = self._extract_symbols_fallback(content)
                return symbols
            
            # Convert to simple symbol list for backward compatibility
            # But store full metadata for later use
            self.last_opportunities_detailed = all_opportunities
            
            # Remove duplicates while preserving order
            symbols = []
            seen = set()
            for opp in all_opportunities:
                symbol = opp['symbol']
                if symbol not in seen:
                    symbols.append(symbol)
                    seen.add(symbol)
            
            logger.info(f"✅ Total extracted: {len(symbols)} unique opportunities across all tiers")
            
            # Log detailed breakdown by tier and direction
            self._log_detailed_breakdown(all_opportunities)
            
            return symbols
            
        except Exception as e:
            logger.error(f"Error extracting symbols: {e}")
            return self._extract_symbols_fallback(content)
    
    def _find_section(self, content: str, content_upper: str, patterns: List[str]) -> str:
        """Find a section in content by patterns."""
        for pattern in patterns:
            # Remove markdown formatting for search
            search_pattern = pattern.replace('**', '').replace(':', '')
            idx = content_upper.find(search_pattern)
            if idx != -1:
                # Find end of section (next tier or end of content)
                end_markers = ['**LARGE-CAP', '**MID-CAP', '**SMALL-CAP', 'LARGE-CAP', 'MID-CAP', 'SMALL-CAP', 'TIER 1', 'TIER 2', 'TIER 3']
                end_idx = len(content)
                for marker in end_markers:
                    next_idx = content_upper.find(marker.replace('**', ''), idx + len(search_pattern))
                    if next_idx != -1 and next_idx < end_idx:
                        end_idx = next_idx
                
                section = content[idx:end_idx]
                logger.info(f"Found section for pattern '{pattern}': {len(section)} chars")
                return section
        return ""
    
    def _parse_opportunities_with_metadata(self, section: str, tier: str, direction: str) -> List[Dict]:
        """Parse opportunities with full metadata."""
        opportunities = []
        
        # Pattern: Match the new format with pipes: "1. **SYMBOL ($PRICE) | CATALYST: ... | TECHNICAL: ... | VOLUME: Xx | STOP: $X | TARGET: $X"
        patterns = [
            # Format: "1. **FCX ($36.52)** | CATALYST: ..." or "1. **FCX** ($36.52) | ..."
            r'(\d+)\.\s+\*\*([A-Z]{1,5})(?:\*\*)?\s*\(\$?([\d.]+)\)(?:\*\*)?\s*\|.*?VOLUME:\s*(\d+\.?\d*)x.*?TARGET:\s*\$?([\d.]+)',
            # Format without bold: "1. FCX ($36.52) | CATALYST: ... | VOLUME: 2.3x | TARGET: $38"
            r'(\d+)\.\s+([A-Z]{1,5})\s*\(\$?([\d.]+)\)\s*\|.*?VOLUME:\s*(\d+\.?\d*)x.*?TARGET:\s*\$?([\d.]+)',
            # Fallback: Old comma format "1. SYMBOL - $PRICE, catalyst, volume Xx, Target $TARGET"
            r'(\d+)\.\s+([A-Z]{1,5})\s*[-–]\s*\$?([\d.]+).*?volume\s+(\d+\.?\d*)x.*?[Tt]arget\s+\$?([\d.]+)',
            # Fallback: Bold format "1. **SYMBOL** - $PRICE, volume Xx, Target $TARGET"
            r'(\d+)\.\s+\*\*([A-Z]{1,5})\*\*\s*[-–]\s*\$?([\d.]+).*?volume\s+(\d+\.?\d*)x.*?[Tt]arget\s+\$?([\d.]+)'
        ]
        
        # Debug: Show what we're trying to parse
        logger.info(f"Parsing section ({len(section)} chars): {section[:200]}...")
        
        # Try each pattern
        all_matches = []
        for i, pattern in enumerate(patterns):
            matches = list(re.finditer(pattern, section, re.IGNORECASE | re.DOTALL))
            all_matches.extend(matches)
            if matches:
                logger.info(f"Pattern {i+1} matched {len(matches)} opportunities")
        
        # If no regex matches, try simpler extraction
        if not all_matches:
            logger.info("No regex matches, trying simple symbol extraction")
            simple_matches = self._extract_simple_opportunities(section, tier, direction)
            return simple_matches
        
        for match in all_matches:
            symbol = match.group(2)
            price = float(match.group(3))
            volume_mult = float(match.group(4))
            target = float(match.group(5))
            
            # Extract catalyst (text after "CATALYST:" or between price and "volume")
            full_match = match.group(0)
            catalyst_match = re.search(r'CATALYST:\s*([^|]+)', full_match, re.IGNORECASE)
            if not catalyst_match:
                # Fallback: old format
                catalyst_match = re.search(r'\$?[\d.]+[,\s]+(.+?)(?:volume|vol|VOLUME)', full_match, re.IGNORECASE)
            catalyst = catalyst_match.group(1).strip() if catalyst_match else "Unknown"
            
            if self._is_valid_symbol(symbol):
                opportunities.append({
                    'symbol': symbol,
                    'tier': tier,
                    'direction': direction,
                    'price': price,
                    'target': target,
                    'volume_mult': volume_mult,
                    'catalyst': catalyst,
                    'confidence': 'HIGH' if volume_mult >= 2.0 else 'MEDIUM'
                })
        
        return opportunities
    
    def _extract_simple_opportunities(self, section: str, tier: str, direction: str) -> List[Dict]:
        """Extract opportunities with simpler parsing when regex fails."""
        opportunities = []
        
        # Look for numbered list items with symbols
        # Format: "1. **COST ($621.10)** | CATALYST: ..."
        lines = section.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Pattern: "1. **SYMBOL ($PRICE)** | ..." or "1. SYMBOL ($PRICE) | ..."
            match = re.match(r'(\d+)\.\s+(?:\*\*)?([A-Z]{2,5})\s*\(\$?([\d.]+)\)(?:\*\*)?\s*\|', line)
            if match:
                symbol = match.group(2)
                price = float(match.group(3))
                
                # Extract catalyst and other info
                rest = line[match.end():].strip()
                catalyst_match = re.search(r'CATALYST:\s*([^|]+)', rest, re.IGNORECASE)
                catalyst = catalyst_match.group(1).strip() if catalyst_match else rest[:100]
                
                # Extract volume if available
                volume_match = re.search(r'volume\s+(\d+\.?\d*)x', rest, re.IGNORECASE)
                volume_mult = float(volume_match.group(1)) if volume_match else 1.0
                
                # Extract target if available
                target_match = re.search(r'TARGET:\s*\$?([\d.]+)', rest, re.IGNORECASE)
                target = float(target_match.group(1)) if target_match else price * 1.02  # Default 2% target
                
                if self._is_valid_symbol(symbol):
                    opportunities.append({
                        'symbol': symbol,
                        'tier': tier,
                        'direction': direction,
                        'price': price,
                        'target': target,
                        'volume_mult': volume_mult,
                        'catalyst': catalyst,
                        'confidence': 'HIGH' if volume_mult >= 2.0 else 'MEDIUM'
                    })
        
        logger.info(f"Simple extraction found {len(opportunities)} opportunities")
        
        # Log each opportunity found
        for opp in opportunities:
            logger.info(f"   📊 {tier.upper()} {direction}: {opp['symbol']} @ ${opp['price']:.2f} - {opp['catalyst'][:50]}...")
        
        return opportunities
    
    def _extract_symbols_fallback(self, content: str) -> List[str]:
        """Fallback symbol extraction (old method)."""
        symbols = []
        
        # Try to separate LONG and SHORT sections
        long_symbols = []
        short_symbols = []
        
        content_upper = content.upper()
        
        # Find section markers
        long_start = -1
        short_start = -1
        
        for marker in ['LONG OPPORTUNITIES', 'LONG:', 'LONGS:', 'BUY OPPORTUNITIES', 'BULLISH']:
            idx = content_upper.find(marker)
            if idx != -1:
                long_start = idx
                break
        
        for marker in ['SHORT OPPORTUNITIES', 'SHORT:', 'SHORTS:', 'SELL OPPORTUNITIES', 'BEARISH']:
            idx = content_upper.find(marker)
            if idx != -1:
                short_start = idx
                break
        
        # Extract from sections if found
        if long_start != -1 and short_start != -1:
            long_section = content[long_start:short_start]
            short_section = content[short_start:]
            
            long_symbols = self._extract_symbols_from_text(long_section)
            short_symbols = self._extract_symbols_from_text(short_section)
            
            logger.info(f"📈 Extracted {len(long_symbols)} LONG opportunities: {', '.join(long_symbols[:10])}")
            logger.info(f"📉 Extracted {len(short_symbols)} SHORT opportunities: {', '.join(short_symbols[:10])}")
            
            # Combine: longs first, then shorts, remove duplicates
            all_symbols = long_symbols + short_symbols
            symbols = []
            seen = set()
            for symbol in all_symbols:
                if symbol not in seen:
                    symbols.append(symbol)
                    seen.add(symbol)
        else:
            # Fallback: extract all symbols
            symbols = self._extract_symbols_from_text(content)
            logger.info(f"Extracted {len(symbols)} symbols (no section separation)")
        
        return symbols
    
    def _extract_symbols_from_text(self, text: str) -> List[str]:
        """Extract symbols from a text section."""
        symbols = []
        
        # Pattern 1: Explicit tickers like $AAPL or (AAPL)
        pattern1 = r'(?:\$|\()([A-Z]{2,5})(?:\)|\b)'
        matches1 = re.findall(pattern1, text)
        symbols.extend(matches1)
        
        # Pattern 2: "1. SYMBOL" or "SYMBOL:" format
        pattern2 = r'(?:\d+\.|:)\s*\*?([A-Z]{2,5})\b'
        matches2 = re.findall(pattern2, text)
        symbols.extend(matches2)
        
        # Pattern 3: Stricter fallback for just capital letters
        # Only accept if surrounded by spaces or specific punctuation
        # Avoid matching words inside sentences unless they look very much like tickers
        pattern3 = r'\b([A-Z]{2,5})\b'
        matches3 = re.findall(pattern3, text)
        
        # Only add pattern3 matches if we haven't found enough symbols yet
        # or if they are in the valid symbol list (if we had one)
        # For now, just add them but rely on the exclusion list to filter garbage
        symbols.extend(matches3)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_symbols = []
        for symbol in symbols:
            # Double check length and validity
            if symbol not in seen and self._is_valid_symbol(symbol):
                seen.add(symbol)
                unique_symbols.append(symbol)
        
        return unique_symbols
    
    def _is_valid_symbol(self, symbol: str) -> bool:
        """Check if symbol looks valid."""
        
        # Common false positives to exclude - EXPANDED to catch more garbage
        excluded = {
            'AI', 'US', 'ET', 'AM', 'PM', 'CEO', 'CFO', 'IPO', 'ETF',
            'NYSE', 'NASDAQ', 'SEC', 'FDA', 'API', 'USD', 'GDP', 'CPI',
            'THE', 'AND', 'FOR', 'WITH', 'FROM', 'THAT', 'THIS', 'HAVE',
            'WILL', 'BEEN', 'WERE', 'THEIR', 'ABOUT', 'WOULD', 'THERE',
            # Exclude section headers and common AI response words
            'LONG', 'SHORT', 'LONGS', 'SHORTS', 'BUY', 'SELL', 'BULLISH', 'BEARISH',
            'OPPORTUNITIES', 'LIST', 'TOP', 'FOCUS', 'LARGE', 'STOP', 'MID', 'SMALL', 
            'PART', 'VIX', 'OPEC', 'GRADE', 'HOURS', 'CAP', 'TODAY', 'PR', 'EPS', 
            'ARR', 'EST', 'OUT', 'LOW', 'HIGH', 'AVG', 'VOL', 'TARGET', 'CATALYST',
            'TECHNICAL', 'VOLUME', 'TIMEFRAME', 'PRIMARY', 'SECONDARY', 'KEY',
            'SECTOR', 'ROTATION', 'MARKET', 'SESSION', 'STRATEGY', 'ANALYSIS',
            'REGIME', 'RISK', 'LEVEL', 'DEFENSIVE', 'OFF', 'ON',
            # NEW: Common multi-word company name fragments that get extracted incorrectly
            'ROYAL', 'BANK', 'FOODS', 'STOCK', 'SHARE', 'SHARES', 'CORP', 'INC',
            'GROUP', 'TRUST', 'FUND', 'INDEX', 'WEEK', 'NEWS', 'PRICE', 'MOVE',
            'GAIN', 'LOSS', 'EARN', 'REPORT', 'QUARTER', 'YEAR', 'MONTH', 'DAY',
            'MAJOR', 'MINOR', 'BASED', 'RATED', 'RATED', 'WATCH', 'ALERT',
            'TECH', 'ENERGY', 'HEALTH', 'FINANCE', 'RETAIL', 'AUTO', 'PHARMA',
            'DECEMBER', 'JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE',
            'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DEC', 'JAN',
            'FEB', 'MAR', 'APR', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV',
            'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'MON', 'TUE',
            'WED', 'THU', 'FRI', 'SAT', 'SUN', 'WEEK', 'DAILY', 'WEEKLY',
            'BASED', 'ABOVE', 'BELOW', 'NEAR', 'OVER', 'UNDER', 'INTO', 'ONTO',
            'ALSO', 'JUST', 'ONLY', 'EVEN', 'STILL', 'MUCH', 'MORE', 'MOST',
            'SOME', 'MANY', 'SUCH', 'EACH', 'EVERY', 'OTHER', 'BOTH', 'FEW',
            'AFTER', 'BEFORE', 'DURING', 'SINCE', 'UNTIL', 'WHILE', 'WHEN',
            'WHERE', 'WHICH', 'WHAT', 'WHO', 'HOW', 'WHY', 'THAN', 'THEN',
            'COULD', 'SHOULD', 'MIGHT', 'MUST', 'SHALL', 'BEING', 'DOES', 'DONE'
        }
        
        if symbol in excluded:
            return False
        
        # Valid symbols are 1-5 uppercase letters
        if not (1 <= len(symbol) <= 5):
            return False
        
        if not symbol.isalpha():
            return False
        
        return True
    
    def _get_fallback_symbols(self) -> List[str]:
        """Get fallback symbols if AI discovery fails - DIVERSIFIED across sectors."""
        
        # Diversified fallback across sectors (not just tech mega-caps)
        fallback = [
            # Indices
            'SPY', 'QQQ', 'IWM', 'DIA',
            # Tech
            'AAPL', 'MSFT', 'NVDA', 'AMD', 'GOOGL', 'META', 'NFLX', 'TSLA',
            # Finance
            'JPM', 'BAC', 'GS', 'MS', 'C', 'WFC',
            # Healthcare
            'JNJ', 'UNH', 'PFE', 'ABBV', 'LLY',
            # Energy
            'XOM', 'CVX', 'COP', 'SLB',
            # Consumer
            'AMZN', 'WMT', 'HD', 'NKE', 'MCD',
            # Industrial
            'BA', 'CAT', 'GE', 'UPS',
            # Growth/Momentum
            'PLTR', 'COIN', 'SOFI', 'RIVN', 'HOOD', 'SNOW', 'CRWD'
        ]
        
        logger.warning("🔄 USING FALLBACK SYMBOLS - AI discovery failed")
        logger.info("=" * 80)
        logger.info("📋 FALLBACK SYMBOL BREAKDOWN")
        logger.info("=" * 80)
        
        # Categorize fallback symbols
        large_cap = ['SPY', 'QQQ', 'IWM', 'DIA', 'AAPL', 'MSFT', 'NVDA', 'AMD', 'GOOGL', 'META', 'NFLX', 'TSLA',
                     'JPM', 'BAC', 'GS', 'MS', 'C', 'WFC', 'JNJ', 'UNH', 'PFE', 'ABBV', 'LLY',
                     'XOM', 'CVX', 'COP', 'SLB', 'AMZN', 'WMT', 'HD', 'NKE', 'MCD', 'BA', 'CAT', 'GE', 'UPS']
        mid_cap = ['PLTR', 'COIN', 'SOFI', 'RIVN', 'HOOD', 'SNOW', 'CRWD']
        small_cap = []  # Will be populated by AI
        
        logger.info(f"🏢 Large-Cap ({len(large_cap)}): {', '.join(large_cap)}")
        logger.info(f"🏭 Mid-Cap ({len(mid_cap)}): {', '.join(mid_cap)}")
        logger.info(f"🏪 Small-Cap ({len(small_cap)}): {', '.join(small_cap)}")
        logger.info(f"📊 Total Fallback: {len(fallback)} symbols")
        logger.info("=" * 80)
        
        return fallback
    
    async def get_symbol_analysis(self, symbol: str) -> Optional[Dict]:
        """
        Get detailed AI analysis for a specific symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Analysis dict or None
        """
        try:
            query = f"""Analyze {symbol} for day trading RIGHT NOW:

1. **Current Price Action**: What's happening with the price today?
2. **Key Levels**: Important support/resistance levels
3. **Catalysts**: Any news or events driving movement?
4. **Technical Setup**: Is there a clear trading setup?
5. **Risk Factors**: What could go wrong?
6. **Trade Idea**: Specific entry, stop loss, and target levels

Provide actionable day trading insights."""

            result = await self.perplexity.search(query)
            
            if result and result.get('content'):
                return {
                    'symbol': symbol,
                    'analysis': result['content'],
                    'citations': result.get('citations', []),
                    'timestamp': datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting analysis for {symbol}: {e}")
            return None
    
    async def get_market_overview(self) -> Optional[Dict]:
        """
        Get AI overview of current market conditions.
        
        Returns:
            Market overview dict or None
        """
        try:
            current_time = datetime.now().strftime("%B %d, %Y at %I:%M %p ET")
            
            query = f"""Provide a comprehensive market overview as of {current_time}:

1. **Market Sentiment**: Overall bullish/bearish/neutral?
2. **Key Drivers**: What's moving the market today?
3. **Sector Performance**: Which sectors are strong/weak?
4. **Economic Data**: Any important releases today?
5. **Risk Factors**: What should traders watch out for?
6. **Trading Strategy**: Best approach for day trading today?

Provide concise, actionable insights for day traders."""

            result = await self.perplexity.search(query)
            
            if result and result.get('content'):
                return {
                    'overview': result['content'],
                    'citations': result.get('citations', []),
                    'timestamp': datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            return None
    
    def get_last_discovery(self) -> Optional[Dict]:
        """Get the last AI discovery results."""
        return self.last_opportunities if self.last_opportunities else None
    
    def _log_detailed_breakdown(self, opportunities: List[Dict]) -> None:
        """Log detailed breakdown of discovered opportunities by tier and direction."""
        
        logger.info("=" * 80)
        logger.info("🎯 DETAILED AI OPPORTUNITY BREAKDOWN")
        logger.info("=" * 80)
        
        # Group by tier and direction
        by_category = {}
        for opp in opportunities:
            key = f"{opp['tier']}_{opp['direction']}"
            if key not in by_category:
                by_category[key] = []
            by_category[key].append(opp)
        
        # Define order for consistent display
        tier_order = [
            ('large_cap', 'LONG'),
            ('large_cap', 'SHORT'),
            ('mid_cap', 'LONG'),
            ('mid_cap', 'SHORT'),
            ('small_cap', 'LONG'),
            ('small_cap', 'SHORT')
        ]
        
        total_by_tier = {'large_cap': 0, 'mid_cap': 0, 'small_cap': 0}
        total_by_direction = {'LONG': 0, 'SHORT': 0}
        
        for tier, direction in tier_order:
            key = f"{tier}_{direction}"
            if key in by_category:
                opps = by_category[key]
                
                emoji = "📈" if direction == "LONG" else "📉"
                tier_name = tier.replace('_', '-').upper()
                
                logger.info(f"{emoji} {tier_name} {direction}: {len(opps)} opportunities")
                logger.info("-" * 60)
                
                # Show all opportunities in this category
                for i, opp in enumerate(opps, 1):
                    symbol = opp['symbol']
                    catalyst = opp.get('catalyst', 'N/A')[:40]
                    confidence = opp.get('confidence', 'UNKNOWN')
                    
                    logger.info(f"  {i:2}. {symbol:6} | {confidence:6} | {catalyst}...")
                
                # Update totals
                total_by_tier[tier] += len(opps)
                total_by_direction[direction] += len(opps)
                
                logger.info("")
        
        # Log summary statistics
        logger.info("=" * 60)
        logger.info("📊 SUMMARY STATISTICS")
        logger.info("=" * 60)
        
        logger.info(f"By Market Cap:")
        for tier, count in total_by_tier.items():
            tier_name = tier.replace('_', '-').upper()
            percentage = (count / len(opportunities) * 100) if opportunities else 0
            logger.info(f"  {tier_name:10}: {count:2} opportunities ({percentage:5.1f}%)")
        
        logger.info(f"By Direction:")
        for direction, count in total_by_direction.items():
            percentage = (count / len(opportunities) * 100) if opportunities else 0
            logger.info(f"  {direction:5}: {count:2} opportunities ({percentage:5.1f}%)")
        
        logger.info(f"Total: {len(opportunities)} opportunities")
        logger.info("=" * 80)
    
    def _log_ai_response_analysis(self, result: Dict) -> None:
        """Log detailed analysis of AI response to validate quality."""
        
        content = result.get('content', '')
        citations = result.get('citations', [])
        
        logger.info("=" * 80)
        logger.info("🧠 AI RESPONSE ANALYSIS")
        logger.info("=" * 80)
        
        # Check if this is a real AI response or fallback
        fallback_indicators = [
            'fallback symbols',
            'using fallback', 
            'default symbols',
            'hardcoded',
            "don't have the information",
            "insufficient data",
            "would need"
        ]
        
        is_fallback = any(indicator.lower() in content.lower() for indicator in fallback_indicators)
        
        logger.info(f"🎯 Response Type: {'🔄 FALLBACK/LIMITED' if is_fallback else '🤖 REAL AI ANALYSIS'}")
        logger.info(f"📚 Citations: {len(citations)}")
        logger.info(f"📝 Content Length: {len(content)} characters")
        
        # Analyze content quality
        quality_indicators = {
            'has_catalysts': any(word in content.lower() for word in ['catalyst', 'earnings', 'news', 'announcement', 'beat', 'guidance', 'upgrade', 'downgrade', 'fda', 'approval']),
            'has_technical': any(word in content.lower() for word in ['breakout', 'support', 'resistance', 'volume', 'momentum', 'setup', 'trend', 'moving average']),
            'has_prices': any(word in content.lower() for word in ['$$', 'price', 'target']),
            'has_tiers': any(word in content.lower() for word in ['large-cap', 'mid-cap', 'small-cap', 'tier', 'large cap', 'mid cap', 'small cap']),
            'has_directions': any(word in content.lower() for word in ['long', 'short', 'buy', 'sell', 'bullish', 'bearish', 'upside', 'downside'])
        }
        
        logger.info("Quality Indicators:")
        for indicator, present in quality_indicators.items():
            status = "✅" if present else "❌"
            logger.info(f"  {status} {indicator.replace('_', ' ').title()}")
        
        # Show content preview
        logger.info("Content Preview (first 300 chars):")
        logger.info("-" * 40)
        preview = content[:300].replace('\n', ' ')
        logger.info(f"{preview}...")
        logger.info("-" * 40)
        
        # Show citations if available
        if citations:
            logger.info("Citations:")
            for i, citation in enumerate(citations[:3], 1):
                logger.info(f"  {i}. {citation}")
        
        logger.info("=" * 80)
    
    async def validate_opportunities(self, symbols: List[str]) -> List[str]:
        """
        Validate that AI-recommended symbols are tradeable.
        
        Args:
            symbols: List of symbols to validate
            
        Returns:
            List of validated symbols
        """
        validated = []
        
        for symbol in symbols:
            # Basic validation
            if self._is_valid_symbol(symbol) and len(symbol) <= 5:
                validated.append(symbol)
        
        logger.info(f"Validated {len(validated)}/{len(symbols)} symbols")
        return validated


# Singleton instance
_ai_finder = None

def get_ai_opportunity_finder() -> AIOpportunityFinder:
    """Get singleton AI opportunity finder instance."""
    global _ai_finder
    if _ai_finder is None:
        _ai_finder = AIOpportunityFinder()
    return _ai_finder
