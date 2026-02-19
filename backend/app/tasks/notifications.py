from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.celery_app import celery_app
from backend.app.core.config import settings
from backend.app.models.notification import Notification, NotificationType
from backend.app.models.user import User, UserRole

logger = logging.getLogger("databridge.tasks.notifications")

sync_engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
SyncSession = sessionmaker(bind=sync_engine)


@celery_app.task(name="backend.app.tasks.notifications.create_notification_task")
def create_notification_task(
    user_id: int,
    transfer_id: int,
    notif_type: str,
    title: str,
    message: str,
) -> dict:
    db: Session = SyncSession()
    try:
        notif = Notification(
            user_id=user_id,
            transfer_id=transfer_id if transfer_id else None,
            type=NotificationType(notif_type),
            title=title,
            message=message,
        )
        db.add(notif)
        db.commit()

        if settings.NOTIFICATION_ENABLED and settings.SMTP_HOST:
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.email:
                try:
                    send_email.delay(user.email, title, _build_email_html(title, message))
                    notif.email_sent = True
                    db.commit()
                except Exception:
                    logger.warning("Failed to queue email for user %d", user_id)

        return {"notification_id": notif.id}

    except Exception:
        logger.exception("Error creating notification for user %d", user_id)
        db.rollback()
        return {"error": "Failed to create notification"}
    finally:
        db.close()


@celery_app.task(name="backend.app.tasks.notifications.notify_role_task")
def notify_role_task(
    role: str,
    transfer_id: int,
    notif_type: str,
    title: str,
    message: str,
) -> dict:
    db: Session = SyncSession()
    try:
        role_enum = UserRole(role)
        users = db.query(User).filter(User.role == role_enum, User.is_active.is_(True)).all()
        created = 0
        for user in users:
            notif = Notification(
                user_id=user.id,
                transfer_id=transfer_id if transfer_id else None,
                type=NotificationType(notif_type),
                title=title,
                message=message,
            )
            db.add(notif)
            created += 1
        db.commit()

        if settings.NOTIFICATION_ENABLED and settings.SMTP_HOST:
            for user in users:
                if user.email:
                    try:
                        send_email.delay(user.email, title, _build_email_html(title, message))
                    except Exception:
                        pass

        logger.info("Notified %d %s users: %s", created, role, title)
        return {"notified": created, "role": role}

    except Exception:
        logger.exception("Error in notify_role_task for role %s", role)
        db.rollback()
        return {"error": "Failed"}
    finally:
        db.close()


@celery_app.task(name="backend.app.tasks.notifications.send_email")
def send_email(to_email: str, subject: str, body_html: str) -> dict:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[DataBridge] {subject}"
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = to_email

        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
            server.ehlo()
            if settings.SMTP_PORT == 587:
                server.starttls()
                server.ehlo()
            server.sendmail(settings.SMTP_FROM_EMAIL, [to_email], msg.as_string())

        logger.info("Email sent to %s: %s", to_email, subject)
        return {"sent": True, "to": to_email}

    except Exception:
        logger.exception("Failed to send email to %s: %s", to_email, subject)
        return {"sent": False, "to": to_email, "error": "SMTP failure"}


def _build_email_html(title: str, message: str) -> str:
    return f"""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 0; background: #0f172a;">
  <div style="max-width: 600px; margin: 0 auto; padding: 32px 24px;">
    <div style="background: #1e293b; border-radius: 12px; padding: 32px; border: 1px solid #334155;">
      <div style="text-align: center; margin-bottom: 24px;">
        <h1 style="color: #22d3ee; font-size: 20px; margin: 0;">DataBridge Pipeline</h1>
      </div>
      <h2 style="color: #f1f5f9; font-size: 18px; margin: 0 0 16px;">{title}</h2>
      <p style="color: #94a3b8; font-size: 14px; line-height: 1.6; white-space: pre-wrap;">{message}</p>
      <hr style="border: none; border-top: 1px solid #334155; margin: 24px 0;" />
      <p style="color: #475569; font-size: 12px; text-align: center;">
        This is an automated message from DataBridge Pipeline.
      </p>
    </div>
  </div>
</body>
</html>"""
