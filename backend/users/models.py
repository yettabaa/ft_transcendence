from django.db import models

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)
from django.utils import timezone

# Create your models here.

class UserManager(BaseUserManager):
    def create_user(self, username, email, password):
        if not username:
            raise ValueError('Users must have a username')
        if not email:
            raise ValueError('Users must have an email')

        user = self.model(
            email=self.normalize_email(email),
            username=username,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password):
        user = self.create_user(
            username=username,
            email=email,
            password=password
        )
        user.is_admin = True
        # user.is_staff = True
        user.save(using=self._db)
        return user

# from django.core.exceptions import ValidationError
# def validate_username(value):
#     if not value:
#         raise ValueError("username field should not be blank: Validator")

# def validate_email(value):
#     if not value:
#         raise ValueError("email field should not be blank: Validator")   

from django.core.validators import validate_email

class User(AbstractBaseUser):
    username = models.CharField(max_length=50, blank=True, unique=True,
        # validators=[validate_username],
        error_messages={
            'unique': 'A user with that username already exists',
        }
    )
    email = models.EmailField(max_length=255, blank=True, unique=True,
        validators=[validate_email],
        error_messages={
            'unique': 'A user with that email already exists',
        }
    )

    is_active = models.BooleanField(default=True)
    total_matches = models.IntegerField(default=0)
    # is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    #   otp = models.CharField(max_length=6, null=True, blank=True)
    avatar_link = models.ImageField(upload_to='avatars', default='avatars/default.png')
    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin


class Auth(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auth')
    content = models.CharField(max_length=50, blank=True,unique=True) # add by alphaben   must replaced  by EmailField 
    is_enabled = models.BooleanField(default=False)
    method = models.CharField(max_length=25,default='email') # email

    # def __init__(self):
    #     return self.content

from django.conf import settings

class Tokens(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='token',blank=True, null=True)
    type = models.CharField(max_length=25)
    token = models.CharField(max_length=12)
    date = models.DateTimeField(auto_now_add=True)
    expired_date = models.DateTimeField(default=timezone.now() + timezone.timedelta(minutes=settings.TOKEN_EXPIRATION))
    other = models.CharField(max_length=12, null=True)

    class Meta:
        verbose_name_plural = "Tokens"

    def __str__(self):
        return self.token

#! put just a path  like this  /media/beginner.png  

class Level(models.Model):
    level_no   =  models.IntegerField(default=0)
    name       =   models.CharField(max_length=30)
    image      =   models.CharField(max_length=255)
    
    def __str__(self):
        return self.name
    
# Added 03/06
    
class Blocked_Friend(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocker_friend')
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_friend')

    def __str__(self):
        return f'{self.blocker} -> {self.blocked}'
    
class Invitation(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sender_invitations')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='receiver_invitations')

    def __str__(self):
        return f'{self.sender} -> {self.receiver}'
    

class Conversation(models.Model):
    cuuid = models.UUIDField(primary_key=True)
    last_message = models.TextField(blank=False, null=False, max_length=500)
    status = models.TextField()
    last_date = models.DateTimeField(auto_now_add=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.sender} : {self.last_message} . Time: {self.last_date}'
    
class Message(models.Model):
    conversation_id = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='id_message')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sender_message')
    status = models.BooleanField(default=False)
    content = models.TextField(blank=False, null=False, max_length=500)
    message_type = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender} -> {self.receiver} : {self.content} . Time: {self.date}'


class Friend(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user1_friend')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user2_friend')
    conversation_id = models.ForeignKey(Conversation, on_delete=models.CASCADE,null=True, related_name='conversation_id_friend')

    def __str__(self):
        return f'{self.user1} <-> {self.user2}'


from django.core.validators import MaxValueValidator

class Match(models.Model):
    time = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)
    winner = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='winner_match')
    is_draw = models.BooleanField(default=False)
    player1 = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='player1_match')
    player2 = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='player2_match')
    player1_goals = models.PositiveIntegerField(validators=[MaxValueValidator(10)])
    player2_goals = models.PositiveIntegerField(validators=[MaxValueValidator(10)])
    match_id = models.UUIDField(primary_key=True)


    class Meta:
        verbose_name_plural = "Matches"

    def __str__(self):
        return f'{self.player1} VS {self.player2}'

