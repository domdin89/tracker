import hashlib
from django.http import HttpResponseRedirect
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
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.urls import reverse


def generate_confirmation_token(user):
    """
    Genera un token di conferma per l'utente specificato.
    
    Args:
        user (User): L'oggetto utente per cui viene generato il token.
    
    Returns:
        tuple: Una tupla contenente l'ID dell'utente codificato in base64 e il token di conferma.
    """
    # Codifica l'ID dell'utente in formato base64
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Genera un token di conferma usando il token generator predefinito di Django
    token = default_token_generator.make_token(user)
    
    return uid, token

def create_short_url(original_url):
    """
    Crea un URL abbreviato per l'URL originale specificato.
    """
    try:
        # Create a temporary instance to normalize the URL
        temp_short_url = ShortURL(original_url=original_url)
        normalized_url = temp_short_url.normalize_url(original_url)

        # Controlla se l'URL abbreviato esiste già
        url_hash = hashlib.sha256(normalized_url.encode()).hexdigest()
        existing_url = ShortURL.objects.filter(url_hash=url_hash).first()

        if existing_url:
            return f"{settings.SITE_URL}/{existing_url.short_code}"

        # Crea un nuovo URL abbreviato
        short_url = ShortURL.objects.create(
            profile=None,  # Puoi lasciare il profilo vuoto o associarlo a un profilo generico
            original_url=normalized_url,
            is_qr_url=False  # Non è un QR Code
        )

        return f"{settings.SITE_URL}/{short_url.short_code}"
    except Exception as e:
        # Log the error
        print(f"Error creating short URL: {str(e)}")
        print('origina ulr', original_url)
        # Return the original URL as fallback
        return original_url

def generate_confirmation_link(user):
    """
    Genera un URL abbreviato sicuro per la conferma email.
    
    Args:
        user: L'oggetto User per cui generare il link di conferma
    
    Returns:
        str: L'URL abbreviato per la conferma email
    """
    from subscription.models import SubscriptionPlan
    # Genera il token di conferma standard
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    
    # Ottieni il piano gratuito per usarlo come default
    free_plan = SubscriptionPlan.objects.get(id=1)  # Assumiamo che il piano ID 1 sia il piano gratuito
    
    # Crea un nuovo ShortURL specifico per la conferma email
    short_url = ShortURL(
        profile=None,  # Non associamo ancora a un profilo
        original_url=f"{settings.SITE_URL}/confirm-email/{uid}/{token}/",
        expires_at=timezone.now() + timedelta(days=1),  # Scade dopo 24 ore
        is_qr_url=False,
        is_custom=False
    )
    
    # Bypass della validazione standard
    short_url._free_plan = free_plan  # Aggiungiamo un attributo temporaneo per il salvataggio
    short_url.save(bypass_subscription_check=True)
    
    # Aggiungi metadati per identificare questo come un URL di conferma email
    short_url.utm_parameters = {
        'type': 'email_confirmation',
        'user_id': user.id,
        'created_at': timezone.now().isoformat()
    }
    short_url.save()
    
    return f"{settings.SITE_URL}/{short_url.short_code}"

def verify_confirmation_link(short_code):
    """
    Verifica che l'URL abbreviato sia valido per la conferma email.
    
    Args:
        short_code: Il codice dell'URL abbreviato
    
    Returns:
        tuple: (uid, token) se valido, (None, None) altrimenti
    """
    try:
        short_url = ShortURL.objects.get(short_code=short_code)
        
        # Verifica che sia un URL di conferma email
        if not short_url.utm_parameters or short_url.utm_parameters.get('type') != 'email_confirmation':
            return None, None
            
        # Verifica la scadenza
        if timezone.now() > short_url.expires_at:
            return None, None
            
        # Estrai uid e token dall'URL originale
        parts = short_url.original_url.split('/')
        if len(parts) >= 7:  # Verifica che l'URL abbia il formato corretto
            uid = parts[-3]
            token = parts[-2]
            return uid, token
            
        return None, None
        
    except ShortURL.DoesNotExist:
        return None, None

def cleanup_expired_confirmation_links():
    """
    Rimuove i link di conferma email scaduti dal database.
    """
    ShortURL.objects.filter(
        utm_parameters__type='email_confirmation',
        expires_at__lt=timezone.now()
    ).delete()

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
                messages.error(request, 'Utente non trovato')
                return render(request, 'auth/login.html')


        if user and user.is_active:
            if password:
                # Verifica la password
                authenticated_user = authenticate(username=username, password=password)
                if authenticated_user:
                    # Esegui il login dell'utente
                    login(request, authenticated_user)
                    # Reindirizza alla pagina 'fattura:home'
                    return redirect('api:projects')
                
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
        
        # Validazione dei campi obbligatori
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
            # Creazione dell'utente all'interno di una transazione
            # Crea l'utente
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                is_active=True
            )
            
            # Crea il profilo associato
            profile = Profile.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                is_active=True
            )
            
                
            messages.success(request, 'Registration successful! Please check your email to activate your account.')
            return render(request, 'auth/login.html')
                
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

def confirm_email(request, uidb64, token):
    """
    Vista per gestire la conferma dell'email.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()

        profile = Profile.objects.get(user=user)
        profile.is_active = True
        profile.save()

        messages.success(request, 'Il tuo account è stato attivato con successo!')
        return render(request, 'auth/confirmation_success.html')
    else:
        messages.error(request, 'Il link di conferma è invalido o scaduto.')
        return redirect('accounts:register_page')
    
class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('accounts:login_page')


def recover_password(request):
    return render(request, 'confirm-password.html')


def password_reset_success(request):
    return render(request, 'reset-password-success.html')


def password_reset_request(request):
    email = request.data.get('email')
    profile = get_object_or_404(Profile, email=email)

    if profile:
        token = default_token_generator.make_token(profile.user)
        uid = urlsafe_base64_encode(force_bytes(profile.pk))

        #reset_link = f'https://theranker.s1.theranker.it/recover-password?uid={uid}&token={token}'
        reset_link = f'http://127.0.0.1:8000/recover-password?uid={uid}&token={token}'




        return Response({
                        'message': 'Password reset link has been sent to your email.',
                        'uid': uid,
                        'token': token,
                        }, )
    else:
        return Response({
                        'message': 'Attenzione, email inserita non valida',
                        }, )