import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from django.db import transaction

from apptfg.models import EmailVerificationCode


def generate_code():
    return f"{random.randint(0, 999999):06d}"


@transaction.atomic
def register_user(username, email, password):
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        is_active=False
    )

    code = generate_code()

    EmailVerificationCode.objects.create(
        user=user,
        code=code,
        expires_at=timezone.now() + timedelta(minutes=10)
    )

    send_mail(
        subject="Código de verificación - TFG",
        message=f"Tu código de verificación es: {code}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

    return user

def verify_email_code(email, code):
    user = User.objects.filter(email=email, is_active=False).first()
    if not user:
        return False, "No existe ninguna cuenta pendiente con ese correo."

    verification = (
        EmailVerificationCode.objects
        .filter(user=user, code=code, is_used=False)
        .order_by("-created_at")
        .first()
    )

    if not verification:
        return False, "El código no es válido."

    if verification.is_expired():
        return False, "El código ha caducado."

    verification.is_used = True
    verification.save()

    user.is_active = True
    user.save()

    return True, "Cuenta verificada correctamente. Ya puedes iniciar sesión."