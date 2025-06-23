import smtplib
from email.mime.text import MIMEText
from app.config import settings

def send_email(subject: str, body: str, recipients: list):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = settings.email_sender
    msg['To'] = ', '.join(recipients)
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        smtp_server.login(settings.email_sender, settings.email_password)
        smtp_server.sendmail(settings.email_sender, recipients, msg.as_string())
    print("Message sent!")

def send_verification_email(email: str, code: str):
    subject = "Ammury: Verify your email address"
    body = f"""
    Hello,

    Thank you for registering with Ammury.

    Your 4-digit verification code is:

    ===========================
            {code}
    ===========================

    This code is valid for the next 20 minutes.

    Best regards,  
    The Ammury Team
    """
    send_email(subject, body, [email])
