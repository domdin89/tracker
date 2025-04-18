# Applicazione Time Tracker

Un'applicazione basata su Django per il tracciamento del tempo dedicato a progetti e attività.

## Funzionalità

- Gestione dei progetti
- Tracciamento delle attività con orari di inizio e fine
- Autenticazione utenti
- Report del tempo per progetto
- Filtraggio delle attività per intervallo di date

## Esecuzione con Docker

### Prerequisiti

- Docker e Docker Compose installati sul sistema

### Configurazione ed Esecuzione

1. Clona questo repository:
   ```bash
   git clone <url-repository>
   cd time-tracker
   ```

2. Crea un file di environment:
   ```bash
   cp .env.template .env
   ```

3. Modifica il file `.env` con le tue impostazioni preferite.

4. Costruisci e avvia i container Docker:
   ```bash
   docker-compose up --build
   ```

5. Accedi all'applicazione:
   - Interfaccia Web: http://localhost:8000
   - Interfaccia Admin: http://localhost:8000/admin

### Sviluppo vs Produzione

- Per lo sviluppo:
  - Imposta `DEBUG=True` nel file `.env`
  - L'applicazione sarà servita dal server di sviluppo di Django

- Per la produzione:
  - Imposta `DEBUG=False` nel file `.env`
  - Cambia `SECRET_KEY` con una stringa casuale sicura
  - L'applicazione sarà servita da Gunicorn dietro Nginx

## Endpoint API

- `GET /projects` - Elenco di tutti i progetti
- `GET /tasks` - Elenco delle attività con filtro per data
- `POST /tasks` - Creazione di una nuova attività
- `GET /tasks/{id}` - Dettagli di un'attività specifica
- `PUT/PATCH /tasks/{id}` - Aggiornamento di un'attività
- `DELETE /tasks/{id}` - Eliminazione di un'attività
- `GET /report` - Generazione di un report del tempo per progetto

## Migrazioni del Database

Quando l'applicazione è in esecuzione con Docker, le migrazioni vengono applicate automaticamente all'avvio.

Se hai bisogno di eseguire migrazioni manualmente:

```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

## Creazione di un Superuser

Per creare un utente amministratore:

```bash
docker-compose exec web python manage.py createsuperuser
```

In alternativa, puoi impostare le variabili d'ambiente `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD` e `DJANGO_SUPERUSER_EMAIL` nel file `.env`, e un superuser verrà creato automaticamente all'avvio.

## Arresto dell'Applicazione

```bash
docker-compose down
```

Per rimuovere anche i volumi (dati del database):

```bash
docker-compose down -v
```

## Struttura dei File Docker

- `docker-compose.yml` - Configurazione principale per lo sviluppo
- `docker-compose.prod.yml` - Configurazione specifica per la produzione
- `Dockerfile` - Istruzioni per la costruzione del container Django
- `start-server.sh` - Script di avvio per il container Django
- `nginx/default.conf` - Configurazione Nginx per servire l'applicazione
- `.env.template` - Template per le variabili d'ambiente
- `create_directories.sh` - Script di supporto per creare le directory richieste

## Utilizzo in Produzione

Per eseguire l'applicazione in modalità produzione:

```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

Assicurati di configurare correttamente le variabili d'ambiente per la produzione, in particolare:
- `DEBUG=False`
- Una `SECRET_KEY` sicura
- I parametri del database
- L'URL predefinito corretto