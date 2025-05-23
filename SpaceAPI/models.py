from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from .managers import CustomUserManager
from django.shortcuts import reverse

class CustomUser(AbstractUser):
    phone = models.CharField(_("phone"), max_length=12, null=True, blank=True)
    about = models.CharField(_("about"), max_length=500, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile = models.ImageField(upload_to="media/user/profile", null=True, blank=True)
    def __str__(self):
        return self.username


class RoomTags(models.Model):
    name= models.CharField(max_length=20)
    def __str__(self):
        return self.name


class Room(models.Model):
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    room_size = models.BigIntegerField(default=52428800) #50mb -> bytes
    used_space = models.BigIntegerField(default=0)
    room_name = models.CharField( max_length = 200 )

    description = models.TextField(max_length= 2000, blank=True, null=True)
    room_type = models.CharField(max_length=50, choices=(('pvt', "Private"), ('pub', "Public")))
    created_at = models.DateTimeField(auto_now_add=True)
    
    room_pass = models.CharField(max_length=1000, blank=True, null=True)

    tags = models.ManyToManyField(to=RoomTags, blank=True, related_name="room_tags")

    logo = models.ImageField(upload_to='media/rooms/icons', null=True, blank=True)

    allow_others_to_upload = models.BooleanField(default=False)
    make_visible_on_search = models.BooleanField(default=False)

    
    def __str__(self):
        return self.room_name


class Files(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    file = models.FileField(upload_to="media/rooms/files")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now_add=True)
    file_size = models.IntegerField(default=0)
    file_name = models.CharField(max_length=200)
    file_type = models.CharField(max_length=20)

    visibility = models.BooleanField(default=False)
    owner = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL)

    is_paid = models.BooleanField(default=False)
    amount = models.BigIntegerField(default=0) # in paise

    def __str__(self):
        return self.file_name


class RoomMembers(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=50, choices=(("admin","admin"), ("moderator","moderator"), ("member","member")), default="member")
    message = models.CharField(max_length=100, null=True, blank=True)
    approved = models.BooleanField(default=False)
    # 
    join_requested_at = models.DateTimeField(null=True, blank=True)

class Notifications(models.Model):
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.CharField(max_length=200)
    
    type = models.CharField(blank=True, null=True, max_length= 50)


# class RoomApprovalRequests(models.Model):
#     reqeusted_at = models.DateTimeField(auto_now_add=True)
#     reqeusted_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
#     room = models.ForeignKey(Room, on_delete=models.CASCADE)



class DownLoadTokens(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    file = models.ForeignKey(Files, on_delete=models.CASCADE)
    token = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.token