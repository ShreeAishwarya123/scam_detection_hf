import time
import hashlib
import redis
from typing import Dict, Optional
from fastapi import HTTPException, Request
from collections import defaultdict
import os
import json

class SecurityManager:
    def __init__(self):
        # Redis for rate limiting and security
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=1,
            decode_responses=True
        )
        
        # Rate limiting settings
        self.rate_limits = {
            'default': {'requests': 100, 'window': 3600},  # 100 requests per hour
            'authenticated': {'requests': 1000, 'window': 3600},  # 1000 requests per hour
            'premium': {'requests': 10000, 'window': 3600}  # 10000 requests per hour
        }
        
        # Security settings
        self.max_request_size = 10000  # 10KB max request size
        self.blocked_ips = set()
        self.suspicious_patterns = {
            'sql_injection': r'(\b(union|select|insert|update|delete|drop|exec|script)\b)',
            'xss': r'(<script|javascript:|onload=|onerror=)',
            'path_traversal': r'(\.\./|\.\.\\)',
            'command_injection': r'(;|\||&|`|\$\()',
            'excessive_length': r'.{1000,}'  # Very long requests
        }
        
        # API key management
        self.api_keys = {
            'free': {'requests': 100, 'window': 3600},
            'basic': {'requests': 1000, 'window': 3600},
            'premium': {'requests': 10000, 'window': 3600}
        }
    
    def generate_secure_api_key(self, user_tier: str = 'free') -> str:
        """Generate secure API key"""
        timestamp = str(int(time.time()))
        random_data = f"{user_tier}_{timestamp}_{os.urandom(16).hex()}"
        api_key = hashlib.sha256(random_data.encode()).hexdigest()
        
        # Store API key info
        key_info = {
            'tier': user_tier,
            'created_at': timestamp,
            'requests_used': 0,
            'last_reset': timestamp
        }
        self.redis_client.set(f"api_key:{api_key}", json.dumps(key_info), ex=86400*30)  # 30 days expiry
        
        return api_key
    
    def validate_api_key(self, api_key: str) -> Dict:
        """Validate API key and return tier info"""
        if not api_key:
            raise HTTPException(status_code=401, detail="API key required")
        
        key_data = self.redis_client.get(f"api_key:{api_key}")
        if not key_data:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        try:
            key_info = json.loads(key_data)
            return key_info
        except json.JSONDecodeError:
            raise HTTPException(status_code=401, detail="Invalid API key format")
    
    def check_rate_limit(self, identifier: str, tier: str = 'default') -> bool:
        """Check if identifier has exceeded rate limit"""
        limit_config = self.rate_limits.get(tier, self.rate_limits['default'])
        key = f"rate_limit:{identifier}"
        
        # Get current request count
        current_requests = int(self.redis_client.get(key) or 0)
        
        if current_requests >= limit_config['requests']:
            return False
        
        # Increment request count
        self.redis_client.incr(key)
        self.redis_client.expire(key, limit_config['window'])
        return True
    
    def is_request_suspicious(self, request_data: Dict) -> tuple[bool, str]:
        """Check if request contains suspicious patterns"""
        # Check request size
        content_length = len(str(request_data))
        if content_length > self.max_request_size:
            return True, "Request too large"
        
        # Check for suspicious patterns
        content = str(request_data).lower()
        
        for pattern_name, pattern in self.suspicious_patterns.items():
            import re
            if re.search(pattern, content):
                return True, f"Suspicious pattern detected: {pattern_name}"
        
        return False, ""
    
    def block_ip(self, ip: str, duration: int = 3600):
        """Block IP for specified duration"""
        self.blocked_ips.add(ip)
        self.redis_client.setex(f"blocked_ip:{ip}", duration, "1")
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        return self.redis_client.exists(f"blocked_ip:{ip}") > 0
    
    def log_security_event(self, event_type: str, details: Dict):
        """Log security event"""
        timestamp = int(time.time())
        event_data = {
            'timestamp': timestamp,
            'type': event_type,
            'details': details
        }
        
        # Store in Redis with TTL
        self.redis_client.lpush("security_events", json.dumps(event_data))
        self.redis_client.ltrim("security_events", 0, 999)  # Keep last 1000 events
        self.redis_client.expire("security_events", 86400 * 7)  # 7 days retention
    
    def get_security_stats(self) -> Dict:
        """Get security statistics"""
        total_blocked = len(self.blocked_ips)
        recent_events = []
        
        # Get recent security events
        events = self.redis_client.lrange("security_events", 0, 49)
        for event in events:
            try:
                event_data = json.loads(event)
                recent_events.append(event_data)
            except json.JSONDecodeError:
                continue
        
        return {
            'blocked_ips_count': total_blocked,
            'recent_events': recent_events,
            'active_rate_limits': len(self.redis_client.keys("rate_limit:*")),
            'api_keys_active': len(self.redis_client.keys("api_key:*"))
        }
    
    def cleanup_expired_data(self):
        """Clean up expired security data"""
        # This would typically be run as a background task
        patterns_to_clean = [
            "rate_limit:*",
            "blocked_ip:*",
            "security_events"
        ]
        
        for pattern in patterns_to_clean:
            keys = self.redis_client.keys(pattern)
            for key in keys:
                ttl = self.redis_client.ttl(key)
                if ttl == -1:  # No expiry set
                    # Set reasonable expiry
                    if "rate_limit" in key:
                        self.redis_client.expire(key, 3600)
                    elif "blocked_ip" in key:
                        self.redis_client.expire(key, 86400)

# Global security manager
security_manager = SecurityManager()

def get_api_key(request: Request) -> str:
    """Extract and validate API key from request"""
    # Try to get API key from header
    api_key = request.headers.get("X-API-Key")
    
    # If not in header, try query parameter
    if not api_key:
        api_key = request.query_params.get("api_key")
    
    # If still not found, raise exception
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Include it in X-API-Key header or api_key query parameter."
        )
    
    return api_key

def validate_request_security(request: Request, api_key: str = None):
    """Validate request security"""
    # Get client IP
    client_ip = request.client.host
    
    # Check if IP is blocked
    if security_manager.is_ip_blocked(client_ip):
        raise HTTPException(status_code=403, detail="IP address blocked")
    
    # Validate API key if provided
    if api_key:
        key_info = security_manager.validate_api_key(api_key)
        tier = key_info.get('tier', 'free')
    else:
        tier = 'default'
    
    # Check rate limiting
    identifier = f"{client_ip}:{api_key}" if api_key else client_ip
    if not security_manager.check_rate_limit(identifier, tier):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
    
    # Check for suspicious content
    request_data = {
        'headers': dict(request.headers),
        'query_params': dict(request.query_params),
        'path': request.url.path
    }
    
    is_suspicious, reason = security_manager.is_request_suspicious(request_data)
    if is_suspicious:
        # Log security event
        security_manager.log_security_event("suspicious_request", {
            'ip': client_ip,
            'reason': reason,
            'request_data': request_data
        })
        
        # Block IP for repeated suspicious requests
        suspicious_count = int(security_manager.redis_client.get(f"suspicious:{client_ip}") or 0)
        if suspicious_count >= 5:
            security_manager.block_ip(client_ip)
            raise HTTPException(status_code=403, detail="IP blocked due to suspicious activity")
        
        security_manager.redis_client.incr(f"suspicious:{client_ip}")
        security_manager.redis_client.expire(f"suspicious:{client_ip}", 3600)
        
        raise HTTPException(status_code=400, detail=f"Suspicious request detected: {reason}")
    
    return tier

def log_api_request(request: Request, response_data: Dict, response_time: float, tier: str):
    """Log API request for analytics and security"""
    client_ip = request.client.host
    
    # Log to analytics
    try:
        from app.core.analytics import track_api_request
        request_data = {
            'ip': client_ip,
            'method': request.method,
            'path': request.url.path,
            'user_agent': request.headers.get('user-agent', ''),
            'tier': tier
        }
        track_api_request(request_data, response_data, response_time)
    except Exception as e:
        # Don't let analytics errors break the API
        pass
    
    # Log security event if it was a scam
    if response_data.get('result', {}).get('is_scam', False):
        security_manager.log_security_event("scam_detected", {
            'ip': client_ip,
            'scam_data': response_data.get('result', {}),
            'request_path': request.url.path
        })
