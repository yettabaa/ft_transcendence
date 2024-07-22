from .design_patterns import ErrorBuilder
import requests, secrets
from rest_framework import status
from .models import Tokens, User
from django.utils import  timezone 
from .serializers import OAuthRegistratinSerialize
from rest_framework.response import Response
from rest_framework.views import APIView
import secrets
import requests
from .models import Tokens


def check_registration(email):
    # print(f'Data is {data}')
    # email = data['email']
    if not email:
        return None
    try:
        user = User.objects.get(email=email)
        return user
    except User.DoesNotExist:
        return None

def insert_user_in_db(users_data):
    serializer = OAuthRegistratinSerialize(data=users_data)

    if serializer.is_valid():
        user = serializer.save()
        return user
    else:
        print(f'Iam always not is_valid(): {serializer.is_valid()}')
        new_username = users_data['username']
        while User.objects.filter(username=new_username).exists():
            new_username += '1' 
        user = User.objects.create(
            username= new_username,
            email=users_data['email']
        )
        user.save()
        return user


# const  client_id =  '332139181442-g674c6sto33iahriiprdrvs35ne3ahom.apps.googleusercontent.com'
# const  client_secret=  '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'
# const  redirect_uri = 'http://localhost:5173/' //http://localhost:5173/
# const redirect_uri_en = 'http%3A%2F%2Flocalhost%3A5173%2F';


class GoogleOAuth:
    def __init__(self,code = None, state = None) -> None:
        self.code  = code
        self.client_id = '332139181442-g674c6sto33iahriiprdrvs35ne3ahom.apps.googleusercontent.com'
        self.client_secret = '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'
        self.scope = 'openid%20profile%20email'
        self.state =  state 
        self.redirect_uri = 'http://localhost:5173/'

    def GenLink(self):
        state = secrets.token_hex(12)
        token = Tokens.objects.create()
        token.token = str(state)
        token.type = 'google_Oauth'
        token.expired_date = token.date + timezone.timedelta(minutes=5)
        # print(f"gen_state is:-> {state}")
        token.save()
        return f'https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id={self.client_id}&scope={self.scope}&redirect_uri={self.redirect_uri}&state={state}'
     
    def getAccessToken(self) :
        if(self.code == None ) :
            raise Exception("")

        body = {
            'code': self.code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code',
            'state' : self.state 
        }
        
        response = requests.post('https://oauth2.googleapis.com/token', data=body)
        if response.status_code != 200:
            print(response.text)
            raise Exception('Error to Connect to Google Server')
        data = response.json()
        print(data)
        return data['access_token']
    

    def getUserData(self) :
        access_token = self.getAccessToken()
        if access_token == None : 
            raise Exception("ERROR : Can't Get Access Token")
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get('https://www.googleapis.com/oauth2/v3/userinfo', headers=headers)
        data = response.json()
        return data




CLIENT_ID_42 = 'u-s4t2ud-789ae11f20ba1b43a81ff49a1393e1f82bfd2a2c180d46f5d37b6af4d2be33af'
CLIENT_SECRET_42 = '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'
REDIRECT_URL = 'https://api.intra.42.fr/oauth/token'


class School_OAuth():
    def __init__(self, code = None, state = None):
        self.code  = code
        self.client_id = CLIENT_ID_42
        self.client_secret = CLIENT_SECRET_42
        self.scope = 'public'
        self.state =  state 
        self.redirect_uri = 'http://localhost:5173/signup/'

    def generate_link(self):
        state = secrets.token_hex(12)
        token = Tokens.objects.create()
        token.type = '42_Oauth'
        token.token = state
        token.save()
        return f'https://api.intra.42.fr/oauth/authorize?client_id=u-s4t2ud-789ae11f20ba1b43a81ff49a1393e1f82bfd2a2c180d46f5d37b6af4d2be33af&redirect_uri=http%3A%2F%2Flocalhost%3A5173%2Fsignup%2F&response_type=code&state={state}'
        # return f'https://api.intra.42.fr/oauth/authorize?client_id=u-s4t2ud-789ae11f20ba1b43a81ff49a1393e1f82bfd2a2c180d46f5d37b6af4d2be33af&redirect_uri=http%3A%2F%2Flocalhost%3A5173%2Fsignup&response_type=code&state={state}'

    def getStudentsData(self):
        access_token = self.get_access_token()
        if access_token == None:
            raise ValueError("{'Error': 'Invalid Access Token'}")
        api_42 = 'https://api.intra.42.fr/v2/me'
        headers = {
            'Authorization': f'Bearer {access_token}',
        }
        response_from_42 = requests.get(api_42, headers=headers)
        if response_from_42.status_code == 200:
            user_data = response_from_42.json()
            return user_data
        else:
            return response_from_42.text

    def get_access_token(self):
        if self.code:
            data = {
                'grant_type': 'authorization_code',
                'client_id': CLIENT_ID_42,
                'client_secret': CLIENT_SECRET_42,
                'code': self.code,
                'state': self.state,
                'redirect_uri': 'http://localhost:5173/signup/',
            }

            response = requests.post(REDIRECT_URL, data=data)
            if response.status_code == 200:
                user_data = response.json()
                token = user_data['access_token']
                return token
            else:
                print('Error from : response.status_code != 200')
        else:
            print('Error from : self.code')

