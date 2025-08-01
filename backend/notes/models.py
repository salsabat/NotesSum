from django.db import models
from django.contrib.auth.models import User

class Tab(models.Model):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default="#007bff")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

class Unit(models.Model):
    tab = models.ForeignKey(Tab, on_delete=models.CASCADE, related_name='units')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        unique_together = ['tab', 'name']

    def __str__(self):
        return f"{self.name} ({self.tab.name})"

class Note(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='notes', null=True, blank=True)
    tab = models.ForeignKey(Tab, on_delete=models.CASCADE, related_name='notes', null=True, blank=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    summary = models.TextField(blank=True, null=True)
    file = models.CharField(max_length=255, blank=True, null=True)
    extraction_method = models.CharField(max_length=50, default='OCR')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='questions')
    question = models.TextField()
    answer = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
