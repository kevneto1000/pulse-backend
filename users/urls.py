from django.urls import path
from .views import TestAuthView, RegisterView, ProfileView


urlpatterns = [
    path('test-auth/', TestAuthView.as_view()),
    path('register/', RegisterView.as_view()),
    path('profile/<str:username>/', ProfileView.as_view()),
]