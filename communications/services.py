import africastalking
import re
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.cache import cache
from typing import List, Dict, Union, Optional

logger = logging.getLogger(__name__)

class SMSService:
    def __init__(self):
        # Initialize Africa's Talking
        africastalking.initialize(
            settings.AFRICASTALKING_USERNAME,
            settings.AFRICASTALKING_API_KEY
        )
        self.sms = africastalking.SMS
        self.rate_limit = getattr(settings, 'SMS_RATE_LIMIT_PER_HOUR', 100)
        self.message_templates = {
            'payment_reminder': "Dear {name}, your rent payment of {amount} is due on {due_date}.",
            'maintenance_notice': "Dear {name}, maintenance is scheduled for {date} at {time}.",
            'welcome': "Welcome {name}! Your tenancy at {property} begins on {start_date}."
        }

    def validate_phone_number(self, phone: str) -> str:
        """Validate phone number format and ensure it has all necessary digits"""
        # Remove any spaces, dashes, or parentheses
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Check if it starts with + and has at least 10 digits
        if not re.match(r'^\+\d{10,15}$', cleaned):
            raise ValidationError(f"Invalid phone number format: {phone}")
        
        return cleaned

    def check_rate_limit(self, sender: str) -> bool:
        """Check if sender has exceeded rate limit"""
        cache_key = f"sms_count_{sender}_{datetime.now().strftime('%Y%m%d%H')}"
        current_count = cache.get(cache_key, 0)
        
        if current_count >= self.rate_limit:
            return False
        
        cache.set(cache_key, current_count + 1, timeout=3600)  # 1 hour timeout
        return True

    def get_message_from_template(self, template_name: str, **kwargs) -> str:
        """Get formatted message from template"""
        if template_name not in self.message_templates:
            raise ValidationError(f"Template {template_name} not found")
        
        try:
            return self.message_templates[template_name].format(**kwargs)
        except KeyError as e:
            raise ValidationError(f"Missing template parameter: {str(e)}")

    def send_sms(
        self,
        recipients: Union[str, List[str], object],
        message: str,
        sender_id: Optional[str] = None,
        template_name: Optional[str] = None,
        template_params: Optional[Dict] = None
    ) -> Dict:
        try:
            # Use template if provided
            if template_name:
                message = self.get_message_from_template(template_name, **(template_params or {}))

            # Format recipients to list of validated phone numbers
            if isinstance(recipients, str):
                recipients = [self.validate_phone_number(recipients)]
            elif hasattr(recipients, 'all'):  # QuerySet
                recipients = [self.validate_phone_number(str(recipient.phone))
                             for recipient in recipients.all()]
            else:
                recipients = [self.validate_phone_number(str(phone))
                             for phone in recipients]

            # Check rate limit
            sender = sender_id or getattr(settings, 'AFRICASTALKING_SENDER_ID', 'default')
            if not self.check_rate_limit(sender):
                raise ValidationError(f"Rate limit exceeded for sender {sender}")

            # Use provided sender_id or default from settings
            send_params = {
                'message': message,
                'recipients': recipients
            }
            
            if sender_id:
                send_params['from'] = sender_id

            # Log the attempt
            logger.info(f"Sending SMS to {len(recipients)} recipients from {sender}")

            response = self.sms.send(**send_params)

            # Check for API-level errors
            sms_data = response.get('SMSMessageData', {})
            recipients_data = sms_data.get('Recipients', [])
            
            if not recipients_data:
                raise ValidationError("No recipients data in response")

            # Check for specific error codes
            failed_recipients = []
            successful_recipients = []
            for recipient in recipients_data:
                status_code = recipient.get('statusCode')
                recipient_info = {
                    'number': recipient.get('number'),
                    'status': recipient.get('status'),
                    'statusCode': status_code,
                    'messageId': recipient.get('messageId'),
                    'cost': recipient.get('cost')
                }
                
                if status_code != 101:  # 101 is success
                    failed_recipients.append(recipient_info)
                    logger.error(f"Failed to send SMS to {recipient_info['number']}: {recipient_info['status']}")
                else:
                    successful_recipients.append(recipient_info)
                    logger.info(f"Successfully sent SMS to {recipient_info['number']}")

            result = {
                'status': 'success' if not failed_recipients else 'partial_failure',
                'message_id': recipients_data[0].get('messageId') if recipients_data else None,
                'response': response,
                'successful_recipients': successful_recipients,
                'failed_recipients': failed_recipients,
                'total_cost': sms_data.get('Message', '').split('Total Cost: ')[-1] if 'Total Cost:' in sms_data.get('Message', '') else None,
                'timestamp': datetime.now().isoformat()
            }

            # Log the result
            logger.info(f"SMS sending completed. Status: {result['status']}, Cost: {result['total_cost']}")
            return result

        except ValidationError:
            raise
        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"SMS sending failed: {error_msg}", exc_info=True)
            
            # Handle specific error types
            if 'rejected by gateway' in error_msg:
                raise ValidationError("Sender ID not mapped to your account. Ensure your sender ID is properly registered.")
            elif 'invalid phone number' in error_msg:
                raise ValidationError("Invalid phone number format. Ensure numbers have all necessary digits.")
            elif 'insufficient balance' in error_msg:
                raise ValidationError("Insufficient account balance. Please top up your account.")
            elif 'risk hold' in error_msg:
                raise ValidationError("Account on risk hold. Contact support or use your own sender ID instead of default.")
            else:
                raise ValidationError(f"Failed to send SMS: {str(e)}")