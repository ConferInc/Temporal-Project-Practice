"""
Pyramid Architecture: Level 3 - Communications MCP Worker

The CommsMCP handles all outbound communications:
- Email notifications (welcome, status updates, decisions)
- SMS alerts

This is a mock implementation with print logs for development.
In production, integrate with SendGrid, Twilio, etc.
"""
from dataclasses import dataclass
from temporalio import activity
from datetime import datetime


@dataclass
class CommsMCP:
    """Communications MCP - handles email and SMS"""

    @staticmethod
    def send_email(template_id: str, recipient: str, context: dict = None) -> str:
        """
        Send an email using a template.

        Args:
            template_id: Email template identifier (e.g., "welcome", "approved", "rejected")
            recipient: Email address of the recipient
            context: Optional context data for template rendering

        Returns:
            Status message
        """
        timestamp = datetime.utcnow().isoformat()
        print(f"[CommsMCP] [{timestamp}] EMAIL SENT")
        print(f"  Template: {template_id}")
        print(f"  To: {recipient}")
        print(f"  Context: {context or {}}")
        return f"Email '{template_id}' sent to {recipient}"

    @staticmethod
    def send_sms(phone_number: str, message: str) -> str:
        """
        Send an SMS message.

        Args:
            phone_number: Recipient phone number
            message: SMS message content

        Returns:
            Status message
        """
        timestamp = datetime.utcnow().isoformat()
        print(f"[CommsMCP] [{timestamp}] SMS SENT")
        print(f"  To: {phone_number}")
        print(f"  Message: {message}")
        return f"SMS sent to {phone_number}"


# =========================================
# Temporal Activity Functions
# =========================================

@activity.defn
async def send_email(template_id: str, recipient: str, context: dict = None) -> str:
    """Temporal Activity: Send email via CommsMCP"""
    return CommsMCP.send_email(template_id, recipient, context or {})


@activity.defn
async def send_sms(phone_number: str, message: str) -> str:
    """Temporal Activity: Send SMS via CommsMCP"""
    return CommsMCP.send_sms(phone_number, message)
