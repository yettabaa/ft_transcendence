from django.urls import path, re_path
# from .views import CustomAPIView, RegistrationView, LoginView
    #, LogoutView, ChangePasswordView
from . import views
from rest_framework_simplejwt import views as jwt_views

from .utils import TokenRefreshView
# from .views import MyTokenObtainPairView

app_name = 'users'

urlpatterns = [

    path('', views.CustomAPIView.as_view(), name='custom'),
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='refresh'),
    #? Seperate OAuth 
    path('generate-googlelink/', views.GoogleGenLink.as_view(), name='googlelink'),
    #? 42 OAuth
    path('generate-42link/', views.GenerateLink42.as_view(), name='42_Link'),
    #? 2FA
    path('2fa/', views.Check_2FAView.as_view(), name='2FA_check'),
    #?Forget Password
    path('forget-password/', views.ForgetPasswordView.as_view(), name='forget-password'),
    path('update-password/', views.UpdatePasswordView.as_view(), name='reset-passowrd'),
    #? 2FA Register
    path('oauth-register/', views.OAuth_Register().as_view(), name='OAuth_Register'),
    #? Profile end Point
    path('profile/', views.Profile().as_view(), name='profile'),
    path('users/<str:username>/', views.Users().as_view(), name='users'),
    path('matches/<str:username>/', views.UserMatches().as_view(), name='UserMatches'),
    path('matches/', views.Matches().as_view(), name='Matches'),
    path('friends/', views.FriendsView().as_view(), name='Friends'),
    path('friends/<str:username>/', views.UserFriendsView().as_view(), name='UserFriends'),
    path('blocked/', views.BlockedUserView().as_view(), name='blocked'),
    path('pending/', views.PendingUserView().as_view(), name='pending'),
    path('upload-avatar/', views.UserAvatarUpload().as_view(), name='upload')

]
