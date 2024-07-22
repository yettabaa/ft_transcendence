from rest_framework import serializers
from .models import User, Tokens

from rest_framework.validators import UniqueValidator
from django.core.validators import RegexValidator
class RegistrationSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        error_messages={
            'blank': 'Username field should not be blank'
        },
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message='A user with that username already exists '
            ),
            RegexValidator(
                regex=r'^[a-z][\w-]{2,15}[a-z\d]$',
                message='Valid Characters are : [a-z][\w-][a-z\d] & Length must be between 3 and 16 characters long',
                code='invalid_username'
            )
        ]
    )

    email = serializers.EmailField(
        error_messages={
            'blank': 'Email field should not be blank ',
            'invalid': 'Enter a valid email address '
        },
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message='A user with that email already exists '
            )
        ]
    )

    password = serializers.CharField(
        style={"input_type": "password"},
        write_only=True,
        error_messages={'blank': 'Password field should not be blank'}
    )

    retype_password = serializers.CharField(
        style={"input_type": "password"},
        write_only=True,
        error_messages={'blank': 'Retype-Password field should not be blank'}
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'retype_password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        errors = {}
        password = data.get('password')
        retype_password = data.get('retype_password')

        if password and retype_password and password != retype_password:
            errors['password'] = "Passwords don't match"
            raise serializers.ValidationError(errors)
        return data

    def save(self):
        user = User (
            username=self.validated_data['username'],
            email=self.validated_data['email'],
        )
        user.set_password(self.validated_data['password'])
        user.save()
        return user

from django.db import IntegrityError

class OAuthRegistratinSerialize(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['username', 'email']

    def save(self):
        try:
            user = User.objects.create(
                username=self.validated_data['username'],
                email=self.validated_data['email']
            )
            user.save()
            return user
        except IntegrityError:
            return None

class OAuthRegistrationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        error_messages={
            'blank': 'Username field should not be blank'
        },
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message='A user with that username already exists '
            ),
            RegexValidator(
                regex=r'^[a-z][\w-]{2,15}[a-z\d]$',
                message='Valid Characters are : [a-z][\w-][a-z\d] & Length must be between 3 and 16 characters long',
                code='invalid_username'
            )
        ]
    )

    class Meta:
        model = User
        fields = ['username']

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.save()
        return instance

from rest_framework import serializers
from PIL import Image  
from .models import User 


class UserAvatarSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id','avatar_link',)

    def update(self, instance, validated_data):
        avatar = validated_data.get('avatar_link', instance.avatar_link)
        instance.avatar_link = avatar
        instance.avatar_link.name=f"{instance.username}.png"
        print(instance.avatar_link.path)
        instance.save()
        self.resize_image(instance.avatar_link.path, (250, 250)) 
        return instance

    def resize_image(self, image_path, size):
        try:
            img = Image.open(image_path)
            img.thumbnail(size)
            img.save(image_path)
        except IOError:
            print(f"Cannot resize image at {image_path} IOError.")
        except Exception as e:
            print(f"An error occurred while resizing image at {image_path}: {str(e)}")