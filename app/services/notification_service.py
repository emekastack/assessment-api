from app.core.logging import get_logger
from datetime import datetime

logger = get_logger(__name__)

class NotificationService:
    """Service for handling email notifications (mocked for this assessment)"""
    
    @staticmethod
    def send_partner_request_notification(recipient_name: str, sender_name: str):
        """Send notification when a partner request is created"""
        message = f"You have a new partner request from {sender_name}."
        
        # Mock email sending - in production this would integrate with email service
        logger.info(f"📧 EMAIL NOTIFICATION: To: {recipient_name}")
        logger.info(f"📧 EMAIL NOTIFICATION: Subject: New Partner Request")
        logger.info(f"📧 EMAIL NOTIFICATION: Body: {message}")
        logger.info(f"📧 EMAIL NOTIFICATION: Timestamp: {datetime.now()}")
        logger.info("📧 EMAIL NOTIFICATION: Status: Sent (mocked)")
        
        return True
    
    @staticmethod
    def send_request_accepted_notification(sender_name: str, recipient_name: str):
        """Send notification when a partner request is accepted"""
        message = f"Your partner request to {recipient_name} was accepted."
        
        # Mock email sending - in production this would integrate with email service
        logger.info(f"📧 EMAIL NOTIFICATION: To: {sender_name}")
        logger.info(f"📧 EMAIL NOTIFICATION: Subject: Partner Request Accepted")
        logger.info(f"📧 EMAIL NOTIFICATION: Body: {message}")
        logger.info(f"📧 EMAIL NOTIFICATION: Timestamp: {datetime.now()}")
        logger.info("📧 EMAIL NOTIFICATION: Status: Sent (mocked)")
        
        return True
