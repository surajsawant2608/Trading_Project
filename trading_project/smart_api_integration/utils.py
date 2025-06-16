from smart_api_integration.models import UserApiTokens, UserApiCredentials
# from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

class UserCredentialManager:
    """Helper class to fetch user API credentials and tokens."""

    @staticmethod
    def get_credentials_and_tokens(user):
        """
        Fetch API credentials and tokens for the given user.

        Args:
            user (User): The Django user instance.

        Returns:
            tuple: (api_key, client_id, auth_token, feed_token) or (None, None, None, None)
        """
        try:
            if not user.is_authenticated:
                logger.error("Unauthenticated user. Cannot fetch credentials.")
                return None, None, None, None
            
            credentials = UserApiCredentials.objects.get(user=user)
            tokens = UserApiTokens.objects.get(user=user)

            return (
                credentials.api_key,
                credentials.client_id,
                tokens.jwt_token,
                tokens.feed_token,
            )

        except UserApiCredentials.DoesNotExist:
            logger.error(f"UserApiCredentials not found for user: {user}")
        except UserApiTokens.DoesNotExist:
            logger.error(f"UserApiTokens not found for user: {user}")
        except Exception as e:
            logger.error(f"Error fetching user credentials: {e}")

        return None, None, None, None
