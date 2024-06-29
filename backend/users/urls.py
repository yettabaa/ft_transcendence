from django.urls import path
from .views import SignUp, LogIn

urlpatterns = [
    path('register/', SignUp.as_view(), name='sign-up'),
    path('login/', LogIn.as_view(), name='login'),
]
