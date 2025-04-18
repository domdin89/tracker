from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import authenticate, login
from accounts.serializers import CustomTokenObtainPairSerializer
from .models import Profile
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import logout
from django.views import View



def login_page(request):
    return render(request, 'auth/login.html')

def register_page(request):
    return render(request, 'auth/register.html')


class Login(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = User.objects.get(username=username)

        except User.DoesNotExist:
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                messages.error(request, 'User not found')
                return render(request, 'auth/login.html')


        if user and user.is_active:
            if password:
                # Verifica la password
                authenticated_user = authenticate(username=username, password=password)
                if authenticated_user:
                    # Esegui il login dell'utente
                    login(request, authenticated_user)
                    # Reindirizza alla pagina 'fattura:home'
                    return redirect('api:dashboard')
                
                else:
                    messages.error(request, 'Password incorrect.')
                    return render(request, 'auth/login.html')
            else:
                messages.error(request, 'Please, insert the password.')
                return render(request, 'auth/login.html')
        elif user and not user.is_active:
            messages.error(request, 'User not active.')
            return render(request, 'auth/login.html')
        
        
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        
        if not all([username, email, password1, password2]):
            messages.error(request, 'All required fields must be filled.')
            return render(request, 'auth/register.html')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'auth/register.html')
        
        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'auth/register.html')
        
        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'auth/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'auth/register.html')
        
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password1,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True
                )
                
                profile = Profile.objects.create(
                    user=user,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True
                )
                
                messages.success(request, 'Registration successful! You can now log in.')
                return redirect('accounts:login')
                
        except Exception as e:
            messages.error(request, f'Error during registration: {str(e)}')
            return render(request, 'auth/register.html')
    
    # GET request: show registration form
    return render(request, 'auth/register.html')



class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('accounts:login_page')