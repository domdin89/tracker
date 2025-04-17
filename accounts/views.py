import secrets
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.contrib.auth import authenticate
from django.http import HttpResponse
from django.conf import settings
from django.db import transaction

from accounts.serializers import CustomTokenObtainPairSerializer, ProfileSerializer, UserSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404, render
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from rest_framework.response import Response
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from accounts.serializers import CustomTokenObtainPairSerializer
from django.contrib.auth import logout
from django.views import View
from django.contrib import messages
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta
from .models import Profile
from django.db import transaction
from .models import Profile
from django.core.validators import validate_email
from django.core.exceptions import ValidationError



def login_page(request):
    return render(request, 'auth/login.html')


def register_page(request):
    return render(request, 'auth/register.html')

class Login(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            email = request.POST.get('email')
            password = request.POST.get('password')
            user = User.objects.get(email=email)

            print('user', user)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, 'Utente non trovato')
                return render(request, 'auth/login.html')


        if user and user.is_active:
            if password:
                # Verifica la password
                authenticated_user = authenticate(email=email, password=password)
                if authenticated_user:
                    # Esegui il login dell'utente
                    login(request, authenticated_user)
                    # Reindirizza alla pagina 'fattura:home'
                    return redirect('shortener:dashboard')
                
                else:
                    messages.error(request, 'Password non valida.')
                    return render(request, 'auth/login.html')
            else:
                messages.error(request, 'La password non è stata fornita.')
                return render(request, 'auth/login.html')
        elif user and not user.is_active:
            messages.error(request, 'Utente non attivato.')
            return render(request, 'auth/login.html')
        

@transaction.atomic
def register(request):
    if request.method == 'POST':
        # Ottieni i dati dal form con strip() per rimuovere spazi
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        
        if not all([username, email, password1, password2]):
            messages.error(request, 'Tutti i campi contrassegnati sono obbligatori.')
            return render(request, 'auth/register.html')
        
        # Validazione dell'email
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Inserisci un indirizzo email valido.')
            return render(request, 'auth/register.html')
            
        # Controllo se l'email è già in uso
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Questa email è già registrata.')
            return render(request, 'auth/register.html')
            
        # Controllo se lo username è già in uso
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Questo username è già in uso.')
            return render(request, 'auth/register.html')
        
        # Validazione password
        if password1 != password2:
            messages.error(request, 'Le password non coincidono.')
            return render(request, 'auth/register.html')
            
        if len(password1) < 8:
            messages.error(request, 'La password deve contenere almeno 8 caratteri.')
            return render(request, 'auth/register.html')
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
            )
            
            # Crea il profilo associato
            profile = Profile.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                is_active=True
            )

            messages.success(request, 'Registrazione avvenuta con successo')
            return render(request, 'auth/register_success.html')
                
        except IntegrityError as e:
            transaction.set_rollback(True)
            messages.error(request, 'Si è verificato un errore con i dati inseriti. Riprova.')
            return render(request, 'auth/register.html')
        except Exception as e:
            transaction.set_rollback(True)
            messages.error(request, f'Si è verificato un errore durante la registrazione. Riprova più tardi.')
            # Log dell'errore per il debug
            print(f'Error during registration: {str(e)}')
            return render(request, 'auth/register.html')
            
    return render(request, 'auth/register.html')