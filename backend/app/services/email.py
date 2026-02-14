import logging

from app.config import settings

logger = logging.getLogger(__name__)


async def send_magic_link_email(email: str, token: str) -> None:
    magic_link = f"{settings.frontend_url}/auth/verify?token={token}"

    if not settings.resend_api_key:
        logger.info("=== MAGIC LINK (dev mode) ===")
        logger.info(f"Email: {email}")
        logger.info(f"Link: {magic_link}")
        logger.info("=============================")
        print(f"\n{'='*50}")
        print(f"MAGIC LINK for {email}:")
        print(f"{magic_link}")
        print(f"{'='*50}\n")
        return

    import resend

    resend.api_key = settings.resend_api_key
    resend.Emails.send(
        {
            "from": "CoffeeRun <noreply@ftt.qlndemo.com>",
            "to": [email],
            "subject": "Your CoffeeRun login link",
            "html": f"""
                <h2>Login to CoffeeRun</h2>
                <p>Click the link below to log in. This link expires in {settings.magic_link_expiry_minutes} minutes.</p>
                <p><a href="{magic_link}" style="display:inline-block;padding:12px 24px;background:#8B4513;color:white;text-decoration:none;border-radius:6px;">Log in to CoffeeRun</a></p>
                <p><small>If you didn't request this, you can safely ignore this email.</small></p>
            """,
        }
    )
