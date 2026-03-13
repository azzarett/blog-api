from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import override


def send_welcome_email(user) -> None:
    with override(user.preferred_language):
        subject = render_to_string('emails/welcome/subject.txt').strip()
        message = render_to_string('emails/welcome/body.txt', {'user': user})

    send_mail(
        subject=subject,
        message=message,
        from_email=None,
        recipient_list=[user.email],
        fail_silently=False,
    )
