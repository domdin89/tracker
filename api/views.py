from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Project, Task
from django.db.models import Count, Sum
from django.contrib import messages
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime

@login_required
def projects_page(request):
    
    projects = Project.objects.all()
    
    total_tasks = Task.objects.filter(user=request.user).count()
    active_tasks = Task.objects.filter(user=request.user, is_active=True).count()
    
    current_date = timezone.now()
    start_of_week = current_date - timezone.timedelta(days=current_date.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_week = start_of_week + timezone.timedelta(days=7)
    
    weekly_tasks = Task.objects.filter(
        user=request.user,
        datetimeStart__gte=start_of_week,
        datetimeEnd__lte=end_of_week
    )
    
    weekly_hours = 0
    for task in weekly_tasks:
        duration = task.datetimeEnd - task.datetimeStart
        weekly_hours += duration.total_seconds() / 3600
    
    weekly_hours = round(weekly_hours, 1)
    
    context = {
        'projects': projects,
        'total_tasks': total_tasks,
        'active_tasks': active_tasks,
        'weekly_hours': weekly_hours
    }
    
    return render(request, 'projects.html', context)

@login_required
def project_create(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        if nome:
            Project.objects.create(nome=nome)
        return redirect('api:projects')
    
    return redirect('api:projects')



@login_required
def tasks_list(request):

    start_datetime = request.GET.get('datetimeStart')
    end_datetime = request.GET.get('datetimeEnd')
    
    if not start_datetime or not end_datetime:
        messages.error(request, 'È necessario specificare entrambi i parametri datetimeStart e datetimeEnd')
        return redirect('api:projects')
    
    try:
        start_datetime = parse_datetime(start_datetime)
        end_datetime = parse_datetime(end_datetime)
    except (ValueError, TypeError):
        messages.error(request, 'Formato datetime non valido. Utilizza il formato ISO 8601 (YYYY-MM-DDTHH:MM:SS)')
        return redirect('api:projects')
    
    tasks = Task.objects.filter(
        user=request.user,
        datetimeStart__gte=start_datetime,
        datetimeEnd__lte=end_datetime,
        is_active=True
    )
    
    projects = Project.objects.all()
    
    total_time = 0
    for task in tasks:
        duration = task.datetimeEnd - task.datetimeStart
        total_time += duration.total_seconds()
    
    total_hours = round(total_time / 3600, 2)
    
    context = {
        'tasks': tasks,
        'projects': projects,
        'total_hours': total_hours,
        'start_date': start_datetime,
        'end_date': end_datetime,
        'total_tasks': tasks.count(),
        'active_tasks': tasks.filter(is_active=True).count()
    }
    
    return render(request, 'tasks.html', context)


@login_required
def tasks_for_project(request, project_id):
    
    if not project_id:
        return JsonResponse({'error': 'Project ID is required'}, status=400)
    
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)
    
    tasks = Task.objects.filter(
        project=project,
        user=request.user
    ).order_by('-datetimeStart')
    
    tasks_data = []
    for task in tasks:
        duration = task.datetimeEnd - task.datetimeStart
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        duration_str = f"{hours}h {minutes}m"
        
        tasks_data.append({
            'id': task.id,
            'description': task.description,
            'datetimeStart': task.datetimeStart.isoformat(),
            'datetimeEnd': task.datetimeEnd.isoformat(),
            'duration': duration_str,
            'is_active': task.is_active,
            'project': project.id
        })
    
    return JsonResponse({
        'tasks': tasks_data,
        'project': {
            'id': project.id,
            'nome': project.nome
        }
    })

@login_required
def task_detail(request, task_id):
    
    try:
        task = Task.objects.get(id=task_id, user=request.user)
    except Task.DoesNotExist:
        messages.error(request, 'Task non trovato')
        return redirect('api:projects')
    
    project = task.project
    
    duration = task.datetimeEnd - task.datetimeStart
    hours = int(duration.total_seconds() // 3600)
    minutes = int((duration.total_seconds() % 3600) // 60)
    
    context = {
        'task': task,
        'project': project,
        'hours': hours,
        'minutes': minutes,
        'projects': Project.objects.all()  # Per la navigazione
    }
    
    return render(request, 'task_detail.html', context)

@login_required
def tasks_for_project(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)
    
    # Filter tasks by project and user
    tasks = Task.objects.filter(
        project=project,
        user=request.user
    ).order_by('-datetimeStart') 
    
    tasks_data = []
    for task in tasks:
        duration = task.datetimeEnd - task.datetimeStart
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        duration_str = f"{hours}h {minutes}m"
        
        tasks_data.append({
            'id': task.id,
            'description': task.description,
            'datetimeStart': task.datetimeStart.isoformat(),
            'datetimeEnd': task.datetimeEnd.isoformat(),
            'duration': duration_str,
            'is_active': task.is_active,
            'project': project.id
        })
    
    return JsonResponse({
        'tasks': tasks_data,
        'project': {
            'id': project.id,
            'nome': project.nome
        }
    })

@login_required
def task_create(request):
    if request.method != 'POST':
        return redirect('api:projects')
    
    project_id = request.POST.get('project')
    description = request.POST.get('description')
    datetime_start_str = request.POST.get('datetimeStart')
    datetime_end_str = request.POST.get('datetimeEnd')
    
    if not all([project_id, description, datetime_start_str, datetime_end_str]):
        messages.error(request, 'Tutti i campi sono obbligatori')
        return redirect('api:projects')
    
    # Ottieni il progetto
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        messages.error(request, 'Progetto non trovato')
        return redirect('api:projects')
    except ValueError:
        messages.error(request, 'ID progetto non valido')
        return redirect('api:projects')
    
    try:
        datetime_start = parse_datetime(datetime_start_str)
        datetime_end = parse_datetime(datetime_end_str)
        
        if datetime_start is None or datetime_end is None:
            raise ValueError("Parsing datetime ha prodotto None")
            
        if datetime_end <= datetime_start:
            messages.error(request, 'La data di fine deve essere successiva alla data di inizio')
            return redirect('api:projects')
    except Exception as e:
        messages.error(request, f'Formato datetime non valido: {str(e)}')
        return redirect('api:projects')
    
    # Crea il task
    Task.objects.create(
        project=project,
        user=request.user,
        description=description,
        datetimeStart=datetime_start,
        datetimeEnd=datetime_end,
        is_active=True
    )
    
    messages.success(request, 'Task creato con successo')
    return redirect('api:projects')

@login_required
def task_update(request, task_id):
    try:
        task = Task.objects.get(id=task_id, user=request.user)
    except Task.DoesNotExist:
        messages.error(request, 'Task non trovato')
        return redirect('api:projects')
    
    project_id = request.POST.get('project')
    description = request.POST.get('description')
    datetime_start_str = request.POST.get('datetimeStart')
    datetime_end_str = request.POST.get('datetimeEnd')
    is_active = request.POST.get('is_active') == 'on'
    
    if project_id:
        try:
            project = Project.objects.get(id=project_id)
            task.project = project
        except Project.DoesNotExist:
            messages.error(request, 'Progetto non trovato')
            return redirect('api:task_update', task_id=task_id)
        except ValueError:
            messages.error(request, 'ID progetto non valido')
            return redirect('api:task_update', task_id=task_id)
    
    if description:
        task.description = description
    
    if datetime_start_str:
        try:
            task.datetimeStart = parse_datetime(datetime_start_str)
            if task.datetimeStart is None:
                raise ValueError("Parsing datetime ha prodotto None")
        except Exception as e:
            messages.error(request, f'Formato start datetime non valido: {str(e)}')
            return redirect('api:task_update', task_id=task_id)
    
    if datetime_end_str:
        try:
            task.datetimeEnd = parse_datetime(datetime_end_str)
            if task.datetimeEnd is None:
                raise ValueError("Parsing datetime ha prodotto None")
        except Exception as e:
            messages.error(request, f'Formato end datetime non valido: {str(e)}')
            return redirect('api:task_update', task_id=task_id)
    
    if task.datetimeEnd <= task.datetimeStart:
        messages.error(request, 'La data di fine deve essere successiva alla data di inizio')
        return redirect('api:task_update', task_id=task_id)
    
    
    # Salva modifiche
    task.save()
    
    messages.success(request, 'Task aggiornato con successo')
    return redirect('api:projects')

@login_required
def task_delete(request, task_id):
    try:
        task = Task.objects.get(id=task_id, user=request.user)
    except Task.DoesNotExist:
        messages.error(request, 'Task non trovato')
        return redirect('api:projects')
    
    # Elimina il task
    task.is_active = False
    task.save()
    
    messages.success(request, f'Task eliminato con successo')
    return redirect('api:projects')

@login_required
def generate_report(request):
    
    start_date_str = request.GET.get('datetimeStart')
    end_date_str = request.GET.get('datetimeEnd')
    
    # Se non sono fornite date, usa ultimi 30 giorni
    if not start_date_str or not end_date_str:
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
    else:
        try:
            start_date = parse_datetime(start_date_str)
            end_date = parse_datetime(end_date_str)
        except (ValueError, TypeError):
            messages.error(request, 'Formato date non valido')
            return redirect('api:projects')
    
    # Filtra i task per l'intervallo di date
    tasks = Task.objects.filter(
        user=request.user,
        datetimeStart__gte=start_date,
        datetimeEnd__lte=end_date
    )
    
    # Calcola le ore per progetto
    project_hours = {}
    for task in tasks:
        project_id = str(task.project.id)
        if project_id not in project_hours:
            project_hours[project_id] = {
                'name': task.project.nome,
                'total_hours': 0,
                'tasks_count': 0
            }
        
        duration = task.datetimeEnd - task.datetimeStart
        project_hours[project_id]['total_hours'] += duration.total_seconds() / 3600
        project_hours[project_id]['tasks_count'] += 1
    
    # Arrotonda le ore
    for project_id in project_hours:
        project_hours[project_id]['total_hours'] = round(project_hours[project_id]['total_hours'], 2)
    
    context = {
        'projects': Project.objects.all(),
        'project_hours': list(project_hours.values()),
        'start_date': start_date,
        'end_date': end_date,
        'total_tasks': Task.objects.filter(user=request.user).count(),
        'active_tasks': Task.objects.filter(user=request.user, is_active=True).count()
    }
    
    return render(request, 'report.html', context)