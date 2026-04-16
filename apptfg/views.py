from django.shortcuts import render, redirect
from django.contrib import messages

from .services import prediction_services
from .services import auth_services
from .forms import RegisterForm, VerifyCodeForm, ForgotPasswordForm, ResetPasswordForm
from django.views.decorators.http import require_http_methods



def principal(request):
    # frontend/pagina_principal.html
    return render(request, 'pagina_principal.html', {})


def iden(request):
    # frontend/identificacion.html
    return render(request, 'identificacion.html', {})


def descargas(request):
    # frontend/descargas.html
    return render(request, 'descargas.html', {})


def contacto(request):
    # frontend/contacto.html
    return render(request, 'contacto.html', {})



def calcular(request):
    # Este endpoint renderiza la misma pantalla de identificación, mostrando resultados
    if request.method == 'POST':
        huesos = prediction_services.build_huesos_from_post(request.POST)

        try:
            result_sort = prediction_services.calcular_prediccion(huesos)
        except ValueError as e:
            return render(request, 'identificacion.html', {'msg': str(e)})

        return render(request, 'identificacion.html', {'msg': 'Resultados', 'valor': result_sort})

    return render(request, 'identificacion.html', {})   


def register_view(request):
    if request.user.is_authenticated:
        messages.info(request, "Ya has iniciado sesión.")
        return redirect("/")
      
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                auth_services.register_user(
                    username=form.cleaned_data["username"],
                    email=form.cleaned_data["email"],
                    password=form.cleaned_data["password1"],
                )
                messages.success(request, "Te hemos enviado un código al correo.")
                return redirect(f"/accounts/verify-email/?email={form.cleaned_data['email']}")
            except Exception as e:
                messages.error(request, "No se pudo completar el registro.")
                print(f"Error en registro: {e}")
    else:
        form = RegisterForm()

    return render(request, "registration/register.html", {"form": form})


def verify_email_view(request):
    if request.user.is_authenticated:
        messages.info(request, "Ya has iniciado sesión.")
        return redirect("/")
    
    initial_email = request.GET.get("email", "")

    if request.method == "POST":
        form = VerifyCodeForm(request.POST)
        if form.is_valid():
            ok, message = auth_services.verify_email_code(
                email=form.cleaned_data["email"],
                code=form.cleaned_data["code"],
            )

            if ok:
                messages.success(request, message)
                return redirect("/accounts/login/")

            messages.error(request, message)
    else:
        form = VerifyCodeForm(initial={"email": initial_email})

    return render(request, "registration/verify_email.html", {"form": form})


@require_http_methods(["POST"])
def resend_verification_code_view(request):
    if request.user.is_authenticated:
        messages.info(request, "Ya has iniciado sesión.")
        return redirect("/")

    email = (request.POST.get("email") or "").strip().lower()

    if not email:
        messages.error(request, "Debes indicar un correo electrónico.")
        return redirect("/accounts/verify-email/")

    ok, message = auth_services.resend_verification_code(email)

    if ok:
        messages.success(request, message)
    else:
        messages.error(request, message)

    return redirect(f"/accounts/verify-email/?email={email}")


@require_http_methods(["GET", "POST"])
def forgot_password_view(request):
    if request.user.is_authenticated:
        messages.info(request, "Ya has iniciado sesión.")
        return redirect("/")

    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            ok, message = auth_services.send_password_reset_code(
                email=form.cleaned_data["email"]
            )

            if ok:
                messages.success(request, message)
                return redirect(f"/accounts/reset-password/?email={form.cleaned_data['email']}")

            messages.error(request, message)
    else:
        form = ForgotPasswordForm()

    return render(request, "registration/forgot_password.html", {"form": form})


@require_http_methods(["GET", "POST"])
def reset_password_view(request):
    if request.user.is_authenticated:
        messages.info(request, "Ya has iniciado sesión.")
        return redirect("/")

    initial_email = request.GET.get("email", "")

    if request.method == "POST":
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            ok, message = auth_services.reset_password_with_code(
                email=form.cleaned_data["email"],
                code=form.cleaned_data["code"],
                new_password=form.cleaned_data["new_password1"],
            )

            if ok:
                messages.success(request, message)
                return redirect("/accounts/login/")

            messages.error(request, message)
    else:
        form = ResetPasswordForm(initial={"email": initial_email})

    return render(request, "registration/reset_password.html", {"form": form})