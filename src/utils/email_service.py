"""
Email notification service using SendGrid for trade notifications.
"""

import json
import logging
import os
from datetime import datetime

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Email, Mail, To

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.api_key = os.environ.get('SENDGRID_API_KEY')
        if not self.api_key:
            logger.warning("SENDGRID_API_KEY not found in environment variables")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("EmailService initialized with SendGrid")
        self.settings_file = "user_settings.json"
        self.settings = self._load_settings()

    def _load_settings(self):
        """Load user email settings from file."""
        try:
            with open(self.settings_file) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Default settings if file doesn't exist
            default_settings = {
                "email_notifications": {
                    "enabled": True,
                    "recipient_email": "trader@example.com",
                    "sender_email": "trading-system@replit.app"
                }
            }
            self._save_settings(default_settings)
            return default_settings

    def _save_settings(self, settings):
        """Save user email settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save email settings: {e}")

    def update_email_settings(self, enabled=None, recipient_email=None, sender_email=None):
        """Update email notification settings."""
        if enabled is not None:
            self.settings["email_notifications"]["enabled"] = enabled
        if recipient_email is not None:
            self.settings["email_notifications"]["recipient_email"] = recipient_email
        if sender_email is not None:
            self.settings["email_notifications"]["sender_email"] = sender_email

        self._save_settings(self.settings)
        logger.info("Email settings updated successfully")
        return True

    def send_trade_notification(self, trade_data, recipient_email=None, sender_email=None):
        """Send email notification when a trade is executed."""
        if not self.enabled:
            logger.warning("Email service not enabled - missing credentials")
            return False

        if not self.settings["email_notifications"]["enabled"]:
            logger.info("Email notifications disabled by user settings")
            return False

        # Use settings or provided parameters
        recipient_email = recipient_email or self.settings["email_notifications"]["recipient_email"]
        sender_email = sender_email or self.settings["email_notifications"]["sender_email"]

        try:
            # Extract trade information
            symbol = trade_data.get('symbol', 'Unknown')
            action = trade_data.get('action', 'Unknown')
            quantity = trade_data.get('quantity', 0)
            price = trade_data.get('price', 0)
            total_value = trade_data.get('total_value', quantity * price)
            timestamp = trade_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            pnl = trade_data.get('pnl', 0)

            # Create email subject
            subject = f"🔔 Trade Alert: {action.upper()} {symbol}"

            # Create HTML email content
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5;">
                <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: {'#28a745' if action.lower() == 'buy' else '#dc3545'};">
                        {'📈' if action.lower() == 'buy' else '📉'} Trade Executed
                    </h2>

                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                        <h3 style="margin: 0 0 10px 0; color: #333;">Trade Details:</h3>
                        <p style="margin: 5px 0;"><strong>Action:</strong> {action.upper()}</p>
                        <p style="margin: 5px 0;"><strong>Cryptocurrency:</strong> {symbol}</p>
                        <p style="margin: 5px 0;"><strong>Quantity:</strong> {quantity:.6f}</p>
                        <p style="margin: 5px 0;"><strong>Price:</strong> ${price:.6f}</p>
                        <p style="margin: 5px 0;"><strong>Total Value:</strong> ${total_value:.2f}</p>
                        {f'<p style="margin: 5px 0;"><strong>Profit/Loss:</strong> <span style="color: {"#28a745" if pnl >= 0 else "#dc3545"};">${pnl:.2f} ({("+" if pnl >= 0 else "")}{(pnl/total_value*100):.1f}%)</span></p>' if action.upper() == 'SELL' and pnl != 0 else ''}
                        <p style="margin: 5px 0;"><strong>Time:</strong> {timestamp}</p>
                    </div>

                    <div style="background-color: #e9ecef; padding: 10px; border-radius: 5px; margin-top: 15px;">
                        <p style="margin: 0; font-size: 12px; color: #666;">
                            This is an automated notification from your Algorithmic Trading System.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """

            # Create plain text version
            pnl_text = f"\nProfit/Loss: ${pnl:.2f} ({(''+'' if pnl >= 0 else '')}{(pnl/total_value*100):.1f}%)" if action.upper() == 'SELL' and pnl != 0 else ''
            text_content = f"""
Trade Executed!

Action: {action.upper()}
Cryptocurrency: {symbol}
Quantity: {quantity:.6f}
Price: ${price:.6f}
Total Value: ${total_value:.2f}{pnl_text}
Time: {timestamp}

This is an automated notification from your Algorithmic Trading System.
            """

            # Create and send email
            sg = SendGridAPIClient(self.api_key)
            message = Mail(
                from_email=Email(sender_email),
                to_emails=To(recipient_email),
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content
            )

            response = sg.send(message)

            if response.status_code == 202:
                logger.info(f"Trade notification email sent successfully for {action} {symbol}")
                return True
            else:
                logger.error(f"Failed to send email. Status code: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            return False

    def send_system_alert(self, alert_message, alert_type="info", recipient_email="trader@example.com", sender_email="trading-system@replit.app"):
        """Send system alert email for important events."""
        if not self.enabled:
            logger.warning("Email service not enabled - missing credentials")
            return False

        try:
            # Determine alert styling based on type
            alert_colors = {
                'info': '#17a2b8',
                'success': '#28a745',
                'warning': '#ffc107',
                'error': '#dc3545'
            }

            alert_icons = {
                'info': '💡',
                'success': '✅',
                'warning': '⚠️',
                'error': '🚨'
            }

            color = alert_colors.get(alert_type, '#17a2b8')
            icon = alert_icons.get(alert_type, '💡')

            subject = f"{icon} Trading System Alert: {alert_type.upper()}"

            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5;">
                <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: {color};">{icon} System Alert</h2>

                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                        <p style="margin: 0; font-size: 16px;">{alert_message}</p>
                    </div>

                    <div style="background-color: #e9ecef; padding: 10px; border-radius: 5px; margin-top: 15px;">
                        <p style="margin: 0; font-size: 12px; color: #666;">
                            Alert sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """

            text_content = f"System Alert: {alert_message}\n\nAlert sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            sg = SendGridAPIClient(self.api_key)
            message = Mail(
                from_email=Email(sender_email),
                to_emails=To(recipient_email),
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content
            )

            response = sg.send(message)

            if response.status_code == 202:
                logger.info(f"System alert email sent successfully: {alert_type}")
                return True
            else:
                logger.error(f"Failed to send alert email. Status code: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"SendGrid alert error: {e}")
            return False

# Global email service instance
email_service = EmailService()
