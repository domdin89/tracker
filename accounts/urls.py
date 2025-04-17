 
from django.urls import path
from . import views
from .views import *


app_name = 'accounts'
urlpatterns = [
    path('login', Login.as_view(), name='login'),
    path('register', register, name='register'),

    path('login-page/', login_page, name='login_page'),
    path('register-page/', register_page, name='register_page'),

]