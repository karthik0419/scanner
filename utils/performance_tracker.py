import pandas as pd
import json
from datetime import datetime, timedelta
import os

class PerformanceTracker:
    def __init__(self, data_file="data/performance_data.json"):
        self.data_file = data_file
        self.performance_data = self.load_data()
        
    def load_data(self):
        """Load existing performance data"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    return json.load(f)
        except:
            return self.get_default_data()
    
    def save_data(self):
        """Save performance data to file"""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        with open(self.data_file, 'w') as f:
            json.dump(self.performance_data, f, indent=2)
    
    def get_default_data(self):
        """Default performance data structure"""
        return {
            "patterns": {},
            "trades": [],
            "last_updated": datetime.now().isoformat()
        }
    
    def record_trade(self, trade_data):
        """Record a new trade outcome"""
        pattern = trade_data.get('pattern', 'Unknown')
        
        # Initialize pattern if it doesn't exist
        if pattern not in self.performance_data['patterns']:
            self.performance_data['patterns'][pattern] = self.get_default_pattern_stats()
        
        # Add trade to history
        trade_record = {
            "date": trade_data.get('date', datetime.now().isoformat()),
            "symbol": trade_data.get('symbol', ''),
            "pattern": pattern,
            "entry_price": trade_data.get('entry_price', 0),
            "exit_price": trade_data.get('exit_price', 0),
            "target": trade_data.get('target', 0),
            "stop_loss": trade_data.get('stop_loss', 0),
            "profit_loss_pct": trade_data.get('profit_loss_pct', 0),
            "profit_loss_amount": trade_data.get('profit_loss_amount', 0),
            "is_win": trade_data.get('is_win', False),
            "days_held": trade_data.get('days_held', 0),
            "rr_ratio": trade_data.get('rr_ratio', 0),
            "market_conditions": trade_data.get('market_conditions', {}),
            "sector": trade_data.get('sector', 'Unknown')
        }
        
        self.performance_data['trades'].append(trade_record)
        
        # Update pattern statistics
        self.update_pattern_stats(pattern, trade_record)
        
        # Save updated data
        self.performance_data['last_updated'] = datetime.now().isoformat()
        self.save_data()
    
    def get_default_pattern_stats(self):
        """Get default pattern statistics structure"""
        return {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "total_profit": 0,
            "total_loss": 0,
            "avg_profit": 0,
            "avg_loss": 0,
            "win_rate": 0,
            "avg_profit_pct": 0,
            "max_profit": 0,
            "max_loss": 0
        }
    
    def update_pattern_stats(self, pattern, trade_record):
        """Update statistics for a specific pattern"""
        stats = self.performance_data['patterns'][pattern]
        
        # Update basic counts
        stats['total_trades'] += 1
        
        if trade_record['is_win']:
            stats['wins'] += 1
            stats['total_profit'] += trade_record['profit_loss_amount']
            
            # Update max profit
            if trade_record['profit_loss_amount'] > stats['max_profit']:
                stats['max_profit'] = trade_record['profit_loss_amount']
        else:
            stats['losses'] += 1
            stats['total_loss'] += abs(trade_record['profit_loss_amount'])
            
            # Update max loss
            if abs(trade_record['profit_loss_amount']) > stats['max_loss']:
                stats['max_loss'] = abs(trade_record['profit_loss_amount'])
        
        # Calculate averages and rates
        if stats['wins'] > 0:
            stats['avg_profit'] = stats['total_profit'] / stats['wins']
            stats['avg_profit_pct'] = (stats['total_profit'] / stats['wins']) * 100
        
        if stats['losses'] > 0:
            stats['avg_loss'] = stats['total_loss'] / stats['losses']
        
        if stats['total_trades'] > 0:
            stats['win_rate'] = (stats['wins'] / stats['total_trades']) * 100
    
    def get_pattern_performance(self, pattern):
        """Get performance statistics for a specific pattern"""
        patterns_data = self.performance_data.get('patterns', {})
        if patterns_data is None:
            return self.get_default_pattern_stats()
        return patterns_data.get(pattern, self.get_default_pattern_stats())
    
    def get_all_patterns_performance(self):
        """Get performance for all patterns"""
        return self.performance_data['patterns']
    
    def get_best_patterns(self, min_trades=5):
        """Get best performing patterns with minimum trade count"""
        pattern_performance = []
        
        for pattern, stats in self.performance_data['patterns'].items():
            if stats['total_trades'] >= min_trades:
                pattern_performance.append({
                    'pattern': pattern,
                    'win_rate': stats['win_rate'],
                    'avg_profit_pct': stats['avg_profit_pct'],
                    'total_trades': stats['total_trades'],
                    'profit_factor': stats['total_profit'] / max(stats['total_loss'], 1),
                    'score': self.calculate_pattern_score(stats)
                })
        
        # Sort by score
        return sorted(pattern_performance, key=lambda x: x['score'], reverse=True)
    
    def calculate_pattern_score(self, stats):
        """Calculate overall score for pattern performance"""
        # Weight different factors
        win_rate_score = stats['win_rate'] * 0.4  # 40% weight
        profit_score = min(stats['avg_profit_pct'] * 5, 20)  # 20% weight, capped at 20
        frequency_score = min(stats['total_trades'] * 2, 20)  # 20% weight, capped at 20
        consistency_score = 20 if stats['win_rate'] > 60 else 10 if stats['win_rate'] > 40 else 0  # 20% weight
        
        return win_rate_score + profit_score + frequency_score + consistency_score
    
    def get_recent_trades(self, days=30):
        """Get trades from last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_trades = []
        
        for trade in self.performance_data['trades']:
            trade_date = datetime.fromisoformat(trade['date'])
            if trade_date >= cutoff_date:
                recent_trades.append(trade)
        
        return recent_trades
    
    def get_market_condition_analysis(self):
        """Analyze performance by market conditions"""
        market_analysis = {
            'bullish': {'wins': 0, 'losses': 0, 'total': 0},
            'bearish': {'wins': 0, 'losses': 0, 'total': 0},
            'sideways': {'wins': 0, 'losses': 0, 'total': 0},
            'high_volatility': {'wins': 0, 'losses': 0, 'total': 0},
            'low_volatility': {'wins': 0, 'losses': 0, 'total': 0}
        }
        
        for trade in self.performance_data['trades']:
            market_cond = trade.get('market_conditions', {})
            trend = market_cond.get('trend', 'Unknown')
            volatility = market_cond.get('volatility', 'Medium')
            
            if trend in market_analysis:
                if trade['is_win']:
                    market_analysis[trend]['wins'] += 1
                else:
                    market_analysis[trend]['losses'] += 1
                market_analysis[trend]['total'] += 1
            
            if f"{volatility}_volatility" in market_analysis:
                if trade['is_win']:
                    market_analysis[f"{volatility}_volatility"]['wins'] += 1
                else:
                    market_analysis[f"{volatility}_volatility"]['losses'] += 1
                market_analysis[f"{volatility}_volatility"]['total'] += 1
        
        # Calculate win rates
        for condition, stats in market_analysis.items():
            if stats['total'] > 0:
                stats['win_rate'] = (stats['wins'] / stats['total']) * 100
            else:
                stats['win_rate'] = 0
        
        return market_analysis
    
    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        report = {
            'summary': self.get_summary_stats(),
            'pattern_performance': self.get_all_patterns_performance(),
            'best_patterns': self.get_best_patterns(),
            'recent_trades': self.get_recent_trades(),
            'market_analysis': self.get_market_condition_analysis(),
            'recommendations': self.generate_recommendations()
        }
        
        return report
    
    def get_summary_stats(self):
        """Get overall summary statistics"""
        total_trades = len(self.performance_data['trades'])
        total_wins = sum(1 for trade in self.performance_data['trades'] if trade['is_win'])
        total_losses = total_trades - total_wins
        
        total_profit = sum(trade['profit_loss_amount'] for trade in self.performance_data['trades'] if trade['is_win'])
        total_loss = sum(abs(trade['profit_loss_amount']) for trade in self.performance_data['trades'] if not trade['is_win'])
        
        return {
            'total_trades': total_trades,
            'total_wins': total_wins,
            'total_losses': total_losses,
            'overall_win_rate': (total_wins / total_trades * 100) if total_trades > 0 else 0,
            'total_profit': total_profit,
            'total_loss': total_loss,
            'net_profit': total_profit - total_loss,
            'avg_profit_per_trade': (total_profit - total_loss) / total_trades if total_trades > 0 else 0,
            'profit_factor': total_profit / max(total_loss, 1) if total_loss > 0 else total_profit
        }
    
    def generate_recommendations(self):
        """Generate trading recommendations based on performance"""
        recommendations = []
        
        # Pattern recommendations
        best_patterns = self.get_best_patterns()
        if best_patterns:
            top_pattern = best_patterns[0]
            recommendations.append(f"Focus on {top_pattern['pattern']} patterns - {top_pattern['win_rate']:.1f}% win rate")
        
        # Market condition recommendations
        market_analysis = self.get_market_condition_analysis()
        
        best_market = max(market_analysis.items(), key=lambda x: x[1]['win_rate'])
        if best_market[1]['total'] >= 5:
            recommendations.append(f"Best performance in {best_market[0]} market conditions - {best_market[1]['win_rate']:.1f}% win rate")
        
        # Risk management recommendations
        summary = self.get_summary_stats()
        if summary['overall_win_rate'] < 40:
            recommendations.append("Consider tightening entry criteria - low win rate detected")
        elif summary['overall_win_rate'] > 70:
            recommendations.append("Excellent win rate - consider increasing position size")
        
        return recommendations

# Global tracker instance
tracker = PerformanceTracker()

def record_trade(trade_data):
    """Convenience function to record a trade"""
    tracker.record_trade(trade_data)

def get_performance_report():
    """Convenience function to get performance report"""
    return tracker.generate_performance_report()

def get_pattern_success_rate(pattern, min_trades=5):
    """Get success rate for a specific pattern"""
    try:
        stats = tracker.get_pattern_performance(pattern)
        
        if stats['total_trades'] < min_trades:
            return 0, f"Insufficient data ({stats['total_trades']} trades, need {min_trades}+)"
        
        return stats['win_rate'], f"{stats['total_trades']} trades, {stats['win_rate']:.1f}% win rate"
    except:
        return 0, "No historical data available"
