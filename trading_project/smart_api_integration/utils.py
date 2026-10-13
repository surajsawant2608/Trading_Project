import logging
import pyotp
from django.utils import timezone
from smart_api_integration.models import UserApiCredentials, UserApiTokens
from SmartApi.smartConnect import SmartConnect

logger = logging.getLogger(__name__)

class SmartApiClientFactory:
    """
    Centralized Gateway Factory for SmartConnect.
    Returns an authenticated SmartConnect client instance without 
    exposing raw credentials or requiring manual token management.
    """

    @classmethod
    def get_client(cls, user, auto_regenerate=True):
        """
        Returns an authenticated SmartConnect instance or raises an Exception.
        """
        try:
            creds = UserApiCredentials.objects.get(user=user)
            if creds.status != 'active':
                raise PermissionError(f"API Credentials are {creds.status}.")

            tokens = UserApiTokens.objects.filter(user=user).first()

            # Trigger auto-regeneration if missing, marked failed, or expired
            needs_refresh = (
                not tokens or 
                tokens.status == 'failed' or 
                (tokens.expires_at and tokens.expires_at <= timezone.now())
            )

            if needs_refresh:
                if auto_regenerate:
                    logger.info(f"Regenerating session for user {user.username}...")
                    return cls.regenerate_client_session(creds)
                else:
                    raise PermissionError("Tokens are expired or invalidated.")

            # Create client with existing valid tokens
            client = SmartConnect(api_key=creds.api_key)
            client.setAccessToken(tokens.jwt_token)
            client.setFeedToken(tokens.feed_token)
            client.setUserId(creds.client_id)
            return client

        except (UserApiCredentials.DoesNotExist, UserApiTokens.DoesNotExist) as e:
            logger.error(f"Credentials not found for {user}: {e}")
            raise e

    @classmethod
    def regenerate_client_session(cls, creds):
        """
        Generates a fresh SmartConnect session using TOTP, updates DB,
        and returns the initialized SmartConnect instance.
        """
        otp = pyotp.TOTP(creds.otp_secret_key).now()
        client = SmartConnect(api_key=creds.api_key)
        
        session = client.generateSession(
            creds.client_id,
            creds.passcode,
            otp
        )

        if not session or not session.get("status"):
            error_msg = session.get("message", "Session generation failed") if session else "No response"
            logger.error(f"Session generation failed: {error_msg}")
            raise ConnectionError(error_msg)

        # In SmartConnect, generateSession already sets the internal tokens on `client`
        # Extract raw strings for database storage
        jwt_token = client.access_token
        feed_token = client.getfeedToken()
        refresh_token = session['data'].get('refreshToken', '')

        # Persist to database
        UserApiTokens.objects.update_or_create(
            user=creds.user,
            defaults={
                "user_credentials": creds,
                "jwt_token": jwt_token,
                "refresh_token": refresh_token,
                "feed_token": feed_token,
                "expires_at": timezone.now() + timezone.timedelta(hours=24),
                "status": "active"
            }
        )

        return client

    @classmethod
    def flag_token_failed(cls, user):
        """
        Flags token as failed so the next call automatically triggers TOTP regeneration.
        """
        UserApiTokens.objects.filter(user=user).update(status='failed')
        logger.warning(f"Tokens for user {user.username} marked as failed.")