import os
from flask import Flask
from smtplib import SMTP_SSL

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "unsafe-key")

@app.route("/")
def hello():
    return "🚀 Hello from Flask on https://qualclamps.com/!"

@app.route("/send-mail")
def send_mail():
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    to = "someone@example.com"
    subject = "Test Email from Flask"
    body = "This is a test email from Flask on qualclamps.com"

    message = f"Subject: {subject}\n\n{body}"

    with SMTP_SSL("mail.qualclamps.com", 465) as smtp:
        smtp.login(smtp_user, smtp_pass)
        smtp.sendmail(smtp_user, to, message)

    return "✅ Mail sent!"
