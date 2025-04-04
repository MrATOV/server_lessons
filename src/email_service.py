import os
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

from src.schemas import EmailSchema, EmailWithAttachmentSchema

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = os.getenv("SMTP_PORT")
        self.smtp_user = os.getenv("SMTP_EMAIL")
        self.smtp_password = os.getenv("SMTP_PASS")
        self.from_email = os.getenv("SMTP_EMAIL")

    async def send_email(self, email_data: EmailSchema):
        message = MIMEMultipart()
        message["From"] = self.from_email
        message["To"] = email_data.email_to
        message["Subject"] = email_data.subject
        message.attach(MIMEText(email_data.body, "html"))

        return await self._send_message(message)

    async def send_email_with_attachement(self, email_data: EmailWithAttachmentSchema):
        message = MIMEMultipart()
        message["From"] = self.from_email
        message["To"] = email_data.email_to
        message["Subject"] = email_data.subject
        message.attach(MIMEText(email_data.body, "html"))

        part = MIMEApplication(email_data.attachement, Name=email_data.filename)
        part["Content-Disposition"] = f'attachment; filename="{email_data.filename}"'
        message.attach(part)

        return await self._send_message(message)

    async def _send_message(self, message: MIMEMultipart):
        try:
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                use_tls=False
            )
            return {"status": "Email send successfully"}
        except Exception as e:
            return {"error": str(e)}