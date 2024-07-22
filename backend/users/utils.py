import secrets
from rest_framework_simplejwt.tokens import RefreshToken
from .models import * 
from django.db.models import Q 

def generate_token_user(user):
    random_token = secrets.token_hex(12)
    record = Tokens.objects.create()
    record.user_id = user
    record.token = random_token
    record.save()
    return record

def generate_jwt(user):
    try: 
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    except Exception as e:
        print(f'Error in JWT : {str(e)}')
        return None
    
from rest_framework.decorators import api_view, permission_classes
# from rest_framework_simplejwt.tokens import algorithms
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .design_patterns import ErrorBuilder, Message_Builder
# from rest_framework_simplejwt import jwt
from rest_framework import status
from src import settings
import jwt

from rest_framework.views import APIView


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token is None:
            error = ErrorBuilder().set_type('RefreshToken').set_message('Invalid Refresh Token').build()
            return Response(error, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            error = Message_Builder().set_message('Expired Refresh Token, Login in again').set_redirection('/login').build()
            return Response(error, status=status.HTTP_200_OK)
        
        user = User.objects.filter(id=payload.get('user_id')).first()
        if user is None:
            error = ErrorBuilder().set_type('User').set_message('Invalid User').build()
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        access_token = generate_jwt(user)
        print(f"After-ExpirationToken: {access_token['refresh']}")
        return Response({'access_token': access_token['access']}, status=status.HTTP_200_OK)

    

import requests 
from  PIL import Image 
from io import BytesIO
from django.core.files.base import ContentFile 
from .models import User 

# def get_extern_image(user=None, url=None ) -> bool: 
#         try:
#             response = requests.get(url)
#             if response.status_code == 200:
#                 image_bytes = BytesIO(response.content)
#                 image = Image.open(image_bytes)
#                 resized_image = image.resize((250, 250))
#                 output_buffer = BytesIO()
#                 resized_image.save(output_buffer, format="PNG")
#                 user.avatar_link.save(f'{user.id}.png', ContentFile(output_buffer.read()), save=True)
#             return True 
#         except Exception as e:
#             print(f'Fail Get image from {url} for {user.username}')# just for debugging will be replaced with return false  
#         return False

def get_extern_image(user=None, url=None) -> bool: 
    try:
        response = requests.get(url)
        if response.status_code == 200:
            image_bytes = BytesIO(response.content)
            image = Image.open(image_bytes)
            resized_image = image.resize((250, 250))
            out_buffer = BytesIO()
            resized_image.save(out_buffer, format="PNG")
            out_buffer.seek(0)
            user.avatar_link.save(f'{user.id}.png', ContentFile(out_buffer.read()), save=True)
            return True 
    except Exception as e:
        print(f'Fail Get image from {url} for {user.username}: Exception {e}')  # Log the error
    return False


def check_redirection(request):
    redirection = request.data['refer']
    if not redirection :
        location = '/home'
    else:
        location = redirection
    return location

def  xp_to_level(xp) : 
        for i in range(0, 100):
            value = 2 * (i * i) + (2 * i) + 15;  
            if(value > xp):
                return i;
        return 100;

def get_level(user):
        wins = user.wins
        losses = user.losses
        total = user.total_matches
        draw = total - (wins + losses)
        level  = draw * 0.05 + wins * 0.08
        progress = level - int(level)
        level = int(level)

        level_model = Level.objects.filter(level_no=level).first()
        return  {
                "name"     : level_model.name,
                "image"    : level_model.image,
                "current"  : level,
                "progress" : progress
    }
  


def get_relation(user1:User ,user2: User):

    if user1 == user2:
        return UserRelation.YOU
    records = Blocked_Friend.objects.filter(Q(blocker=user1) | Q(blocked=user1))
    for item in  records:
            if item.blocked == user2 or item.blocker == user2: 
                if item.blocked == user1: 
                    return UserRelation.BLOCKED
                else:
                    return UserRelation.BLOCKER
    records = Invitation.objects.filter(Q(sender=user1) | Q(receiver=user1))
    for item in  records:
            if item.sender == user2 or item.receiver == user2: 
                if item.sender == user1: 
                    return UserRelation.SEND_REQUEST
                else:
                    return UserRelation.REC_REQ
    records = Friend.objects.filter(Q(user1=user1) | Q(user2=user1))
    for item in  records:
            if (item.user1 == user1 and item.user2 == user2) or (item.user1 == user2 and item.user2 == user1): 
                return  UserRelation.FRIEND
    return UserRelation.NONE 


class UserRelation:
    NONE           = 'none'
    FRIEND         = 'friend'
    SEND_REQUEST   = 'send_req'
    REC_REQ        = 'rec_req'
    BLOCKER        = "blocker"
    BLOCKED        = "blocked" 
    YOU            = "you"
     
    