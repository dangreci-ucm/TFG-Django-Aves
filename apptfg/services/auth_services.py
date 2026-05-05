import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from django.db import transaction

from apptfg.models import EmailVerificationCode, PasswordResetCode


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


def resend_verification_code(email):
    email = email.strip().lower()

    user = User.objects.filter(email=email, is_active=False).first()
    if not user:
        return False, "No existe ninguna cuenta pendiente de verificación con ese correo."

    code = generate_code()

    EmailVerificationCode.objects.create(
        user=user,
        code=code,
        expires_at=timezone.now() + timedelta(minutes=10)
    )

    send_mail(
        subject="Nuevo código de verificación - TFG",
        message=f"Tu nuevo código de verificación es: {code}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

    return True, "Te hemos enviado un nuevo código de verificación."


def send_password_reset_code(email):
    email = email.strip().lower()

    user = User.objects.filter(email=email, is_active=True).first()
    if not user:
        return False, "No existe ninguna cuenta activa con ese correo."

    code = generate_code()

    PasswordResetCode.objects.create(
        user=user,
        code=code,
        expires_at=timezone.now() + timedelta(minutes=10)
    )

    send_mail(
        subject="Código para recuperar contraseña - TFG",
        message=f"Tu código para restablecer la contraseña es: {code}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

    return True, "Te hemos enviado un código para restablecer tu contraseña."


@transaction.atomic
def reset_password_with_code(email, code, new_password):
    email = email.strip().lower()

    user = User.objects.filter(email=email, is_active=True).first()
    if not user:
        return False, "No existe ninguna cuenta activa con ese correo."

    reset_obj = (
        PasswordResetCode.objects
        .filter(user=user, code=code, is_used=False)
        .order_by("-created_at")
        .first()
    )

    if not reset_obj:
        return False, "El código no es válido."

    if reset_obj.is_expired():
        return False, "El código ha caducado."

    reset_obj.is_used = True
    reset_obj.save()

    user.set_password(new_password)
    user.save()

    return True, "Tu contraseña se ha actualizado correctamente. Ya puedes iniciar sesión."
