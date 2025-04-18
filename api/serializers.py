from rest_framework import serializers
from .models import Project, Task
from django.contrib.auth.models import User

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'nome']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'project', 'user', 'description', 'datetimeStart', 'datetimeEnd', 'is_active']

    def validate(self, data):
        
        if data['datetimeStart'] >= data['datetimeEnd']:
            raise serializers.ValidationError("End time must be after start time")
        return data