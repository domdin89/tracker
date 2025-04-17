 
from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
from .views import *


app_name = 'accounts'
urlpatterns = [
    path('login', Login.as_view()),
    path('register', register, name='register'),

     path('login-page/', login_page, name='login_page'),
    path('register-page/', register_page, name='register_page'),
    

    # path('register', views.register_user),
    # path('invite/<str:token>', views.redirect_to_register, name='invite_redirect'),

    # path('login/refresh', TokenRefreshView.as_view()),
    # path('user/detail', views.get_user_detail),

    # path('password-reset', views.password_reset_request),
    # path('password-reset-confirm', views.password_reset_confirm),


]