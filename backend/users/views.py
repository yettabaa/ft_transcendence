from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import authenticate, login
from rest_framework import status
from rest_framework.views import APIView 
# from rest_framework.reverse import reverse
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from .Serializers import Serializers, LoginSerializer

class SignUp(APIView):
    def post(self, request):
        serializers = Serializers(data=request.data)
        if serializers.is_valid():
            serializers.save()
            return Response(serializers.data, status=201)
        return Response(serializers.errors, status=400)
    
class LogIn(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                token, created = Token.objects.get_or_create(user=user)
                return Response({'token': token.key}, status=status.HTTP_200_OK)
            print('zab')
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
