import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import threading


def send_plan_success(
    user_name: str, user_email: str, referral_link: str, plan_name: str
):
    # Define HTML content for the email template
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Plan Activated</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }}

        .container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #fff;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }}

        h1 {{
            color: #333;
            text-align: left;
            font-size: 24px;
            margin-bottom: 10px;
        }}

        p {{
            color: #666;
            font-size: 16px;
            line-height: 1.6;
        }}
    </style>
    </head>
    <body>
    <div class="container">
        <h1>Plan Activated</h1>
        <p>Hello {user_name},</p>
        <p>Greetings from Eatoearn</p>
        <p>Congratulations, your plan has been activated! Now you can refer anybody with your unique referral link to get benefits and also liquidate your plan BENIFITS within the specified time period!</p>
        <p>Referral Link: {referral_link}</p>
        <p>Plan activated: "{plan_name}"</p>
        <br/>
        <p>With your free plan benefits, You can now order any of these foods within the specified time period.</p>
        <p><strong>Note:</strong> If you don’t use these benefits in the specific time period, it will expire and you will have no benefit of it!</p>
        <p>We wish you the best of luck for this wonderful journey with Eatoearn.</p>
        <p>Best regards,</p>
        <p>Team Eatoearn</p>
        <p>For help, contact support@eatoearn.com</p>
    </div>
    </body>
    </html>
    """

    # Create message object
    msg = MIMEMultipart()
    msg.set_unixfrom("author")
    msg["From"] = "support@eatoearn.com"
    msg["To"] = user_email
    msg["Subject"] = "Successful Plan Order"

    # Attach HTML content
    msg.attach(MIMEText(html_content, "html"))

    # SMTP setup
    mailserver = smtplib.SMTP_SSL(
        "smtpout.secureserver.net", 465
    )  # Port 465 will be used
    mailserver.ehlo()
    mailserver.login("support@eatoearn.com", "Eatoearn@123")  # Email and password

    # Send email
    mailserver.sendmail("support@eatoearn.com", user_email, msg.as_string())

    # Quit SMTP server
    mailserver.quit()


def send_order_success(user_name: str, user_email: str):
    # Define HTML content for the email template
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Food Order Confirmation</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }}

        .container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #fff;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }}

        h1 {{
            color: #333;
            text-align: left;
            font-size: 24px;
            margin-bottom: 10px;
        }}

        p {{
            color: #666;
            font-size: 16px;
            line-height: 1.6;
            margin-top: 5px;
            margin-bottom: 5px;
        }}
    </style>
    </head>
    <body>
    <div class="container">
        <h1>Food Order Confirmation</h1>
        <p>Dear {user_name},</p>
        <p>Your food order has been successfully placed with Eatoearn. Our team is now processing your order, and you can expect to receive your delicious meal shortly.</p>
        <p>At Eatoearn, we strive to provide a hassle-free experience for our customers. Should you have any questions or concerns regarding your order, please do not hesitate to contact us.</p>
        <p>Thank you for choosing Eatoearn. We look forward to serving you again in the future.</p>
        <p>Best regards,</p>
        <p>Team Eatoearn</p>
        <p>For assistance, please contact <a href="mailto:support@eatoearn.com">support@eatoearn.com</a></p>
    </div>
    </body>
    </html>
    """

    # Create message object
    msg = MIMEMultipart()
    msg.set_unixfrom("author")
    msg["From"] = "support@eatoearn.com"
    msg["To"] = user_email
    msg["Subject"] = "Order successful"

    # Attach HTML content
    msg.attach(MIMEText(html_content, "html"))

    # SMTP setup
    mailserver = smtplib.SMTP_SSL(
        "smtpout.secureserver.net", 465
    )  # Port 465 will be used
    mailserver.ehlo()
    mailserver.login("support@eatoearn.com", "Eatoearn@123")  # Email and password

    # Send email
    mailserver.sendmail("support@eatoearn.com", user_email, msg.as_string())

    # Quit SMTP server
    mailserver.quit()


def send_referral_success(
    referrer_name: str,
    referred_name: str,
    plan_name: str,
    user_email: str,
    mode="Level 1",
):
    # Define HTML content for the email template
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Referral Successful</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }}

        .container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #fff;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }}

        h1 {{
            color: #333;
            text-align: left;
            font-size: 24px;
            margin-bottom: 10px;
        }}

        p {{
            color: #666;
            font-size: 16px;
            line-height: 1.6;
            margin-top: 5px;
            margin-bottom: 5px;
        }}
    </style>
    </head>
    <body>
    <div class="container">
        <h1>Referral Successful</h1>
        <p>Hello {referrer_name},</p>
        <p>Greetings from Eatoearn</p>
        <p>You have successfully referred <strong>{referred_name}</strong> with a plan "<strong>{plan_name}</strong>". You can go to your AFFILIATE INCOME and track your earnings.</p>
        <p>Earning Level: {mode} </p>
        <p>Now help your referee to get more benefits from Eatoearn, and you will have benefits too!</p>
        <p>We are happy to help you if you face any issue.</p>
        <p>Best Regards,</p>
        <p>Team Eatoearn</p>
        <p>For help, contact <a href="mailto:support@eatoearn.com">support@eatoearn.com</a></p>
    </div>
    </body>
    </html>
    """

    # Create message object
    msg = MIMEMultipart()
    msg.set_unixfrom("author")
    msg["From"] = "support@eatoearn.com"
    msg["To"] = user_email
    msg["Subject"] = "Referral Successful"

    # Attach HTML content
    msg.attach(MIMEText(html_content, "html"))

    # SMTP setup
    mailserver = smtplib.SMTP_SSL(
        "smtpout.secureserver.net", 465
    )  # Port 465 will be used
    mailserver.ehlo()
    mailserver.login("support@eatoearn.com", "Eatoearn@123")  # Email and password

    # Send email
    mailserver.sendmail("support@eatoearn.com", user_email, msg.as_string())

    # Quit SMTP server
    mailserver.quit()


async def send_redeem_success(user_uid: str, user_collection, is_redeem=False):
    if is_redeem == True:
        _user = await user_collection.find_one({"user_uid": user_uid})
        if _user is not None:
            user_name = _user.get("user_name") or _user.get("user_email")
            user_email = _user.get("user_email")
            t1 = threading.Thread(
                target=send_redeem_success_email, args=(user_name, user_email)
            )
            t1.start()
    # END


def send_redeem_success_email(user_name: str, user_email: str):
    # Define HTML content for the email template
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Plan Benefits redeemed</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }}

        .container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #fff;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }}

        h1 {{
            color: #333;
            text-align: left;
            font-size: 24px;
            margin-bottom: 10px;
        }}

        p {{
            color: #666;
            font-size: 16px;
            line-height: 1.6;
            margin-top: 5px;
            margin-bottom: 5px;
        }}
        
    </style>
    </head>
    <body>
    <div class="container">
        <h1>Benefits redeemed!</h1>
        <p>Hi {user_name},</p>
        <p>Congratulations! You've successfully redeemed your plan benefits on EatoEarn. Enjoy exploring exclusive deals and perks!</p>
        <p>Best regards,</p>
        <p>EatoEarn Team</p>
        <p>Any help: <a href="mailto:support@eatoearn.com">support@eatoearn.com</a></p>
    </div>
    </body>
    </html>
    """

    # Create message object
    msg = MIMEMultipart()
    msg.set_unixfrom("author")
    msg["From"] = "support@eatoearn.com"
    msg["To"] = user_email
    msg["Subject"] = "Your Plan Benefits have redeemed successfully!"

    # Attach HTML content
    msg.attach(MIMEText(html_content, "html"))

    # SMTP setup
    mailserver = smtplib.SMTP_SSL(
        "smtpout.secureserver.net", 465
    )  # Port 465 will be used
    mailserver.ehlo()
    mailserver.login("support@eatoearn.com", "Eatoearn@123")  # Email and password

    # Send email
    mailserver.sendmail("support@eatoearn.com", user_email, msg.as_string())

    # Quit SMTP server
    mailserver.quit()


def send_plan_admin(user_name: str, plan_name: str):
    # Define HTML content for the email template
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Plan Ordered</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }}

        .container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #fff;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }}

        h1 {{
            color: #333;
            text-align: left;
            font-size: 24px;
            margin-bottom: 10px;
        }}

        p {{
            color: #666;
            font-size: 16px;
            line-height: 1.6;
        }}
    </style>
    </head>
    <body>
    <div class="container">
        <h1>Plan Ordered</h1>
        <p>User: {user_name},</p>
        <p>Plan bought: "{plan_name}"</p>
        <p>Best regards,</p>
        <p>Team Eatoearn</p>
    </div>
    </body>
    </html>
    """

    # Create message object
    msg = MIMEMultipart()
    msg.set_unixfrom("author")
    msg["From"] = "support@eatoearn.com"
    msg["To"] = "eatoearn@gmail.com"
    msg["Subject"] = "New Plan Order"

    # Attach HTML content
    msg.attach(MIMEText(html_content, "html"))

    # SMTP setup
    mailserver = smtplib.SMTP_SSL(
        "smtpout.secureserver.net", 465
    )  # Port 465 will be used
    mailserver.ehlo()
    mailserver.login("support@eatoearn.com", "Eatoearn@123")  # Email and password

    # Send email
    mailserver.sendmail("support@eatoearn.com", "eatoearn@gmail.com", msg.as_string())

    # Quit SMTP server
    mailserver.quit()


# UTIL FUNC...
def generate_food_list_html(food_list):
    # Initialize an empty string to store HTML content
    html_content = ""
    html_content += (
        f"<string>Food Name | Food type | Quantity | Food Price</strong><br/>"
    )
    # Loop through each food item in the list
    for food in food_list:
        # Add HTML content for each food item
        html_content += f"<li>{food.food_name} | {food.food_type} | {food.food_qty} | &#8377;{food.food_price}</li>"

    # Return the HTML content for the food list
    return html_content


def send_food_admin(user_name: str, food_items, total: float):
    # Define HTML content for the email template
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Food Order</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }}

        .container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #fff;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }}

        h1 {{
            color: #333;
            text-align: left;
            font-size: 24px;
            margin-bottom: 10px;
        }}

        p {{
            color: #666;
            font-size: 16px;
            line-height: 1.6;
        }}
    </style>
    </head>
    <body>
    <div class="container">
        <h1>Food Ordered</h1>
        <h2> Total: {total} </h2>
        <p>User: {user_name},</p>
        <p>Food order items:</p>
        <ul>
            {generate_food_list_html(food_items)}
        </ul>
        <p>Best regards,</p>
        <p>Team Eatoearn</p>
    </div>
    </body>
    </html>
    """

    # Create message object
    msg = MIMEMultipart()
    msg.set_unixfrom("author")
    msg["From"] = "support@eatoearn.com"
    msg["To"] = "eatoearn@gmail.com"
    msg["Subject"] = "New Food Order"

    # Attach HTML content
    msg.attach(MIMEText(html_content, "html"))

    # SMTP setup
    mailserver = smtplib.SMTP_SSL(
        "smtpout.secureserver.net", 465
    )  # Port 465 will be used
    mailserver.ehlo()
    mailserver.login("support@eatoearn.com", "Eatoearn@123")  # Email and password

    # Send email
    mailserver.sendmail("support@eatoearn.com", "eatoearn@gmail.com", msg.as_string())

    # Quit SMTP server
    mailserver.quit()


# END
