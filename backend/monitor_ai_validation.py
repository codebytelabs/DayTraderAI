"""
Monitor AI Trade Validation Performance
Tracks statistics and generates daily reports
"""
import re
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path


def parse_log_file(log_path: str = "logs/trading.log"):
    """Parse trading log for AI validation events"""
    
    validations = []
    rejections = []
    approvals = []
    errors = []
    
    # Try multiple possible log locations
    possible_paths = [
        log_path,
        "../logs/trading.log",
        "../../logs/trading.log",
        "/tmp/daytrader_ai.log"
    ]
    
    log_file = None
    for path in possible_paths:
        try:
            if Path(path).exists():
                log_file = path
                break
        except:
            continue
    
    if not log_file:
        print(f"❌ Log file not found in any of these locations:")
        for path in possible_paths:
            print(f"   - {path}")
        print(f"\n💡 Your backend is running but logs are going to stdout (terminal).")
        print(f"   AI validation is active and will show logs when high-risk trades are detected.")
        print(f"\n   To see AI logs in real-time, watch your backend terminal for '🤖' emoji.")
        return None
    
    try:
        with open(log_file, 'r') as f:
            for line in f:
                # Skip non-AI lines
                if '🤖' not in line:
                    continue
                
                # Parse timestamp
                timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                if not timestamp_match:
                    continue
                
                timestamp = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                
                # High-risk detection
                if 'High-risk trade detected' in line:
                    symbol_match = re.search(r'for (\w+):', line)
                    reason_match = re.search(r': (.+)$', line)
                    
                    if symbol_match and reason_match:
                        validations.append({
                            'timestamp': timestamp,
                            'symbol': symbol_match.group(1),
                            'reason': reason_match.group(1).strip()
                        })
                
                # AI rejection
                elif 'AI REJECTED' in line:
                    match = re.search(r'REJECTED (\w+) (\w+) \((\d+\.\d+)s\): (.+)$', line)
                    if match:
                        rejections.append({
                            'timestamp': timestamp,
                            'signal': match.group(1),
                            'symbol': match.group(2),
                            'time': float(match.group(3)),
                            'reason': match.group(4).strip()
                        })
                
                # AI approval
                elif 'AI APPROVED' in line:
                    match = re.search(r'APPROVED (\w+) (\w+) \((\d+\.\d+)s\)', line)
                    if match:
                        approvals.append({
                            'timestamp': timestamp,
                            'signal': match.group(1),
                            'symbol': match.group(2),
                            'time': float(match.group(3))
                        })
                
                # Errors
                elif 'AI validation error' in line or 'AI validation timeout' in line:
                    errors.append({
                        'timestamp': timestamp,
                        'line': line.strip()
                    })
    
    except FileNotFoundError:
        print(f"❌ Log file not found: {log_path}")
        return None
    
    return {
        'validations': validations,
        'rejections': rejections,
        'approvals': approvals,
        'errors': errors
    }


def generate_report(data, period_hours=24):
    """Generate AI validation report"""
    
    if not data:
        print("❌ No data to analyze")
        return
    
    # Filter by time period
    cutoff = datetime.now() - timedelta(hours=period_hours)
    
    validations = [v for v in data['validations'] if v['timestamp'] > cutoff]
    rejections = [r for r in data['rejections'] if r['timestamp'] > cutoff]
    approvals = [a for a in data['approvals'] if a['timestamp'] > cutoff]
    errors = [e for e in data['errors'] if e['timestamp'] > cutoff]
    
    total = len(rejections) + len(approvals)
    
    print("\n" + "="*70)
    print(f"AI TRADE VALIDATION REPORT - Last {period_hours} Hours")
    print("="*70)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Summary statistics
    print("\n📊 SUMMARY STATISTICS")
    print("-"*70)
    print(f"Total High-Risk Trades Detected: {len(validations)}")
    print(f"Total AI Validations: {total}")
    print(f"  ✅ Approved: {len(approvals)} ({len(approvals)/total*100:.1f}%)" if total > 0 else "  ✅ Approved: 0")
    print(f"  ❌ Rejected: {len(rejections)} ({len(rejections)/total*100:.1f}%)" if total > 0 else "  ❌ Rejected: 0")
    print(f"  ⚠️  Errors: {len(errors)}")
    
    # Performance metrics
    if total > 0:
        all_times = [r['time'] for r in rejections] + [a['time'] for a in approvals]
        avg_time = sum(all_times) / len(all_times)
        min_time = min(all_times)
        max_time = max(all_times)
        
        print(f"\n⏱️  PERFORMANCE")
        print("-"*70)
        print(f"Average Validation Time: {avg_time:.2f}s")
        print(f"Fastest: {min_time:.2f}s")
        print(f"Slowest: {max_time:.2f}s")
        print(f"Error Rate: {len(errors)/total*100:.1f}%")
    
    # Symbol breakdown
    if rejections or approvals:
        symbol_stats = defaultdict(lambda: {'approved': 0, 'rejected': 0})
        
        for r in rejections:
            symbol_stats[r['symbol']]['rejected'] += 1
        
        for a in approvals:
            symbol_stats[a['symbol']]['approved'] += 1
        
        print(f"\n📈 BY SYMBOL")
        print("-"*70)
        print(f"{'Symbol':<10} {'Approved':<12} {'Rejected':<12} {'Rejection %':<12}")
        print("-"*70)
        
        for symbol in sorted(symbol_stats.keys()):
            stats = symbol_stats[symbol]
            total_sym = stats['approved'] + stats['rejected']
            rej_pct = stats['rejected'] / total_sym * 100 if total_sym > 0 else 0
            print(f"{symbol:<10} {stats['approved']:<12} {stats['rejected']:<12} {rej_pct:<12.1f}%")
    
    # Recent rejections
    if rejections:
        print(f"\n❌ RECENT REJECTIONS (Last 10)")
        print("-"*70)
        
        for r in sorted(rejections, key=lambda x: x['timestamp'], reverse=True)[:10]:
            print(f"\n{r['timestamp'].strftime('%H:%M:%S')} - {r['signal'].upper()} {r['symbol']} ({r['time']:.2f}s)")
            print(f"  Reason: {r['reason'][:100]}...")
    
    # Risk factors analysis
    if validations:
        risk_factors = defaultdict(int)
        
        for v in validations:
            reason = v['reason'].lower()
            if 'cooldown' in reason:
                risk_factors['Cooldown'] += 1
            if 'win rate' in reason:
                risk_factors['Low Win Rate'] += 1
            if 'position' in reason:
                risk_factors['Large Position'] += 1
            if 'counter-trend' in reason:
                risk_factors['Counter-Trend'] += 1
            if 'confidence' in reason:
                risk_factors['Low Confidence'] += 1
            if 'consecutive' in reason:
                risk_factors['Consecutive Losses'] += 1
        
        print(f"\n⚠️  RISK FACTORS DETECTED")
        print("-"*70)
        for factor, count in sorted(risk_factors.items(), key=lambda x: x[1], reverse=True):
            print(f"{factor:<25} {count:>3} times")
    
    # Errors
    if errors:
        print(f"\n⚠️  ERRORS (Last 5)")
        print("-"*70)
        for e in errors[-5:]:
            print(f"{e['timestamp'].strftime('%H:%M:%S')} - {e['line'][:80]}...")
    
    # Estimated impact
    if rejections:
        avg_loss_per_bad_trade = 150  # Conservative estimate
        estimated_savings = len(rejections) * avg_loss_per_bad_trade
        
        print(f"\n💰 ESTIMATED IMPACT")
        print("-"*70)
        print(f"Trades Prevented: {len(rejections)}")
        print(f"Estimated Savings: ${estimated_savings:,.2f}")
        print(f"  (Assuming ${avg_loss_per_bad_trade} avg loss per bad trade)")
    
    print("\n" + "="*70)


def monitor_live():
    """Monitor AI validation in real-time"""
    import time
    import subprocess
    
    print("\n" + "="*70)
    print("AI VALIDATION LIVE MONITOR")
    print("="*70)
    print("Watching for AI validation events... (Press Ctrl+C to stop)")
    print("="*70 + "\n")
    
    try:
        # Use tail -f to follow log file
        process = subprocess.Popen(
            ['tail', '-f', 'logs/trading.log'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        for line in process.stdout:
            if '🤖' in line:
                # Color code the output
                if 'REJECTED' in line:
                    print(f"\033[91m{line.strip()}\033[0m")  # Red
                elif 'APPROVED' in line:
                    print(f"\033[92m{line.strip()}\033[0m")  # Green
                elif 'High-risk' in line:
                    print(f"\033[93m{line.strip()}\033[0m")  # Yellow
                else:
                    print(line.strip())
    
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped")
        process.terminate()
    except FileNotFoundError:
        print("❌ Log file not found. Is the backend running?")


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'live':
            monitor_live()
            return
        elif sys.argv[1] == 'report':
            hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
            data = parse_log_file()
            generate_report(data, period_hours=hours)
            return
    
    # Default: show report
    data = parse_log_file()
    generate_report(data, period_hours=24)
    
    print("\n💡 Usage:")
    print("  python monitor_ai_validation.py          # Show 24h report")
    print("  python monitor_ai_validation.py report 48 # Show 48h report")
    print("  python monitor_ai_validation.py live      # Live monitoring")


if __name__ == "__main__":
    main()
