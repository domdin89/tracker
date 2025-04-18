from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import *

app_name = 'api'

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('project/create/', create_project, name='create_project'),
    path('task/create/', create_task, name='create_task'),
    
    path('projects', project_list, name='project_list'),
    path('tasks', task_list, name='task_list'),
    path('tasks/<uuid:task_id>', task_detail, name='task_detail'),
    path('report', report, name='report'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)