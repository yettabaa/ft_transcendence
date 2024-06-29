from django.db import models

# Create your models here.
class ReadyToPlay(models.Model):
    username = models.CharField(max_length=100, unique=True, error_messages={
            'unique': 'A user with that username already exists',})
    def __str__(self) -> str:
        return self.username
