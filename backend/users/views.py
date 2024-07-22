from django.shortcuts import render
from src.logger import log  
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.views import  APIView
from rest_framework.response import  Response
from django.contrib.auth import login, logout
from django.template.loader import render_to_string 
from .serializers import RegistrationSerializer, OAuthRegistrationSerializer
from .backends import CustomAuthenticationBackend
# from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Auth, Level, Tokens
from .design_patterns import ErrorBuilder , OAuthBuilder, TwoFA_Builder, Message_Builder
from .tfa_utils import send_otp, check_otp_is_enabled 
from django.conf import settings
from django.core.mail import send_mail
import secrets
from rest_framework.exceptions import ValidationError
from .utils import generate_token_user, generate_jwt, check_redirection , get_relation, UserRelation ,  get_level 
from rest_framework.permissions import IsAuthenticated
from .validators import validate_request_data_register ,\
    validate_request_data_login, validate_request_data_2fa,\
    validate_request_data_forget_pwd, validate_request_data_upgrade_pwd, \
    validate_request_data_oauth_register

# OAuth Google Added 
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from src.errors import *    
from .oauth2 import GoogleOAuth , insert_user_in_db, check_registration ,School_OAuth
from django.db.models import Q 
# Create your views here.
class CustomAPIView(APIView):
    def get(self, request, format=None):
        api_endpoints = {
            #? Add other endpoints here as needed
            'register': reverse('users:register', request=self.request),
            'login': reverse('users:login', request=self.request),
            'refresh-token': reverse('users:refresh', request=self.request),
            'generate-googlelink': reverse('users:googlelink', request=self.request),
            'generate-42link': reverse('users:42_Link', request=self.request),
            'tfa': reverse('users:2FA_check', request=self.request),
            'forget-password': reverse('users:forget-password', request=self.request),
            'update-password': reverse('users:reset-passowrd', request=self.request),
            'oauth-register': reverse('users:OAuth_Register', request=self.request),
        }
        return Response(api_endpoints, status=status.HTTP_200_OK)

from .utils import get_extern_image 
class RegistrationView(APIView):

    def normal_registration_type(self, request):
        serializer = RegistrationSerializer(data=request.data['data'])
        try:
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                message = Message_Builder().set_message('Your account has been created successfully').set_redirection('/login').build()
                return Response(message, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            error_message = e.detail
            errors = {}
            for field, field_errors in error_message.items():
                errors[field] = field_errors[0]
            errors = ErrorBuilder().set_type('').set_message(errors).build()
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)


    def handle_google_oauth(self, code, state):
        oauth = GoogleOAuth(code=code, state=state)
        token = Tokens.objects.get(token=state)
        token.delete()
        
        data = oauth.getUserData()
        user = check_registration(data['email'])
        if user != None :
            jwt = generate_jwt(user)
            oauth_google_builder = OAuthBuilder().set_jwt(jwt).set_IsUser('True').set_redirection('').build()
            return Response(oauth_google_builder, status=status.HTTP_200_OK)
        else:
            filtered_data = {'username': data['name'], 'email': data['email'], 'image_url': data['picture']}
            # print(f"Register Google: this is the filtered data JSON response: {filtered_data}")
            user = insert_user_in_db(filtered_data)
            is_sccuess  =  get_extern_image(user,filtered_data['image_url'])
            print(f'get_extern_image = {is_sccuess}')
            jwt = generate_jwt(user)
            oauth_google_builder = OAuthBuilder().set_jwt(jwt).set_IsUser('False').set_redirection('/oauth-register').build()
            return Response(oauth_google_builder, status=status.HTTP_201_CREATED)

    def handle_42_oauth(self, code, state):
        school_oauth = School_OAuth(code=code, state=state)
        token = Tokens.objects.get(token=state)
        token.delete()

        students_data = school_oauth.getStudentsData()
        # print(f'42 DATA is: {students_data}')
        email = students_data.get('email')
        student = check_registration(email)
        if student != None :
            # message = Message_Builder().set_message('You are already registered').build()
            jwt = generate_jwt(student)
            oauth_42_builder = OAuthBuilder().set_jwt(jwt).set_IsUser('True').set_redirection('').build()
            return Response(oauth_42_builder, status=status.HTTP_200_OK)
        else:
            login = students_data.get('login')
            image_url = students_data.get('image', {}).get('link')
            filtered_data =  {'email': email, 'username': login, 'image_url': image_url}
            # print(f"Register 42: this is the filtered data JSON response: {filtered_data}")
            student = insert_user_in_db(filtered_data)
            is_sccuess  =  get_extern_image(student,filtered_data['image_url'])
            print(f'get_extern_image = {is_sccuess}')
            jwt = generate_jwt(student)
            oauth_42_builder = OAuthBuilder().set_jwt(jwt).set_IsUser('False').set_redirection('/oauth-register').build()
            return Response(oauth_42_builder, status=status.HTTP_201_CREATED)

    def post(self, request):
        try:
            is_valid = validate_request_data_register(request.data)
            if not is_valid:
                error = ErrorBuilder().set_type('Format_From_Front_End').set_message('Invalid arguments').build()
                return Response(error, status=status.HTTP_400_BAD_REQUEST)

            register_type = request.data['type']
            if register_type == 'normal':
                return self.normal_registration_type(request)
            elif (register_type == 'oauth'):
                state = request.data['data']['state']
                code = request.data['data']['code']
                token = Tokens.objects.filter(token=state).first()
                if not token:
                   return INVALID_TOKEN_RES
                else :
                    type = token.type
                    if type and type == 'google_Oauth':
                        return self.handle_google_oauth(code, state)
                    elif type and type == '42_Oauth':
                        return self.handle_42_oauth(code, state)
                    else :
                        error = ErrorBuilder().set_type('token').set_message('Invalid OAuth Type').build()
                        print(f'LoginView Error: {str(error)}')
                        return Response(error, status=status.HTTP_400_BAD_REQUEST)
            else:
                error = ErrorBuilder().set_type('oauth').set_message('Undefined Authenticatin type').build()
                return Response(error, status=status.HTTP_400_BAD_REQUEST)
        # except ValidationError as e:
        #     error_message = e.detail
        #     errors = error_message
        #     error_string = ""
        #     for field_errors in errors.values():
        #         for error in field_errors:
        #             error_string += f"{error}\n"
        #     print(f'Im within ValidationError block ELSE: {error_string}')
        #     errors = ErrorBuilder().set_type('').set_message(error_string).build()
        #     return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            error_message = str(e)  # Ensure the error message is a string
            print(f'Im within Exception block ELSE: {error_message}')
            errors = ErrorBuilder().set_type('').set_message(error_message).build()
            return Response(errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class LoginView(APIView):

    def normal_login_type(self, request):
            input = request.data['data']['identity']['value']
            if not input :
                error = ErrorBuilder().set_type('').set_message('Empty Username').build()
                return Response(error, status=status.HTTP_400_BAD_REQUEST)        
            password = request.data['data']['password']

            user = CustomAuthenticationBackend().authenticate(request, username=input, password=password)
            log.info("[1]")
            if user is not None:
                login(request, user)
                auth_record = check_otp_is_enabled(user)
                if auth_record and auth_record.is_enabled is True:
                    log.info("[2]")
                    token = generate_token_user(user)
                    otp_error =  send_otp(token, auth_record)
                    if otp_error !=  None: 
                            return Response(otp_error,status=404)
                    log.info("[3]")
                    response = TwoFA_Builder().set_is_enabled('True').set_token(token.token).set_redirection('/2fa').build()
                    # redirection = {'Location': '/2fa'}
                    log.info("[response is sended]")
                    return Response(response, status=status.HTTP_200_OK)
                    # return Response(response, status=status.HTTP_301_MOVED_PERMANENTLY, headers=redirection)
                else:
                    redirection = request.data['refer']
                    if not redirection :
                        location = '/home'
                    else:
                        location = redirection
                    # json_response =  {'jwt': generate_jwt(user), 'redirection': location}
                    jwt_data = generate_jwt(user)
                    print (f"Origin-RefreshToekn: {jwt_data['refresh']}")
                    json_response = {'access_token': jwt_data['access'], 'redirection': location}
                    response = Response(json_response, status=status.HTTP_200_OK)
                    response.set_cookie(
                        key = settings.SIMPLE_JWT['AUTH_COOKIE'],
                        value = jwt_data['refresh'],
                        expires = settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
                        httponly = settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                        samesite = settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
                    )
                    # return Response(json_response, status=status.HTTP_301_MOVED_PERMANENTLY, headers=location)
                    return response

            error = ErrorBuilder().set_type('').set_message('Invalid Username or Password').build()
            # return (error, status=status.HTTP_400_BAD_REQUEST)
            return Response(error, status=status.HTTP_400_BAD_REQUEST)


    def handle_42_oauth(self, code, state):
        school_oauth = School_OAuth(code=code, state=state)
        token = Tokens.objects.get(token=state)
        token.delete()

        students_data = school_oauth.getStudentsData()
        email = students_data.get('email')
        student = check_registration(email)
        if student != None :
            jwt = generate_jwt(student)
            redirection = check_redirection(self.request)
            oauth_42_builder = OAuthBuilder().set_jwt(jwt).set_IsUser('True').set_redirection(redirection).build()
            return oauth_42_builder
        else:
            login = students_data.get('login')
            image_url = students_data.get('image', {}).get('link')
            filtered_data =  {'email': email, 'username': login, 'image_url': image_url}
            # print(f"Login 42: this is the filtered data JSON response: {filtered_data}")
            student = insert_user_in_db(filtered_data)
            is_sccuess  =  get_extern_image(student,filtered_data['image_url'])
            print(f'get_extern_image = {is_sccuess}')
            jwt = generate_jwt(student)
            oauth_42_builder = OAuthBuilder().set_jwt(jwt).set_IsUser('False').set_redirection('/oauth-register').build()
            return oauth_42_builder


    def handle_google_oauth(self, code, state):
        oauth = GoogleOAuth(code=code, state=state)
        token = Tokens.objects.get(token=state)
        token.delete()
    
        data = oauth.getUserData()
        user = check_registration(data['email'])
        if user != None :
            jwt = generate_jwt(user)
            redirection = check_redirection(self.request)
            oauth_google_builder = OAuthBuilder().set_jwt(jwt).set_IsUser('True').set_redirection(redirection).build()
            return oauth_google_builder
        else:
            filtered_data = {'username': data['name'], 'email': data['email'], 'image_url': data['picture']}
            # print(f"Login Google: this is the filtered data JSON response: {filtered_data}")
            user = insert_user_in_db(filtered_data)
            is_sccuess  =  get_extern_image(user,filtered_data['image_url'])
            print(f'get_extern_image = {is_sccuess}')
            jwt = generate_jwt(user)
            oauth_google_builder = OAuthBuilder().set_jwt(jwt).set_IsUser('False').set_redirection('/oauth-register').build()
            return oauth_google_builder


    def post(self, request):
        try:
            is_valid = validate_request_data_login(request.data)
            if not is_valid:
                error = ErrorBuilder().set_type('Format_From_Front_End').set_message('Invalid arguments').build()
                return Response(error, status=status.HTTP_400_BAD_REQUEST)

            login_type = request.data['type']

            if (login_type == 'normal'):
                return self.normal_login_type(request)
            elif (login_type == 'oauth'):
                state = request.data['data']['state']
                code = request.data['data']['code']
                token = Tokens.objects.filter(token=state).first()
                if not token:
                    error = ErrorBuilder().set_type('token').set_message('Invalid Token').build()
                    print(f'LoginView Error: {str(error)}')
                    return Response(error, status=status.HTTP_400_BAD_REQUEST)
                else :
                    type = token.type
                    if type and type == 'google_Oauth':
                        response = self.handle_google_oauth(code, state)
                        return Response(response, status=status.HTTP_200_OK)
                    elif type and type == '42_Oauth':
                        response = self.handle_42_oauth(code, state)
                        return Response(response, status=status.HTTP_200_OK)
                    else :
                        error = ErrorBuilder().set_type('token').set_message('Invalid OAuth Type').build()
                        print(f'LoginView Error: {str(error)}')
                        return Response(error, status=status.HTTP_400_BAD_REQUEST)
            else:
                error = ErrorBuilder().set_type('oauth').set_message('Undefined Authenticatin type').build()
                return Response(error, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            if hasattr(e, 'detail'):
                error_message = e.detail
            else:
                error_message = str(e)
            errors = ErrorBuilder().set_type('').set_message(error_message).build()
            print(f'Builder message: {errors}')
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)


#! 2FA

class Check_2FAView(APIView):
    # permission_classes = [IsAuthenticated]
    def post(self, request):
        is_valid = validate_request_data_2fa(request.data)
        if not is_valid:
            error = ErrorBuilder().set_type('From Front-End').set_message('Invalid JSON Format').build()
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        token = request.data.get('token')
        other = request.data.get('otp')

        try :
            record = Tokens.objects.get(token=token)
            if record.other == other:
                record.delete()
                user = record.user_id
                jwt = generate_jwt(user)
                redirection = request.data.get('refer')
                if not redirection:
                    location = '/home'
                else:
                    location = redirection
                response =  {'jwt': jwt, 'redirection': location}
                return Response(response, status=status.HTTP_200_OK)
                # response = OAuthBuilder().set_IsUser('1').set_jwt(jwt).build()
                # return Response(response, status=status.HTTP_301_MOVED_PERMANENTLY, headers=location)
            else:
                error = ErrorBuilder().set_type('').set_message('Invalid Code').build()
                return Response(error, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            message = str(e)
            print(f'Check_2FAView Exception: {message}')
            error = ErrorBuilder().set_type('').set_message(message).build()
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
    
##! Google_OAuth
class GoogleGenLink(APIView) :
    def get(self ,req):
        oauth = GoogleOAuth()
        link =  oauth.GenLink()
        response_link = {'link': link}
        return Response(response_link, status=status.HTTP_200_OK)

#! 42_OAuth
class GenerateLink42(APIView):
    def get(self, request):
        oauth_42 = School_OAuth()
        link = oauth_42.generate_link()
        response_link = {'link': link}
        return Response(response_link, status=status.HTTP_200_OK)


#! forget-password
class ForgetPasswordView(APIView):
    def check_email_in_db(self, email):
        if not email:
            return False
        exists = User.objects.filter(email=email).first()
        return exists

    def post(self, request):

        is_valid = validate_request_data_forget_pwd(request.data)
        if not is_valid:
            error = ErrorBuilder().set_type('From Front-End').set_message('Invalid JSON Format').build()
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        try: 
            email = request.data['email']
            email_in_db = self.check_email_in_db(email)

            if not email_in_db:
                message = ErrorBuilder().set_type('email_not_found').set_message('Not Found').build()
                return Response(message, status=status.HTTP_400_BAD_REQUEST)
            return self.generate_email_link(email)
        except Exception as e:
            error_message = e.detail
            errors = ErrorBuilder().set_type('').set_message(error_message).build()
            print(f'Builder message: {errors}')
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    def link_token_user(self, user):
        secret = secrets.token_hex(12)
        record = Tokens.objects.create()
        record.token = secret
        record.type = 'password'
        record.user_id = user
        record.save()
        return record

    def generate_email_link(self, email):
    #* linked a token to the user who has forgotten his password
        user = User.objects.filter(email=email).first()
        token = self.link_token_user(user)
        link = self.generate_link(token)
        if link:
            message = Message_Builder().set_message('A link was sent to your email').set_redirection('/login').build()
            return Response(message, status=status.HTTP_200_OK)

            # location = {'Location': '/login'}
            # return Response(message, status=status.HTTP_301_MOVED_PERMANENTLY, headers=location)
        else:
            error = ErrorBuilder().set_type('generate-link').set_message('The Link is invalid').build()
            print(f'generate_email_link: {str(error)}')
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
    def generate_link(self, token):
        try:
            client_reset_url = getattr(settings, 'CLIENT_RESET_URL', None)
            if client_reset_url:
                # link = f'{client_reset_url}/resetPassword?token={token.token}'
                link = f'http://127.0.0.1:5173/reset/resetpassword.html?token={token.token}'
                subject = 'Reset Password for ft_transcendance Account'
                message = f'Click on the link below to be redirected for resetting your password : {link}'
                sender = settings.EMAIL_HOST_USER
                receiver = [token.user_id.email]
                html_content =  render_to_string('reset_pass.html',{'user':token.user_id.username, 'link':link})
                send_mail(subject, message, sender, receiver,html_message=html_content)
                return link
        except Exception as e:
            print(e)
            return None

# from datetime import datetime
# from django.core.mail import send_mail
# from django.template.loader import render_to_string
# from django.utils.html import strip_tags
# from django.conf import settings


# context = {
#   "receiver_name": "Saium Khan",
#   "age": 27,
#   "profession": "Software Developer",
#   "marital_status": "Divorced",
#   "address": "Planet Earth"
#   "year": 2023
# }

# receiver_email = "saium@abcinc.com"
# template_name = "email/template/path/in/template/folder/filename.html"
# convert_to_html_content =  render_to_string(
#   template_name=template_name,
#   context=context
# )
# plain_message = strip_tags(convert_to_html_content)

# yo_send_it = send_mail(
#   subject="Receiver information from a form",
#   message=plain_message,
#   from_email=settings.EMAIL_HOST_USER,
#   recipient_list=[receiver_email,]   # recipient_list is self explainatory
#   html_message=convert_to_html_content
#   fail_silently=True    # Optional
# )


#! update-password/
class UpdatePasswordView(APIView):

    def post(self, request):
        try:
            message  = "" 
            is_valid = validate_request_data_upgrade_pwd(request.data)
            if not is_valid:
                error = ErrorBuilder().set_type('From Front-End').set_message('Invalid JSON Format').build()
                return Response(error, status=status.HTTP_400_BAD_REQUEST)

            token = request.data['token']
            user = self.fetch_user_from_token(token)
            if user:
                password = request.data['data']['password']
                retype_password = request.data['data']['retype_password']

                if password and retype_password and password == retype_password:
                    self.reset_password_in_db(user, password)
                    token_record = Tokens.objects.get(token=token)
                    token_record.delete()
                    message = Message_Builder().set_message('Your password has been changed successfully').set_redirection('/login').build()
                    # redirection = {'Location': '/login'}
                    return Response(message, status=200)
                else :
                    error = ErrorBuilder().set_type('Unmatched_password').set_message("Passwords don't match").build()
                    print(f'UpdatePasswordView error: {str(error)}')
                    return Response(error, status=status.HTTP_400_BAD_REQUEST)

            else :
                error = ErrorBuilder().set_type('reset_password').set_message('Error: Invalid Token/User').build()
                print(f'UpdatePasswordView error: {str(error)}')
        except Exception as e:
           error = ErrorBuilder().set_type('Invalid JWT').set_message(e.__str__()).build()
        return Response(error, status=status.HTTP_404_NOT_FOUND)

    def fetch_user_from_token(self, token):
        record = Tokens.objects.filter(token=token).first()
        if record is None:
            return None
        user = record.user_id
        return user


    def reset_password_in_db(self, user, password):
        user.set_password(password)
        user.save()



from rest_framework_simplejwt.authentication import JWTAuthentication
JWT_authenticator = JWTAuthentication()

class OAuth_Register(APIView):
    def post(self, request):
        try: 
            is_valid = validate_request_data_oauth_register(request.data)
            if not is_valid:
                error = ErrorBuilder().set_type('Form Front-End').set_message('Invalid JSON Format').build()
                return Response(error, status=status.HTTP_400_BAD_REQUEST)
            response = JWT_authenticator.authenticate(request)
            if response is not None:
                user, token = response
                username = request.data.get("username")
                partial_change = {"username": username}
                serializer = OAuthRegistrationSerializer(user, partial_change, partial=True)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    message = Message_Builder().set_message("You've successfully been registered").set_redirection('/login').build()
                    return Response(message, status=status.HTTP_201_CREATED)
            else:
                return INVALID_TOKEN_RES
        except ValidationError as e:
            error_message = e.detail
            errors = {}
            for field, field_errors in error_message.items():
                errors[field] = field_errors[0]
            errors = ErrorBuilder().set_type('').set_message(field_errors[0]).build()
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

##############>>  Don't remove this !!!  <<< 

# this code for generating Level data 
#   data = ("Novice","Apprentice","Bronze","Basic","Rookie","Entry","Greenhorn","Trainee","Learner","Initiate","Iron","Copper","Silver","Gold","Platinum","Diamond","Titanium","Obsidian","Adamantium","Etherium")

#         i = 0; 
#         for item in data: 
#             lv = Level.objects.create(name=item,level_no=i, image="https://picsum.photos/200/300")
#             i += 1
#         return Response({"ok":"ok"})




class  Profile(APIView):

    def get(self, req):

        auth_data = JWT_authenticator.authenticate(req)
        if auth_data is  None:
            error = ErrorBuilder().set_type('Invalid JWT').set_message('No/Invalid Token is provided in the Header').build()
            return Response(error, status=status.HTTP_401_UNAUTHORIZED)
        
        user = auth_data[0]
        print(user.username)
        level_data = get_level(user) 
        print(f"{user.avatar_link}")  
        tfa = {
        "type": "email",
        "content": "",
        "status":    False 
        } 
        try:
            tfa_obj = Auth.objects.get(user_id=user) 
            tfa['content'] = tfa_obj.content
            tfa['status'] = tfa_obj.is_enabled 
        except:
            tfa['content'] = ""

        data = {
            "username": user.username,
            "profile_image": f"{settings.BACKEND_URL}{user.avatar_link.url}",
            "bg_image": "https://cdn.intra.42.fr/coalition/cover/73/BiosBG.jpg", # just for test 
            'total_friends' : 150,
            "online" : True,
            "email": user.email,
            "tfa": tfa,
            "matches": {
            "total": user.total_matches,
            "wins": user.wins,
            "losses": user.losses
           
            },
            "level": level_data
        }
        return Response(data)
        


class  Users(APIView):

  
    def get(self, req, username):

        auth_data = JWT_authenticator.authenticate(req)
        if auth_data is  None:
            return INVALID_TOKEN_RES
        user = auth_data[0]
        target = None
        try:
         target = User.objects.get(username=username)
        except Exception as e :
            return USER_NOT_FOUND_RES
        relation = get_relation(user1=user, user2=target)
        if relation == UserRelation.BLOCKED:
             return USER_NOT_FOUND_RES
        if relation == UserRelation.BLOCKER:
            data = {
                "username": target.username,
                "relation": relation,
                "profile_image": f"{settings.BACKEND_URL}/media/avatars/default.png",
                "bg_image": "https://cdn.intra.42.fr/coalition/cover/73/BiosBG.jpg",
                'total_friends' : 0,
                "online" : False,
                "matches": {
                "total":    0,
                "wins":     0,
                "losses":   0
                },
                "level": {
                        "name"     : "unknown",
                        "profile_image"    : "/media/levels/default.png", # here must be add default level
                        "current"  : 0,
                        "progress" : 0
                         }
            }
            return Response(data)
        # check is self  
        # first  check is Blocked or block
        # check  is Friend 
        # check is receive_inv  or send_inv 
        #    
        
        print(user.username)
        level_data = get_level(target) 
        print(f"{user.avatar_link}")  
        data = {
            "username": target.username,
            "relation": relation,
            "profile_image": f"{settings.BACKEND_URL}{user.avatar_link.url}",
            "bg_image": "https://cdn.intra.42.fr/coalition/cover/73/BiosBG.jpg",
            'total_friends' : 150,
            "online" : True,
             "matches": {
            "total":    target.total_matches,
            "wins":     target.wins,
            "losses":   target.losses
            },
            "level": level_data
        }
        return Response(data)
        


from .models import Match
import uuid
from django.utils import timezone
from users.models import Match, User
import random


users = User.objects.all()
if len(users) < 2:
    raise ValueError("Not enough users in the database to create matches.")

def create_mock_matches(num_matches=10):
        for _ in range(num_matches):
            player1, player2 = random.sample(list(users), 2)
            player1_goals = random.randint(0, 10)
            player2_goals = random.randint(0, 10)
            is_draw = player1_goals == player2_goals
            winner = None if is_draw else (player1 if player1_goals > player2_goals else player2)
            
            match = Match.objects.create(
                time=random.randint(30, 120),  # match duration in minutes
                winner=winner,
                is_draw=is_draw,
                player1=player1,
                player2=player2,
                player1_goals=player1_goals,
                player2_goals=player2_goals,
                match_id=uuid.uuid4(),
            )
            match.save()
            print(f"Created match: {match.match_id}")



from .models import Match , Friend , Blocked_Friend , Invitation
class  Matches(APIView) :

    def get_status_from_match(self, draw, user_goals, opponent_goals):
        if draw == True:
            return 'draw'
        return 'win' if user_goals > opponent_goals else 'lose'

    def make_match(self ,match, username):
        # user = match.player1.  if match.player1.username == username else match.player2.username
        # opponent =   match.player1 . if match.player1.username == username else match.player2.username

        user = ""
        opponent = ""
        if match.player1.username == username:
            user = {
                "username": match.player1.username,
                "goals": match.player1_goals
            }
            opponent = {
                "obj": match.player2,
                "username": match.player2.username,
                "goals": match.player2_goals
            }
        else :
            user = {
                "username": match.player2.username,
                "goals": match.player2_goals
            }
            opponent = {
                "obj": match.player1,
                "username": match.player1.username,
                "goals": match.player1_goals
            }

        return { 
            "match_id": match.match_id,
            "status": self.get_status_from_match(match.is_draw, user['goals'], opponent['goals']) ,
            "goals": user['goals'], 
            "opponent":{
                "username" : opponent['username'],
                "goals": opponent['goals'],
                "profile_image" : f"{opponent['obj'].avatar_link}",
                "profile" : f"/users/{opponent['username']}",
                "level": get_level(opponent['obj']) 
            }
        }

    def get(self,req):
        auth_data = JWT_authenticator.authenticate(req)
        if auth_data is  None:
            return INVALID_TOKEN_RES
        user = auth_data[0]    
        matches = Match.objects.filter(Q(player1=user) | Q(player2=user))
        data  = []
        for match in matches:
            data.insert(0,self.make_match(match=match, username=user.username))
            print(match)
        return Response({"data" : data})

class UserMatches(APIView) :

    def get_status_from_match(self, draw, user_goals, opponent_goals):
        if draw == True:
            return 'draw'
        return 'win' if user_goals > opponent_goals else 'lose'

    def make_match(self ,match, username):
        # user = match.player1.  if match.player1.username == username else match.player2.username
        # opponent =   match.player1 . if match.player1.username == username else match.player2.username

        user = ""
        opponent = ""
        if match.player1.username == username:
            user = {
                "username": match.player1.username,
                "goals": match.player1_goals
            }
            opponent = {
                "obj": match.player2,
                "username": match.player2.username,
                "goals": match.player2_goals
            }
        else :
            user = {
                "username": match.player2.username,
                "goals": match.player2_goals
            }
            opponent = {
                "obj": match.player1,
                "username": match.player1.username,
                "goals": match.player1_goals
            }

        return { 
            "match_id": match.match_id,
            "status": self.get_status_from_match(match.is_draw, user['goals'], opponent['goals']) ,
            "goals": user['goals'],

            "opponent":{
                "username" : opponent['username'],
                "goals": opponent['goals'],
                "profile_image" : f"{opponent['obj'].avatar_link}",
                "profile" : f"/users/{opponent['username']}",
                 "level": get_level(opponent['obj']) 
            }
        }

    def get(self,req ,username):
        auth_data = JWT_authenticator.authenticate(req)
        if auth_data is  None:
            return INVALID_TOKEN_RES
        user = auth_data[0]
        target = None
        try:
            start = int(req.GET.get('start', 0))
            end  = int(req.GET.get('end', start + 10))
            if start < 0 or end < 0 or end < start: 
                return INVALID_PARAMS_RES
        except:
             return INVALID_PARAMS_RES
        try:
            print("tested ...")
            target = User.objects.get(username=username)
        except Exception as e:
           return USER_NOT_FOUND_RES
        rel = get_relation(user1=user,user2=target)
        print(rel);
        block_record = Blocked_Friend.objects.filter(Q(blocker=user) | Q(blocked=user))
        block_row  = None 
        for item in  block_record:
            if item.blocked == target or item.blocker == target:
                block_row  = item;
                break
        if  block_row != None:
            print(f"{block_row.blocked} {username}")
            if block_row.blocked == user: 
                return USER_NOT_FOUND_RES;
            else:
                return Response([])
    
        #- - - - - - - - - -
        #
        #   check relation Between all users 
        # - - - - - - - - - - -

        matches = Match.objects.filter(Q(player1=target) | Q(player2=target)).order_by('-date')
        matches = matches[start:end]
        data  = []
        for match in matches: 
            data.append(self.make_match(match=match, username=target.username))
            print(match.date)
        print(len(data))

        return Response(data)
    
class FriendsView(APIView):
    def get(self,req):
        auth_data = JWT_authenticator.authenticate(req)
        if auth_data is  None:
            return INVALID_TOKEN_RES
        user = auth_data[0]
        try:
            start  = int(req.GET.get('start', 0))
            end    = int(req.GET.get('end', start + 10))
            filter = req.GET.get('filter', None)
            if start < 0 or end < 0 or end < start: 
                return INVALID_PARAMS_RES
        except:
             return INVALID_PARAMS_RES
        
        records = Friend.objects.filter(Q(user1=user) | Q(user2=user))
        
        # records = records[start:end]
        data  = []
        
        for item in records: 
            friend = None
            if item.user1 == user : 
                friend = item.user2
            else:
                friend = item.user1 
            if filter == None or  friend.username.find(filter) >  -1:
                data.append({"username" : friend.username,
                        "profile_image" : f"{settings.BACKEND_URL}/{friend.avatar_link}",
                        "online" : True ,
                        "profile" : f"/users/{friend.username}",
                        "relation" : f"{UserRelation.FRIEND}"
                        })
        data = data[start:end]
        return Response(data)
    
class UserFriendsView(APIView):
    def get(self,req, username):
        auth_data = JWT_authenticator.authenticate(req)
        if auth_data is  None:
            return INVALID_TOKEN_RES
        user = auth_data[0]
        try:
            start  = int(req.GET.get('start', 0))
            end    = int(req.GET.get('end', start + 10))
            filter = req.GET.get('filter', None)
            if start < 0 or end < 0 or end < start: 
                return INVALID_PARAMS_RES
        except:
             return INVALID_PARAMS_RES
        target =  None
        print(username)
        try:
             target = User.objects.get(username=username)
        except Exception as ex:
          return USER_NOT_FOUND_RES
        relation = get_relation(user, target)
        if relation =='blocked' or relation == 'blocker':
            return Response([])
        records = Friend.objects.filter(Q(user1=target) | Q(user2=target))
        data  = []
        for item in records: 
            friend = None
            if item.user1 == target : 
                friend = item.user2
            else:
                friend = item.user1 
            if filter == None or  friend.username.find(filter) >  -1:
                user_relation =  get_relation(user1=user, user2=friend)
                if user_relation != UserRelation.BLOCKED:
                    data.append({"username" : friend.username,
                        "profile_image" : f"{settings.BACKEND_URL}/{friend.avatar_link}",
                        "online" : True ,
                        "profile" : f"/users/{friend.username}",
                        "relation" : user_relation
                        })
        data = data[start:end]
        return Response(data)    
class BlockedUserView(APIView):
    def get(self,req):
        auth_data = JWT_authenticator.authenticate(req)
        if auth_data is  None:
            return INVALID_TOKEN_RES
        user = auth_data[0]
        try:
            start  = int(req.GET.get('start', 0))
            end    = int(req.GET.get('end', start + 10))
            filter = req.GET.get('filter', None)
            if start < 0 or end < 0 or end < start: 
                return INVALID_PARAMS_RES
        except:
                return INVALID_PARAMS_RES
        records = Blocked_Friend.objects.filter(blocker=user)
        data  = []
        for item in records: 
            if filter == None or  item.blocked.username.find(filter) >  -1:
                data.append({
                            "username" : item.blocked.username,
                        "profile_image" : f"{settings.BACKEND_URL}/{item.blocked.avatar_link}",
                        "profile" : f"/users/{item.blocked.username}",
                        "relation" : f"{UserRelation.BLOCKER}"
                                })
        data = data[start:end]
        return Response(data)
class PendingUserView(APIView):
    def get(self,req):
        auth_data = JWT_authenticator.authenticate(req)
        if auth_data is  None:
            return INVALID_TOKEN_RES
        user = auth_data[0]
        try:
            start  = int(req.GET.get('start', 0))
            end    = int(req.GET.get('end', start + 10))
            filter = req.GET.get('filter', None)
            if start < 0 or end < 0 or end < start: 
                return INVALID_PARAMS_RES
        except:
                return INVALID_PARAMS_RES
        records = Invitation.objects.filter(receiver=user)
        data  = []
        for item in records: 
            if filter == None or  item.sender.username.find(filter) >  -1:
                data.append({
                                "username" : item.sender.username,
                                "profile_image" : f"{settings.BACKEND_URL}/{item.sender.avatar_link}",
                                "profile" : f"/users/{item.sender.username}",
                                "relation" : f"{UserRelation.REC_REQ}"
                                })
        data = data[start:end]
        return Response(data)

# class InvitationUserView(APIView):
#     def get(self,req):
#         auth_data = JWT_authenticator.authenticate(req)
#         if auth_data is  None:
#             return INVALID_TOKEN_RES
#         user = auth_data[0]
#         try:
#             start  = int(req.GET.get('start', 0))
#             end    = int(req.GET.get('end', start + 10))
#             filter = req.GET.get('filter', None)
#             if start < 0 or end < 0 or end < start: 
#                 return INVALID_PARAMS_RES
#         except:
#                 return INVALID_PARAMS_RES
#         records = Invitation.objects.filter(sender=user)
#         data  = []
#         for item in records: 
#             if filter == None or  item.blocked.username.find(filter) >  -1:
#                 data.append({
#                         "username" : item.receiver.username,
#                         "profile_image" : f"{settings.BACKEND_URL}/{item.receiver.avatar_link}",
#                         "profile" : f"/users/{item.receiver.username}"
#                                 })
#         data = data[start:end]
#         return Response(data)


from .serializers import UserAvatarSerializer 
from rest_framework.parsers import MultiPartParser, FormParser

class UserAvatarUpload(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, req) :
        try:
            auth_data = JWT_authenticator.authenticate(req)
            if auth_data is  None:
                return INVALID_TOKEN_RES
            user = auth_data[0]
            serializer = UserAvatarSerializer(instance=user, data=req.data)
            if serializer.is_valid():
                serializer.save()
                print(user.avatar_link.url)
                link = str(serializer.data["avatar_link"])
                return Response({"url" : f"{settings.BACKEND_URL}{link}"}, status=status.HTTP_200_OK)
        except:
               return Response({"error": "unexpected error"}, status=status.HTTP_400_BAD_REQUEST)
        print(f"{serializer.errors['avatar_link'][0]}")
        return Response({"error": serializer.errors['avatar_link'][0]}, status=status.HTTP_400_BAD_REQUEST)