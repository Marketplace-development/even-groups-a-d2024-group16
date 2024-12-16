from flask_mail import Message
from app import mail
from app.models import Transaction
from app import db

def check_and_notify_chef(chef_email, recipename):
    """
    Controleer of een chef notificatie moet ontvangen op basis van het aantal transacties.
    """
    transaction_count = db.session.query(Transaction).filter_by(chef_email=chef_email, recipename=recipename).count()
    if transaction_count == 10:
        send_email_to_chef(chef_email, recipename)

def send_email_to_chef(chef_email, recipename):
    """
    Stuur een notificatie-e-mail naar de chef.
    """
    msg = Message(
        subject="Time to Adjust Your Recipe Price!",
        sender="no-reply@dishcovery.com",
        recipients=[chef_email]
    )
    msg.body = f"""
    Congratulations! Your recipe '{recipename}' has been sold 10 times.
    This is a great opportunity to evaluate and adjust your pricing.
    
    Best regards,
    The Dishcovery Team
    """
    try:
        mail.send(msg)
        print(f"Email sent to {chef_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

