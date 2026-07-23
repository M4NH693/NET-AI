import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from starlette.concurrency import run_in_threadpool

def send_email_sync(to_email: str, subject: str, html_content: str):
    """Gửi email đồng bộ sử dụng SMTP."""
    smtp_host = os.getenv("MAIL_HOST", "sandbox.smtp.mailtrap.io")
    try:
        smtp_port = int(os.getenv("MAIL_PORT", "2525"))
    except ValueError:
        smtp_port = 2525
        
    smtp_username = os.getenv("MAIL_USERNAME")
    smtp_password = os.getenv("MAIL_PASSWORD")
    from_email = os.getenv("MAIL_FROM", "noreply@netai.com")
    from_name = os.getenv("MAIL_FROM_NAME", "NetAI Portal")
    
    if not smtp_username or not smtp_password:
        raise Exception("Cấu hình Mailtrap SMTP (MAIL_USERNAME/MAIL_PASSWORD) chưa được thiết lập trong file .env.")
        
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to_email
    
    part = MIMEText(html_content, "html", "utf-8")
    msg.attach(part)
    
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(from_email, to_email, msg.as_string())

async def send_otp_email(to_email: str, otp_code: str):
    """Gửi email chứa mã OTP bất đồng bộ."""
    subject = f"Mã xác thực khôi phục mật khẩu: {otp_code}"
    html_content = f"""
    <html>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #0b0f19; color: #f3f4f6; padding: 20px;">
            <div style="max-width: 500px; margin: 0 auto; background-color: #111827; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 30px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
                <h2 style="color: #E100FF; margin-bottom: 10px; font-weight: bold;">NetAI Portal</h2>
                <p style="color: #9ca3af; font-size: 16px; margin-bottom: 20px;">Bạn đã yêu cầu khôi phục mật khẩu. Dưới đây là mã xác thực (OTP) gồm 4 chữ số của bạn:</p>
                <div style="font-size: 36px; font-weight: bold; letter-spacing: 5px; color: #00C6FF; margin: 20px 0; padding: 15px; background-color: rgba(0,0,0,0.3); border-radius: 8px; display: inline-block;">
                    {otp_code}
                </div>
                <p style="color: #9ca3af; font-size: 14px; margin-top: 20px;">Mã này có hiệu lực trong vòng 5 phút. Vui lòng không chia sẻ mã này với bất kỳ ai.</p>
                <hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.08); margin: 20px 0;">
                <p style="color: #6b7280; font-size: 12px;">Nếu bạn không yêu cầu thay đổi này, hãy bỏ qua email này.</p>
            </div>
        </body>
    </html>
    """
    await run_in_threadpool(send_email_sync, to_email, subject, html_content)
