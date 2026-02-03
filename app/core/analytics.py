import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict, Counter
import redis
import os

class AnalyticsEngine:
    def __init__(self):
        # Redis connection for real-time analytics
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True
        )
        
        # Analytics keys
        self.analytics_keys = {
            'total_requests': 'analytics:total_requests',
            'scam_requests': 'analytics:scam_requests',
            'unique_ips': 'analytics:unique_ips',
            'hourly_stats': 'analytics:hourly',
            'daily_stats': 'analytics:daily',
            'scam_patterns': 'analytics:patterns',
            'extracted_intel': 'analytics:intel',
            'response_times': 'analytics:response_times',
            'geographic_data': 'analytics:geo',
            'language_stats': 'analytics:languages'
        }
    
    def track_request(self, request_data: Dict, response_data: Dict, response_time: float):
        """Track individual request for analytics"""
        timestamp = datetime.now()
        hour_key = timestamp.strftime('%Y-%m-%d-%H')
        day_key = timestamp.strftime('%Y-%m-%d')
        
        # Increment counters
        self.redis_client.incr(self.analytics_keys['total_requests'])
        self.redis_client.incr(f"{self.analytics_keys['hourly_stats']}:{hour_key}:total")
        self.redis_client.incr(f"{self.analytics_keys['daily_stats']}:{day_key}:total")
        
        # Track scam detection
        if response_data.get('result', {}).get('is_scam', False):
            self.redis_client.incr(self.analytics_keys['scam_requests'])
            self.redis_client.incr(f"{self.analytics_keys['hourly_stats']}:{hour_key}:scams")
            self.redis_client.incr(f"{self.analytics_keys['daily_stats']}:{day_key}:scams")
        
        # Track response time
        self.redis_client.lpush(self.analytics_keys['response_times'], response_time)
        self.redis_client.ltrim(self.analytics_keys['response_times'], 0, 999)  # Keep last 1000
        
        # Track IP addresses
        ip = request_data.get('ip', 'unknown')
        self.redis_client.sadd(self.analytics_keys['unique_ips'], ip)
        
        # Track scam patterns
        if 'result' in response_data and 'detected_patterns' in response_data['result']:
            patterns = response_data['result']['detected_patterns']
            for pattern in patterns:
                self.redis_client.incr(f"{self.analytics_keys['scam_patterns']}:{pattern}")
        
        # Track extracted intelligence
        if 'result' in response_data and 'extracted_intel' in response_data['result']:
            intel = response_data['result']['extracted_intel']
            for intel_type, values in intel.items():
                if values:
                    for value in values:
                        self.redis_client.lpush(f"{self.analytics_keys['extracted_intel']}:{intel_type}", value)
                        self.redis_client.ltrim(f"{self.analytics_keys['extracted_intel']}:{intel_type}", 0, 99)
    
    def get_real_time_stats(self) -> Dict:
        """Get real-time statistics"""
        total_requests = int(self.redis_client.get(self.analytics_keys['total_requests']) or 0)
        scam_requests = int(self.redis_client.get(self.analytics_keys['scam_requests']) or 0)
        unique_ips = int(self.redis_client.scard(self.analytics_keys['unique_ips']))
        
        # Get response time stats
        response_times = [float(rt) for rt in self.redis_client.lrange(self.analytics_keys['response_times'], 0, -1)]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Get hourly stats for last 24 hours
        hourly_stats = {}
        for i in range(24):
            hour = (datetime.now() - timedelta(hours=i)).strftime('%Y-%m-%d-%H')
            total = int(self.redis_client.get(f"{self.analytics_keys['hourly_stats']}:{hour}:total") or 0)
            scams = int(self.redis_client.get(f"{self.analytics_keys['hourly_stats']}:{hour}:scams") or 0)
            hourly_stats[hour] = {'total': total, 'scams': scams}
        
        # Get top scam patterns
        pattern_keys = self.redis_client.keys(f"{self.analytics_keys['scam_patterns']}:*")
        top_patterns = {}
        for key in pattern_keys:
            pattern = key.split(':')[-1]
            count = int(self.redis_client.get(key) or 0)
            top_patterns[pattern] = count
        
        return {
            'total_requests': total_requests,
            'scam_requests': scam_requests,
            'scam_rate': (scam_requests / total_requests * 100) if total_requests > 0 else 0,
            'unique_ips': unique_ips,
            'avg_response_time': round(avg_response_time, 3),
            'hourly_stats': hourly_stats,
            'top_patterns': dict(sorted(top_patterns.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    def get_extracted_intel_summary(self) -> Dict:
        """Get summary of extracted intelligence"""
        intel_summary = {}
        
        for intel_type in ['upi_ids', 'links', 'bank_accounts', 'phone_numbers', 'emails']:
            key = f"{self.analytics_keys['extracted_intel']}:{intel_type}"
            values = self.redis_client.lrange(key, 0, 49)  # Get last 50
            intel_summary[intel_type] = {
                'count': len(values),
                'recent_values': values[:10]  # Show last 10
            }
        
        return intel_summary
    
    def get_performance_metrics(self) -> Dict:
        """Get performance metrics"""
        response_times = [float(rt) for rt in self.redis_client.lrange(self.analytics_keys['response_times'], 0, -1)]
        
        if not response_times:
            return {
                'avg_response_time': 0,
                'min_response_time': 0,
                'max_response_time': 0,
                'p95_response_time': 0,
                'total_requests': 0
            }
        
        response_times.sort()
        total_requests = len(response_times)
        
        return {
            'avg_response_time': round(sum(response_times) / total_requests, 3),
            'min_response_time': round(min(response_times), 3),
            'max_response_time': round(max(response_times), 3),
            'p95_response_time': round(response_times[int(total_requests * 0.95)], 3),
            'total_requests': total_requests
        }
    
    def get_trending_analysis(self) -> Dict:
        """Get trending analysis of scam patterns"""
        # Compare last 7 days with previous 7 days
        now = datetime.now()
        recent_start = now - timedelta(days=7)
        previous_start = now - timedelta(days=14)
        
        recent_patterns = defaultdict(int)
        previous_patterns = defaultdict(int)
        
        # Get pattern data for recent period
        for i in range(7):
            day = (recent_start + timedelta(days=i)).strftime('%Y-%m-%d')
            pattern_keys = self.redis_client.keys(f"{self.analytics_keys['scam_patterns']}:*")
            for key in pattern_keys:
                pattern = key.split(':')[-1]
                recent_patterns[pattern] += int(self.redis_client.get(key) or 0)
        
        # Calculate trending patterns
        trending = {}
        for pattern, recent_count in recent_patterns.items():
            previous_count = previous_patterns.get(pattern, 0)
            if previous_count > 0:
                growth_rate = ((recent_count - previous_count) / previous_count) * 100
                trending[pattern] = {
                    'recent_count': recent_count,
                    'growth_rate': round(growth_rate, 2)
                }
        
        # Sort by growth rate
        sorted_trending = dict(sorted(trending.items(), key=lambda x: x[1]['growth_rate'], reverse=True))
        
        return {
            'trending_patterns': sorted_trending,
            'analysis_period': {
                'recent_start': recent_start.strftime('%Y-%m-%d'),
                'recent_end': now.strftime('%Y-%m-%d')
            }
        }
    
    def export_analytics(self, format: str = 'json') -> Dict:
        """Export all analytics data"""
        analytics_data = {
            'timestamp': datetime.now().isoformat(),
            'real_time_stats': self.get_real_time_stats(),
            'extracted_intel': self.get_extracted_intel_summary(),
            'performance_metrics': self.get_performance_metrics(),
            'trending_analysis': self.get_trending_analysis()
        }
        
        if format == 'json':
            return analytics_data
        else:
            return json.dumps(analytics_data, indent=2)

# Global analytics instance
analytics = AnalyticsEngine()

def track_api_request(request_data: Dict, response_data: Dict, response_time: float):
    """Track API request for analytics"""
    analytics.track_request(request_data, response_data, response_time)

def get_analytics_dashboard() -> Dict:
    """Get complete analytics dashboard data"""
    return {
        'real_time': analytics.get_real_time_stats(),
        'intel': analytics.get_extracted_intel_summary(),
        'performance': analytics.get_performance_metrics(),
        'trending': analytics.get_trending_analysis()
    }
