from celery import shared_task

from apps.users.models import User
from apps.users.services import send_welcome_email as send_welcome_email_service

@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3
)
def send_welcome_email(user_id):
    # Retry protects against transient SMTP/network delivery failures.
    user = User.objects.get(id=user_id)
    send_welcome_email_service(user)