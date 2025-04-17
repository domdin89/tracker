import uuid
from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=255)

    def __str__(self):
        return self.nome


class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, related_name='tasks', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='tasks', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    description = models.TextField()
    datetimeStart = models.DateTimeField()
    datetimeEnd = models.DateTimeField()

    def __str__(self):
        return f"{self.description} ({self.project.nome})"