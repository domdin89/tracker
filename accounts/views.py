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
        

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):

    try:
        # Estrai i dati dalla richiesta
        username = f"user_{secrets.token_hex(4)}"
        password = request.data.get('password')
        email = request.data.get('email')
        name = request.data.get('name')
        surname = request.data.get('surname')
        display_name = request.data.get('display_name')
        mobile_number = request.data.get('mobile_number', None)
        role = request.data.get('role', 'utente')

        
        if User.objects.filter(email=email).exists():
            return Response({
                'message': 'Email già registrata.'
            }, status=status.HTTP_400_BAD_REQUEST)

        
        # Usa la transazione per assicurarti che entrambe le operazioni abbiano successo
        with transaction.atomic():
            
            # Crea l'utente Django
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=name,
                last_name=surname
            )

            # Crea un nuovo profilo se non esiste già
            profile = Profile.objects.create(
                user=user,
                name=name,
                surname=surname,
                display_name=display_name,
                email=email,
                mobile_number=mobile_number,
                role=role,
                is_active=True
            )
            
            # Gestione dell'immagine del profilo
            if 'image' in request.FILES:
                profile.image = request.FILES['image']
                profile.save()
            
            return Response({
                'message': 'Registrazione completata con successo.',
                'user_id': user.id,
                'profile_id': profile.id
            }, status=status.HTTP_201_CREATED)
                
    except Exception as e:
        # Log dell'errore per debug
        print(f"Errore durante la registrazione: {str(e)}")
        return Response({
            'message': f'Si è verificato un errore durante la registrazione: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    