from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Project, Task
from django.db.models import Count

@login_required
def projects_page(request):
    projects = Project.objects.all()
    
    # Recupera alcune statistiche per la dashboard
    total_tasks = Task.objects.filter(user=request.user).count()
    active_tasks = Task.objects.filter(user=request.user, is_active=True).count()
    
    context = {
        'projects': projects,
        'total_tasks': total_tasks,
        'active_tasks': active_tasks,
        'weekly_hours': 0
    }
    
    return render(request, 'projects.html', context)

@login_required
def project_create(request):
    print('sono qui')
    if request.method == 'POST':
        print('entro nella post')
        nome = request.POST.get('nome')
        if nome:
            Project.objects.create(nome=nome)
        return redirect('api:projects')
    
    return redirect('api:projects')