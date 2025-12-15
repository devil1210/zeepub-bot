import logging
import functools
from telegram import Update
from telegram.ext import ContextTypes
from config.config_settings import config
from utils.rate_limiter import rate_limiter, RateLimitType

logger = logging.getLogger(__name__)


def _get_update_context(args):
    """Auxiliary to find Update and Context in args."""
    update = None
    context = None
    for arg in args:
        if isinstance(arg, Update):
            update = arg
        # We can also check for ContextTypes, but usually if we have update we are good
        # Context is useful but not strictly needed for these decorators' logic
    return update


def admin_only(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        update = _get_update_context(args)
        if update:
            user_id = update.effective_user.id
            if user_id not in config.ADMIN_USERS:
                await update.message.reply_text(
                    "❌ Este comando es solo para administradores."
                )
                return
        return await func(*args, **kwargs)

    return wrapper


def log_user_action(action_name: str):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            update = _get_update_context(args)
            if update:
                user_id = update.effective_user.id
                username = update.effective_user.username or "unknown"
                logger.info(f"User {user_id} (@{username}) performed action: {action_name}")
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def rate_limit(limit_type_str: str, max_requests: int = 10, window_seconds: int = 60):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            update = _get_update_context(args)
            if update and update.effective_user:
                user_id = update.effective_user.id
                
                # Convert string to Enum or use DEFAULT if not found
                try:
                    limit_type = RateLimitType(limit_type_str)
                except ValueError:
                    limit_type = RateLimitType.DEFAULT
                
                rate_limiter.set_default_limit(limit_type, max_requests, window_seconds)
                
                allowed = await rate_limiter.is_allowed(user_id, limit_type)
                if not allowed:
                    logger.warning(f"Rate limit exceeded for user {user_id} on {limit_type_str}")
                    # Reply if possible
                    if update.message:
                        await update.message.reply_text(
                            "⚠️ Has excedido el límite de solicitudes. Por favor espera un momento."
                        )
                    return

            return await func(*args, **kwargs)

        return wrapper

    return decorator
