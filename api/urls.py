from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import *


app_name='api'


urlpatterns = [

    #PROJECTS

    path('projects', projects_page, name='projects'),
    path('projects', project_create, name='project_create'),


    # path('tasks', task, name='tasks'),
    # path('tasks/<str:id>', name=task),

    # path('tasks', task_create, name='task-create'),

    # path('tasks/<str:id>', task_edit, name='task-edit'),

    # path('tasks/<str:id>', task_delete, name='task-delete'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)