from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import admin

# local
from .models import (User, Profile, Followlist)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """ user admin """


admin.site.register(Profile)
admin.site.register(Followlist)
