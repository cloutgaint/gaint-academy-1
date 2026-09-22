import smtplib
from email.message import EmailMessage
from app.core.config import settings

def send_password_reset_otp(recipient: str, otp: str) -> None:
    if not settings.smtp_host or not settings.smtp_from_email:
        raise RuntimeError("Password reset email is not configured")
    msg=EmailMessage()
    msg["Subject"]="GAINT Academy password reset code"
    msg["From"]=settings.smtp_from_email
    msg["To"]=recipient
    msg.set_content(
        f"Your GAINT Academy password reset code is {otp}. "
        f"It expires in {settings.password_reset_otp_minutes} minutes. "
        "If you did not request this, you can ignore this email."
    )
    with smtplib.SMTP(settings.smtp_host,settings.smtp_port,timeout=15) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_username and settings.smtp_password:
            smtp.login(settings.smtp_username,settings.smtp_password)
        smtp.send_message(msg)
