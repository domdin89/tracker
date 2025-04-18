from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime
import json
import uuid
from .models import Project, Task
from django.contrib.auth.models import User

@login_required
def dashboard(request):
    projects = Project.objects.all()
    context = {
        'projects': projects,
    }
    return render(request, 'projects.html', context)

@login_required
def project_list(request):
    if request.method == 'GET':
        projects = Project.objects.all()
        projects_data = [{'id': str(project.id), 'nome': project.nome} for project in projects]
        return JsonResponse(projects_data, safe=False)
    return HttpResponseBadRequest("Method not allowed")

@login_required
def task_list(request):
    if request.method == 'GET':
        start_date = request.GET.get('datetimeStart')
        end_date = request.GET.get('datetimeEnd')
        
        if not start_date or not end_date:
            return HttpResponseBadRequest("datetimeStart and datetimeEnd parameters are required")
        
        tasks = Task.objects.filter(
            user=request.user,
            datetimeStart__gte=start_date,
            datetimeEnd__lte=end_date
        )
        
        tasks_data = [{
            'id': str(task.id),
            'project': str(task.project.id),
            'user': str(task.user.id),
            'description': task.description,
            'datetimeStart': task.datetimeStart.isoformat(),
            'datetimeEnd': task.datetimeEnd.isoformat()
        } for task in tasks]
        
        return JsonResponse(tasks_data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            required_fields = ['project', 'description', 'datetimeStart', 'datetimeEnd']
            for field in required_fields:
                if field not in data:
                    return HttpResponseBadRequest(f"Field '{field}' is required")
            
            try:
                project = Project.objects.get(id=data['project'])
            except Project.DoesNotExist:
                return HttpResponseBadRequest("Project not found")
            
            task = Task.objects.create(
                project=project,
                user=request.user,
                description=data['description'],
                datetimeStart=data['datetimeStart'],
                datetimeEnd=data['datetimeEnd'],
                is_active=True
            )
            
            response_data = {
                'id': str(task.id),
                'project': str(task.project.id),
                'user': str(task.user.id),
                'description': task.description,
                'datetimeStart': task.datetimeStart.isoformat(),
                'datetimeEnd': task.datetimeEnd.isoformat()
            }
            
            return JsonResponse(response_data, status=201)
        
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON")
        except Exception as e:
            return HttpResponseBadRequest(str(e))
    
    return HttpResponseBadRequest("Method not allowed")

@login_required
def task_detail(request, task_id):
    try:
        task = get_object_or_404(Task, id=task_id, user=request.user)
    except ValueError:
        return HttpResponseBadRequest("Invalid task ID format")
    
    if request.method == 'GET':
        task_data = {
            'id': str(task.id),
            'project': str(task.project.id),
            'user': str(task.user.id),
            'description': task.description,
            'datetimeStart': task.datetimeStart.isoformat(),
            'datetimeEnd': task.datetimeEnd.isoformat()
        }
        return JsonResponse(task_data)
    
    elif request.method == 'PUT' or request.method == 'PATCH':
        try:
            data = json.loads(request.body)
            
            if request.method == 'PUT':
                required_fields = ['project', 'description', 'datetimeStart', 'datetimeEnd']
                for field in required_fields:
                    if field not in data:
                        return HttpResponseBadRequest(f"Field '{field}' is required for PUT")
            
            if 'project' in data:
                try:
                    task.project = Project.objects.get(id=data['project'])
                except Project.DoesNotExist:
                    return HttpResponseBadRequest("Project not found")
            
            if 'description' in data:
                task.description = data['description']
            if 'datetimeStart' in data:
                task.datetimeStart = data['datetimeStart']
            if 'datetimeEnd' in data:
                task.datetimeEnd = data['datetimeEnd']
            
            task.save()
            
            task_data = {
                'id': str(task.id),
                'project': str(task.project.id),
                'user': str(task.user.id),
                'description': task.description,
                'datetimeStart': task.datetimeStart.isoformat(),
                'datetimeEnd': task.datetimeEnd.isoformat()
            }
            
            return JsonResponse(task_data)
        
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON")
        except Exception as e:
            return HttpResponseBadRequest(str(e))
    
    elif request.method == 'DELETE':
        task.delete()
        return JsonResponse({}, status=204)
    
    return HttpResponseBadRequest("Method not allowed")

@login_required
def report(request):
    """GET /report - Report the time spent on each project"""
    if request.method == 'GET':
        start_date = request.GET.get('datetimeStart')
        end_date = request.GET.get('datetimeEnd')
        
        if not start_date or not end_date:
            return HttpResponseBadRequest("datetimeStart and datetimeEnd parameters are required")
        
        projects = Project.objects.all()
        report_data = []
        
        for project in projects:
            tasks = Task.objects.filter(
                project=project,
                user=request.user,
                datetimeStart__gte=start_date,
                datetimeEnd__lte=end_date
            )
            
            total_seconds = 0
            for task in tasks:
                start = task.datetimeStart
                end = task.datetimeEnd
                duration = (end - start).total_seconds()
                total_seconds += duration
            
            report_data.append({
                'project': str(project.id),
                'project_name': project.nome,
                'total': total_seconds,
                'total_hours': round(total_seconds / 3600, 2)
            })
        
        return JsonResponse(report_data, safe=False)
    
    return HttpResponseBadRequest("Method not allowed")

@login_required
def create_project(request):
    if request.method == 'POST':
        name = request.POST.get('nome')
        if name:
            Project.objects.create(nome=name)
        return redirect('api:dashboard')
    return HttpResponseBadRequest("Method not allowed")

@login_required
def create_task(request):
    if request.method == 'POST':
        project_id = request.POST.get('project')
        description = request.POST.get('description')
        datetime_start = request.POST.get('datetimeStart')
        datetime_end = request.POST.get('datetimeEnd')
        
        try:
            project = Project.objects.get(id=project_id)
            Task.objects.create(
                project=project,
                user=request.user,
                description=description,
                datetimeStart=datetime_start,
                datetimeEnd=datetime_end,
                is_active=True
            )
        except Exception as e:
            print(f"Error creating task: {e}")
        
        return redirect('api:dashboard')
    return HttpResponseBadRequest("Method not allowed")