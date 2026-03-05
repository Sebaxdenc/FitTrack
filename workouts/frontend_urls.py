from django.urls import path

from .frontend_views import HomeView, LandingView, LoginView, RegisterView

urlpatterns = [
    path('', LandingView.as_view(), name='landing'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('home/', HomeView.as_view(), name='dashboard-home'),
]
