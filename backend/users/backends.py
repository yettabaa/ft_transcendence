from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
import ssl
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
from django.utils.functional import cached_property

UserModel = get_user_model()

class CustomAuthenticationBackend(ModelBackend):
    def authenticate(self, request, username=None, email=None, password=None, **kwargs):

        if username is None:
            return None
        try:
            if '@' in username:
                user = UserModel.objects.get(email=username)  # Query by email
            else:
                user = UserModel.objects.get(username=username)
            print(f'user is {user}')
            if user.check_password(password):
                return user
        except UserModel.DoesNotExist:
            return None
            # UserModel().set_password(password)




class EmailBackend(SMTPBackend):
    @cached_property
    def ssl_context(self):
        if self.ssl_certfile or self.ssl_keyfile:
            ssl_context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
            ssl_context.load_cert_chain(self.ssl_certfile, self.ssl_keyfile)
            return ssl_context
        else:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            return ssl_context