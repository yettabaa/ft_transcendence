from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
from django import forms
from .models import User, Tokens, Auth , Level, Blocked_Friend , Invitation , Conversation, Message, Friend, Match


class UserCreationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    retype_password = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'username')

    def clean_retype_password(self):

        password = self.cleaned_data.get("password")
        retype_password = self.cleaned_data.get("retype_password")
        if password and retype_password and password != retype_password:
            raise ValidationError("Passwords don't match")
        return retype_password

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('email', 'password', 'is_active', 'is_admin')

    def clean_password(self):
        return self.initial["password"]


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('email', 'username', 'is_admin')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username',)}),
        ('Permissions', {'fields': ('is_admin',)}), 
        ('Match', {'fields': ('wins','losses','total_matches')})
    )

    list_filter = ('is_admin', )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'retype_password'),
        }),
    )

    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()

admin.site.register(User, UserAdmin)
admin.site.register(Tokens)


class AuthAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'content', 'is_enabled', 'method')  # Customize the fields displayed in the list view
    list_filter = ('is_enabled', 'method')  # Add filters for is_enabled and method fields
    search_fields = ('user_id__username', 'content', 'method')  # Add search functionality for specified fields

admin.site.register(Auth, AuthAdmin)
admin.site.register(Level)
admin.site.register(Blocked_Friend)
admin.site.register(Invitation)
admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(Friend)
admin.site.register(Match)