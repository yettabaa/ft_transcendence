from .models import ReadyToPlay
from rest_framework import serializers

class Serializers(serializers.ModelSerializer):
    class Meta:
        model = ReadyToPlay
        fields = '__all__'