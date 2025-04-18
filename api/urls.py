from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import *

app_name='api'

urlpatterns = [
    # PROJECTS
    path('projects', projects_page, name='projects'),
    path('projects/new', project_create, name='project_create'),
    

  
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)