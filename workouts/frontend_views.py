from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View

from .forms import LoginForm, RegistrationForm


class LoginView(View):
    template_name = 'auth/login.html'

    def get(self, request):
        return render(request, self.template_name, {
            'form': LoginForm(),
            'next_url': request.GET.get('next', ''),
        })

    def post(self, request):
        form = LoginForm(request.POST)
        next_url = request.POST.get('next') or 'dashboard-home'
        if form.is_valid():
            login(request, form.cleaned_data['user'])
            messages.success(request, 'Inicio de sesión exitoso.')
            return redirect(next_url)
        messages.error(request, 'No pudimos iniciar sesión. Revisa tus datos.')
        return render(request, self.template_name, {
            'form': form,
            'next_url': next_url,
        })


class RegisterView(View):
    template_name = 'auth/register.html'

    def get(self, request):
        return render(request, self.template_name, {'form': RegistrationForm()})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cuenta creada correctamente. Inicia sesión para continuar.')
            return redirect('auth-login')
        messages.error(request, 'Revisa los campos del registro para continuar.')
        return render(request, self.template_name, {'form': form})


class HomeView(LoginRequiredMixin, View):
    template_name = 'dashboard/home.html'

    def get(self, request):
        sample_meal = {
            'title': 'Pescado y Verduras',
            'subtitle': 'Ejemplo dinner dependiendo de la hora',
            'time_range': '7pm - 9pm',
        }
        sample_routine = {
            'title': 'Gym - Pierna',
            'focus': 'Enfoque en cuádriceps y glúteos',
            'cta': 'Ver detalles',
        }
        return render(request, self.template_name, {
            'user': request.user,
            'meal': sample_meal,
            'routine': sample_routine,
        })


class LandingView(View):
    template_name = 'landing.html'

    def get(self, request):
        return render(request, self.template_name)
