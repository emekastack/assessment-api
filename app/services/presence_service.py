from datetime import datetime, timezone
from typing import Dict, Optional
import redis
import json
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)

class PresenceService:
    """Service for managing user presence (online/offline status)"""
    
    def __init__(self):
        # Try to connect to Redis, fall back to in-memory storage
        try:
            self.redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
            self.redis_client.ping()  # Test connection
            self.use_redis = True
            logger.info("Connected to Redis for presence storage")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using in-memory storage.")
            self.redis_client = None
            self.use_redis = False
            # In-memory storage as fallback
            self._presence_data: Dict[int, Dict] = {}
    
    def _get_presence_key(self, user_id: int) -> str:
        """Get Redis key for user presence"""
        return f"presence:user:{user_id}"
    
    def _get_online_users_key(self) -> str:
        """Get Redis key for set of online users"""
        return "presence:online_users"
    
    def set_user_online(self, user_id: int) -> bool:
        """Mark user as online"""
        try:
            presence_data = {
                "online": True,
                "last_seen": datetime.now(timezone.utc).isoformat(),
                "connected_at": datetime.now(timezone.utc).isoformat()
            }
            
            if self.use_redis:
                # Store in Redis with expiration (e.g., 5 minutes)
                self.redis_client.setex(
                    self._get_presence_key(user_id), 
                    300,  # 5 minutes
                    json.dumps(presence_data)
                )
                # Add to online users set
                self.redis_client.sadd(self._get_online_users_key(), user_id)
            else:
                # Store in memory
                self._presence_data[user_id] = presence_data
            
            logger.info(f"User {user_id} is now online")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set user {user_id} online: {e}")
            return False
    
    def set_user_offline(self, user_id: int) -> bool:
        """Mark user as offline"""
        try:
            if self.use_redis:
                # Update presence data
                presence_data = {
                    "online": False,
                    "last_seen": datetime.now(timezone.utc).isoformat()
                }
                self.redis_client.setex(
                    self._get_presence_key(user_id),
                    86400,  # Keep for 24 hours
                    json.dumps(presence_data)
                )
                # Remove from online users set
                self.redis_client.srem(self._get_online_users_key(), user_id)
            else:
                # Update in memory
                if user_id in self._presence_data:
                    self._presence_data[user_id]["online"] = False
                    self._presence_data[user_id]["last_seen"] = datetime.now(timezone.utc).isoformat()
            
            logger.info(f"User {user_id} is now offline")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set user {user_id} offline: {e}")
            return False
    
    def get_user_presence(self, user_id: int) -> Dict:
        """Get user presence status"""
        try:
            if self.use_redis:
                presence_data = self.redis_client.get(self._get_presence_key(user_id))
                if presence_data:
                    return json.loads(presence_data)
                else:
                    return {"online": False, "last_seen": None}
            else:
                return self._presence_data.get(user_id, {"online": False, "last_seen": None})
                
        except Exception as e:
            logger.error(f"Failed to get presence for user {user_id}: {e}")
            return {"online": False, "last_seen": None}
    
    def get_online_users(self) -> list:
        """Get list of currently online user IDs"""
        try:
            if self.use_redis:
                online_user_ids = self.redis_client.smembers(self._get_online_users_key())
                return [int(user_id) for user_id in online_user_ids]
            else:
                return [user_id for user_id, data in self._presence_data.items() 
                       if data.get("online", False)]
                
        except Exception as e:
            logger.error(f"Failed to get online users: {e}")
            return []
    
    def is_user_online(self, user_id: int) -> bool:
        """Check if user is currently online"""
        presence = self.get_user_presence(user_id)
        return presence.get("online", False)
    
    def update_last_seen(self, user_id: int) -> bool:
        """Update user's last seen timestamp"""
        try:
            if self.use_redis:
                presence_data = self.redis_client.get(self._get_presence_key(user_id))
                if presence_data:
                    data = json.loads(presence_data)
                    data["last_seen"] = datetime.now(timezone.utc).isoformat()
                    self.redis_client.setex(
                        self._get_presence_key(user_id),
                        300,  # 5 minutes
                        json.dumps(data)
                    )
            else:
                if user_id in self._presence_data:
                    self._presence_data[user_id]["last_seen"] = datetime.now(timezone.utc).isoformat()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update last seen for user {user_id}: {e}")
            return False

# Global instance
presence_service = PresenceService()
