from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Project, Task
from django.db.models import Count, Sum, F, ExpressionWrapper, DurationField
from django.db.models.functions import ExtractHour
from django.contrib import messages

@login_required
def projects_page(request):
    projects = Project.objects.all()
    
    # Recupera alcune statistiche per la dashboard
    total_tasks = Task.objects.filter(user=request.user).count()
    active_tasks = Task.objects.filter(user=request.user, is_active=True).count()
    
    # Calculate weekly hours (tasks from the current week)
    current_date = timezone.now()
    start_of_week = current_date - timezone.timedelta(days=current_date.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_week = start_of_week + timezone.timedelta(days=7)
    
    # Calculate duration using F expressions
    weekly_tasks = Task.objects.filter(
        user=request.user,
        datetimeStart__gte=start_of_week,
        datetimeEnd__lte=end_of_week
    )
    
    # Calculate total hours from all weekly tasks
    weekly_hours = 0
    for task in weekly_tasks:
        duration = task.datetimeEnd - task.datetimeStart
        weekly_hours += duration.total_seconds() / 3600  # Convert to hours
    
    weekly_hours = round(weekly_hours, 1)  # Round to 1 decimal place
    
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

    """Genera un report aggregato dei task per progetto"""
    # Ottieni i parametri dalla query
    start_date_str = request.GET.get('datetimeStart')
    end_date_str = request.GET.get('datetimeEnd')
    
    # Se non sono fornite date, usa ultimi 30 giorni
    if not start_date_str or not end_date_str:
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
    else:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
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
        'start_date': start_date.strftime('%Y-%m-%dT%H:%M'),
        'end_date': end_date.strftime('%Y-%m-%dT%H:%M'),
        'total_tasks': Task.objects.filter(user=request.user).count(),
        'active_tasks': Task.objects.filter(user=request.user, is_active=True).count()
    }
    
    return render(request, 'projects.html', context)
    """Visualizza il report dei task raggruppati per progetto"""
    # Ottieni i parametri dalla query
    start_date_str = request.GET.get('datetimeStart')
    end_date_str = request.GET.get('datetimeEnd')
    
    # Se non sono fornite date, usa ultimi 30 giorni
    if not start_date_str or not end_date_str:
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
    else:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            messages.error(request, 'Formato date non valido')
            return redirect('api:projects')
    
    # Filtra i task per l'intervallo di date
    tasks = Task.objects.filter(
        user=request.user,
        datetimeStart__gte=start_date,
        datetimeEnd__lte=end_date
    )
    
    # Raggruppa i task per progetto
    projects_data = {}
    for task in tasks:
        project_id = str(task.project.id)
        project_name = task.project.nome
        
        if project_id not in projects_data:
            projects_data[project_id] = {
                'name': project_name,
                'total_seconds': 0,
                'total_hours': 0,
                'tasks_count': 0
            }
        
        duration = task.datetimeEnd - task.datetimeStart
        projects_data[project_id]['total_seconds'] += duration.total_seconds()
        projects_data[project_id]['tasks_count'] += 1
    
    # Converti i secondi in ore
    for project_id, data in projects_data.items():
        data['total_hours'] = round(data['total_seconds'] / 3600, 2)
    
    context = {
        'projects_data': projects_data.values(),
        'start_date': start_date,
        'end_date': end_date
    }
    
    return render(request, 'projects.html', context)