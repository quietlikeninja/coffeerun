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
        print(f"\n{'=' * 50}")
        print(f"MAGIC LINK for {email}:")
        print(f"{magic_link}")
        print(f"{'=' * 50}\n")
        return

    import resend

    resend.api_key = settings.resend_api_key
    resend.Emails.send(
        {
            "from": settings.email_from,
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


async def send_team_invite_email(
    email: str, token: str, team_name: str, inviter_email: str
) -> None:
    invite_link = f"{settings.frontend_url}/invite?token={token}"

    if not settings.resend_api_key:
        logger.info("=== TEAM INVITE (dev mode) ===")
        logger.info(f"To: {email}")
        logger.info(f"Team: {team_name}")
        logger.info(f"Invited by: {inviter_email}")
        logger.info(f"Link: {invite_link}")
        logger.info("==============================")
        print(f"\n{'=' * 50}")
        print(f"TEAM INVITE for {email}:")
        print(f"Team: {team_name}")
        print(f"Invited by: {inviter_email}")
        print(f"Link: {invite_link}")
        print(f"{'=' * 50}\n")
        return

    import resend

    resend.api_key = settings.resend_api_key
    resend.Emails.send(
        {
            "from": settings.email_from,
            "to": [email],
            "subject": f"You've been invited to {team_name} on CoffeeRun",
            "html": f"""
                <h2>You're invited to {team_name}!</h2>
                <p>{inviter_email} has invited you to join <strong>{team_name}</strong> on CoffeeRun.</p>
                <p><a href="{invite_link}" style="display:inline-block;padding:12px 24px;background:#8B4513;color:white;text-decoration:none;border-radius:6px;">Accept Invite</a></p>
                <p><small>This invite expires in {settings.invite_expiry_days} days. If you weren't expecting this, you can safely ignore it.</small></p>
            """,
        }
    )
