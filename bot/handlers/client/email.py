import logging
import aiosmtplib
from random import choice
from email.message import EmailMessage
from aiosmtplib.errors import SMTPAuthenticationError

from create_bot import bot
from configs.env_reader import config
from handlers.admin.send_on import send_to_admins


emails = [
    {
        "email": "nes.cafe.user1@gmail.com",
        "password": config.EMAIL1_PASSWORD.get_secret_value(),
    },
    {
        "email": "nes.cafe.user2@gmail.com",
        "password": config.EMAIL2_PASSWORD.get_secret_value(),  
    },
    {
        "email": "nes.cafe.user4@gmail.com",
        "password": config.EMAIL4_PASSWORD.get_secret_value(),
    },
    {
        "email": "nes.cafe.user5@gmail.com",
        "password": config.EMAIL5_PASSWORD.get_secret_value(),  
    },
    {
        "email": "nes.cafe.user6@gmail.com",
        "password": config.EMAIL6_PASSWORD.get_secret_value(),  
    },
]


async def send_email(email_to, text):
    """
    Sends an email with a verification code to the specified email address.
    If the email sender fails, it retries with another email account.
    """
    global emails

    try:
        email_sender = choice(emails)

        message = EmailMessage()
        message["Subject"] = "Код подтверждения (ValentiNES)"
        message["From"] = email_sender["email"]
        message["To"] = email_to
        message.set_content(text)


        await aiosmtplib.send(
            message,
            username=email_sender["email"],
            password=email_sender["password"],
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
        )
    except SMTPAuthenticationError:
        logging.warning(f"process='email send'                      !! Email \"{email_sender['email']}\" is not working. Was trying to send email to {email_to}.")

        await send_to_admins(f"WARNING: Email \"{email_sender['email']}\" is not working")

        await send_email(email_to, text)

    return


async def test_emails():
    """
    Tests all configured email accounts to ensure they are working. 
    Removes non-working email accounts from the list.
    """
    global emails
    
    logging.info("### Checking emails ... ###")

    failed_emails = []

    for email_sender in emails:
        try:
            message = EmailMessage()
            message["Subject"] = "Проверка работоспособности (ValentiNES)"
            message["From"] = email_sender["email"]
            message["To"] = "vbalabaev@nes.ru"
            message.set_content("Почта работает.")


            await aiosmtplib.send(
                message,
                username=email_sender["email"],
                password=email_sender["password"],
                hostname="smtp.gmail.com",
                port=587,
                start_tls=True,
            )

        except SMTPAuthenticationError:
            logging.warning(f"process='email test' !! Email \"{email_sender['email']}\" is not working.")

            await send_to_admins(f"WARNING: Email \"{email_sender['email']}\" is not working")

            failed_emails.append(email_sender)

    for email_sender in failed_emails:
        emails.remove(email_sender);

    logging.info("### Emails have been checked! ###")

    return
