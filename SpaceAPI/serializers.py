from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from . import models
from rest_framework import serializers
from rest_framework.serializers import ValidationError
from datetime import datetime
from django.contrib.auth.hashers import make_password, check_password



def formatDateTime(datetime):
    return [
        datetime.strftime("%d %b %Y"),
        datetime.strftime("%I:%M %p")
    ]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['username'] = user.username
        token["image"] = user.profile.url if user.profile else None
        return token



class CreateRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Room
        # fields = "__all__"
        fields = ("room_name", "room_type", "description", "logo", "room_pass")
        extra_kwargs = {"room_pass":{"write_only": True}}

    def create(self, validated_data):
        password = None
        try:
            if(validated_data.get("room_type") == "pvt"):
                if validated_data.get("room_pass") is None:
                    raise serializers.ValidationError(detail={"details":"While creating private rooms, an extra field 'room_pass' is required."})
                else:
                    password = validated_data["room_pass"]
                    
            new_room = models.Room.objects.create(
                room_name = validated_data.get("room_name"),
                room_type= validated_data.get("room_type"),
                author= self.context['request'].user,
                description= validated_data.get("description"),
                logo = validated_data.get("logo")
            )
            if password:
                new_room.room_pass = make_password(password)
            new_room.save()
            return new_room
        except Exception as e:
            raise e




class UserSerializerForRooms(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    def get_profile(self, user):
        return user.profile.url if user.profile else None 
    class Meta:
        model = models.CustomUser
        fields = ("id", "first_name", "last_name","username","profile" )


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Room
        exclude = ('room_pass', )
        read_only_fields = ['id', 'author', 'room_size', 'used_space', 'created_at']

    created_at = serializers.SerializerMethodField()
    author = UserSerializerForRooms()
    tags = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()
    members_count = serializers.SerializerMethodField()

    def get_logo(self, obj):
        return obj.logo.url if obj.logo else None 

    def get_members_count(self, obj):
        return models.RoomMembers.objects.filter(room = obj, approved=True).count()

    def get_tags(self, s):
        return [i.name for i in s.tags.all()]

    def get_created_at(self, s):
        return formatDateTime(s.created_at)


class JoinedRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RoomMembers
        exclude = ("id","user")

    joined_at = serializers.SerializerMethodField()
    join_requested_at = serializers.SerializerMethodField()

    room = RoomSerializer()

    def get_joined_at(self, o):
        return formatDateTime(o.joined_at)
    
    def get_join_requested_at(self, o):
        if o.join_requested_at:
            return formatDateTime(o.join_requested_at)

    

class SerializeRoomMembers(serializers.ModelSerializer):
    user = UserSerializerForRooms()
    
    class Meta:
        model = models.RoomMembers
        fields = ("user", "joined_at","role", "approved",)

















class FileSerializer(serializers.ModelSerializer):

    last_modified = serializers.SerializerMethodField()
    uploaded_at = serializers.SerializerMethodField()

    def get_uploaded_at(self, s):
        return formatDateTime(s.uploaded_at)
    
    def get_last_modified(self, obj):
        return formatDateTime(obj.last_modified)

    class Meta:
        model = models.Files
        exclude = ("room", )

class FileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Files
        fields = ("visibility", )



class RoomSearchSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    def get_author(self, obj):
        return obj.author.get_full_name()
    class Meta:
        model = models.Room
        fields = ("id", "author", "room_name" ,"room_type")


class RegisterUserSerializer(serializers.Serializer):
    # username = serializers.CharField(max_length=50, required=True)
    password = serializers.CharField(max_length=50, required=True)
    first_name = serializers.CharField(max_length=50, required=True)
    last_name = serializers.CharField(max_length=50, required=True)
    email = serializers.EmailField(max_length=100, required=True)

    def validate_password(self, value):
        if(len(value) < 6):
            raise ValidationError("Password must be at least 6 characters.")
        return value
    

    def validate_username(self, value):
        if models.CustomUser.objects.filter(username= value).exists():
            raise ValidationError("username already taken.")
        return value
    
    def validate_email(self, value):
        if models.CustomUser.objects.filter(email= value).exists():
            raise ValidationError("email already exists.")
        return value
    
    def create(self, validated_data):
        user = models.CustomUser.objects.create(
            username= validated_data["email"],
            first_name= validated_data["first_name"],
            last_name= validated_data["last_name"],
            email= validated_data["email"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CustomUser
        fields = "__all__"
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
            "email": {"required": True}
            }

    def validate(self, obj):
        return obj
    
    def create(self,validated_data):
        if(len(validated_data["password"]) < 6):
            raise ValidationError({"password":["Password must be at least 6 characters"]})
        if models.CustomUser.objects.filter(username= validated_data["username"]).exists():
            raise ValidationError({"username":["username already exists"]})
        if models.CustomUser.objects.filter(email= validated_data["email"]).exists():
            raise ValidationError({"email":["email already exists"]})
             
        user = models.CustomUser.objects.create(
            username= validated_data["username"],
            first_name= validated_data["first_name"],
            last_name= validated_data["last_name"],
            email= validated_data["email"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class UploadFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Files
        fields = serializers.ALL_FIELDS


