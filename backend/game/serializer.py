
from rest_framework.serializers import Serializer 


from rest_framework import serializers

class SystemSocketSerializer(serializers.Serializer):
    type = serializers.CharField(max_length=50)
    identifier = serializers.CharField(max_length=50)

    def validate(self, attrs):
        if 'type' not in attrs or not attrs['type']:
            raise serializers.ValidationError("The 'type' field is required.")
        if 'identifier' not in attrs or not attrs['identifier']:
            raise serializers.ValidationError("The 'identifier' field is required.")
        
        return attrs
