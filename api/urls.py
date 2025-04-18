from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import *

app_name='api'

urlpatterns = [
    # PROJECTS
    path('projects', projects_page, name='projects'),
    path('projects/new', project_create, name='project_create'),
    
    path('projects', projects_page, name='projects'),
    path('tasks', tasks_list, name='tasks'),
    path('tasks/project/<uuid:project_id>', tasks_for_project, name='tasks_for_project'),
    path('tasks/<uuid:task_id>', task_detail, name='task_detail'),
    path('tasks/create', task_create, name='task_create'),  # POST
    path('tasks/<uuid:task_id>/update', task_update, name='task_update'),  # PUT/PATCH
    path('tasks/<uuid:task_id>/delete', task_delete, name='task_delete'),  # DELETE
    
    # Endpoint opzionale
    path('report', generate_report, name='report'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)