import logging
import pyotp
from django.contrib.auth.models import User
from django.utils import timezone
from smart_api_integration.models import UserApiCredentials, UserApiTokens
from SmartApi import SmartConnect

logger = logging.getLogger(__name__)

class UserCredentialManager:
    """
    Helper class to manage user SmartAPI credentials and token lifecycle.
    """

    @staticmethod
    def get_credentials_and_tokens(user):
        """
        Fetch API credentials and tokens for a given Django user.

        Args:
            user (User): The Django user instance.

        Returns:
            tuple: (api_key, client_id, jwt_token, feed_token) or (None, None, None, None)
        """
        try:
            # if not user.is_authenticated:
            #     logger.warning("User is not authenticated.")
            #     return None, None, None, None

            creds = UserApiCredentials.objects.get(user=user)
            tokens = UserApiTokens.objects.get(user=user)

            return {
                "status": "success",
                "data": {
                    "jwt_token": tokens.jwt_token,
                    "feed_token": tokens.feed_token,
                    "client_code": creds.client_id,
                    "api_key": creds.api_key
                }
            }
        except UserApiCredentials.DoesNotExist:
            logger.error(f"❌ UserApiCredentials not found for user: {user}")
            return {
                "status": "error",
                "message": "User API credentials not found."
            }
        except UserApiTokens.DoesNotExist:
            logger.error(f"❌ UserApiTokens not found for user: {user}")
            return {
                "status": "error",
                "message": "User API tokens not found."
            }
        except Exception as e:
            logger.error(f"❌ Error fetching credentials: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

        

    @staticmethod
    def regenerate_tokens(user):
        """
        Regenerates SmartAPI tokens (JWT, feed) using OTP and updates the database.

        Args:
            user_id (int): Django user ID.

        Returns:
            dict: {
                "status": "success",
                "data": {
                    "jwt_token": str,
                    "feed_token": str,
                    "client_code": str,
                    "api_key": str
                }
            }
            OR
            {
                "status": "error",
                "message": str
            }
        """
        try:
            user_credentials = UserApiCredentials.objects.get(user=user)
            otp = pyotp.TOTP(user_credentials.otp_secret_key).now()
            connection_object = SmartConnect(api_key=user_credentials.api_key)
            session_data = connection_object.generateSession(
                user_credentials.client_id,
                user_credentials.passcode,
                otp
            )
            
            # Save new tokens
            jwt_token = session_data['data']['jwtToken']
            refresh_token = session_data['data']['refreshToken']
            feed_token = connection_object.getfeedToken()

            # Correctly associate user_credentials and update existing record if found
            user_tokens, created = UserApiTokens.objects.update_or_create(
                user_credentials=user_credentials,
                defaults={
                    "user": user_credentials.user,
                    "jwt_token": jwt_token,
                    "refresh_token": refresh_token,
                    "feed_token": feed_token,
                    "expires_at": timezone.now() + timezone.timedelta(hours=24)
                }
            )
            return {
                "status": "success",
                "data": {
                    "jwt_token": jwt_token,
                    "feed_token": feed_token,
                    "client_code": user_credentials.client_id,
                    "api_key": user_credentials.api_key
                }
            }

        except Exception as e:
            logger.error(f"❌ Token regeneration failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
