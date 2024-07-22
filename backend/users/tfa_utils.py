from django.core.mail import send_mail
from django.conf import settings
import secrets
from rest_framework.response import Response
from rest_framework import status
from .design_patterns import ErrorBuilder
from .models import User, Auth
from django.template.loader import render_to_string 


def check_otp_is_enabled(user):
    try:
        record = Auth.objects.filter(user_id=user).first()
        print(f'record is: {record}')
        return record
    except Exception as e:
        message = str(e)
        print(f'check_otp_is_enabled: {message}')
        return Response(message, status=status.HTTP_400_BAD_REQUEST)


def generate_otp():
    # characters = string.digits
    # otp = ''.join(random.choices(characters, k=length))
    otp = ''.join(secrets.choice('0123456789') for _ in range(6))
    return otp

def send_otp_email(email, otp) -> bool:
    try:
        tfa_record = Auth.objects.get(content=email)
        subject = 'OTP for ft_transcendance'
        message = f'This is a generated OTP for 2FA : {otp}'
        sender = settings.EMAIL_HOST_USER
        receiver = [email]
        html_content =  render_to_string('2fa_email.html',{'user':tfa_record.user_id, 'otp':otp})
        send_mail(subject, message, sender, receiver,html_message=html_content)
        return True
    except Exception as e:
        print(f'fail send 2fa Email{e}') #this just for debugging 
        return False 


# @permission_classes([IsAuthenticated])
def send_otp(token, auth_record) -> Response:
    #! This function has to happen accordinly with login is 200
    try:
        # user = User.objects.get(email=email)
        # user = User.token.get(token=token)
        otp = generate_otp()
        token.other = otp
        token.type = 'otp' 
        token.save()
        # email = user.email
        email = auth_record.content
        send_status =  send_otp_email(email, otp)
        if send_status:
             return None
            # return Response("{'message': 'The OTP has been sent successfully'}", status=status.HTTP_200_OK)
        else: 
            error = ErrorBuilder().set_type('send_email').set_message("Fail to Send Email,try again ").build()
            return error
    except User.DoesNotExist:
        error = ErrorBuilder().set_type('OTP').set_message("The User with this email doesn't exist").build()
        return error
