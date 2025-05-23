from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
from django.utils.translation import gettext_lazy as _


class CustomUserAdmin(UserAdmin):
    ordering = ["first_name"]

    fieldsets = (
            ("Account info", {"fields": ("username","email", "password")}),
            (_("Profile Picture"), {"fields":("profile",)}),
            (_("Personal info"), {"fields": ("first_name", "last_name","phone", "about", "date_of_birth")}),
            ( _("Permissions"), { "fields": ( "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
            (_("Important dates"), {"fields": ("last_login", "date_joined")}),
        )

    # readonly_fields =("username", "email")
    list_display = ("username","email", "first_name", "last_name", "is_staff")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("first_name", "last_name", "email")



class RoomAdmin(admin.ModelAdmin):
    readonly_fields = ("room_size",)

class RoomMemberAdmin(admin.ModelAdmin):
    readonly_fields = ("joined_at", "join_requested_at")


admin.site.register(Room, RoomAdmin)
admin.site.register(Files)
# admin.site.register(Folder)
admin.site.register(RoomTags)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(RoomMembers, RoomMemberAdmin)
admin.site.register(Notifications)
admin.site.register(DownLoadTokens)