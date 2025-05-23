from django.shortcuts import HttpResponse
from rest_framework import generics
from . import models
from . import serializers
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, JSONParser
from math import ceil
import json
from django.contrib.auth.hashers import make_password, check_password
from uuid import uuid4
from django.conf import settings
from .permissions import IsRoomOwner
from django.utils import timezone

def formatDateTime(datetime):
    return [
        datetime.strftime("%d %b %Y"),
        datetime.strftime("%I:%M %p")
    ]


class GetRoomRecommendations(generics.ListAPIView):
    serializer_class = serializers.RoomSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    authentication_classes = [JWTAuthentication]
    
    def get_queryset(self):
        # if self.request.user.is_authenticated:
        #     # filter room suggestions as per user settings
        # else:
        #     # return random room....
        return models.Room.objects.all()


class UserRooms(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = serializers.RoomSerializer
    parser_classes = [MultiPartParser, JSONParser]

    def get_queryset(self):
        return models.Room.objects.filter(author=self.request.user)

    def create(self, request, *args, **kwargs):
        self.serializer_class = serializers.CreateRoomSerializer
        return super().create(request, *args, **kwargs)





class RoomDetailedApiView(APIView):
    permission_classes = [IsAuthenticated, IsRoomOwner]
    authentication_classes = [JWTAuthentication]

    def get(self, request, pk):
        try:
            room = models.Room.objects.get(pk=pk)

            data = {
                "room": serializers.RoomSerializer(room).data,
                "is_admin" :False,
                "is_member": False,
            }
            # check if room owner
            if room.author == request.user:
                data["is_admin"] = True
                data["role"] = "admin"
                return Response(data=data)

            # not admin check if user is member of this room
            m = models.RoomMembers.objects.filter(user = request.user, room = room)
            if m.exists():
                # user is memebr of the room
                data["is_member"] = True
                temp = serializers.JoinedRoomSerializer(m[0]).data
                temp.pop("room")
                data["membership_info"] = temp

            return Response(data=data)
        
        except models.Room.DoesNotExist:
            return Response(data= {"details": [f"invalid room id {pk}, No Room exists with given room id."]}, status=status.HTTP_404_NOT_FOUND)
    
    def patch(self, req, pk):
        room = models.Room.objects.get(pk=pk)
        self.check_object_permissions(req, room)
        room_data = serializers.RoomSerializer(room, data=req.data, partial = True)
        if room_data.is_valid():
            room_data.save()
            return Response(status= status.HTTP_200_OK)
        


class RetrieveUserRooms(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = serializers.RoomSerializer

    def get_queryset(self):
        return models.Room.objects.filter(author= self.request.user)


class RoomSearchAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        room_name = request.GET.get('query')
        if not room_name:
            return Response(status= status.HTTP_400_BAD_REQUEST, data={'details': "url param 'query' is required"})
        res = models.Room.objects.filter(room_name__icontains=room_name, make_visible_on_search = True)
        return Response(data = serializers.RoomSearchSerializer(res, many=True).data, status= status.HTTP_200_OK)

 
class Register(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        slz = serializers.RegisterUserSerializer(data=request.data)
        if slz.is_valid():
            slz.save()
            return Response(data={"details": ["user registration successfull."]}, status=status.HTTP_201_CREATED)
        else:
            return Response(data=slz.errors, status = status.HTTP_400_BAD_REQUEST)


class UserUpdate(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = serializers.CustomUserSerializer
    # queryset = models.CustomUser.objects.all()

    def get_object(self):
        return self.request.user


class CheckUsernameAvailability(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        user =  get_user_model()
        username = request.GET.get("q")
        
        if username is None:
            stt= status.HTTP_400_BAD_REQUEST
            data={'details': ["url param q (query) is required"]}
        elif len(username) < 3:
            stt= status.HTTP_400_BAD_REQUEST
            data={'details': ["username cannot be less than 3 characters."]}
        else:
            stt= status.HTTP_200_OK
            data= {"available" : not user.objects.filter(username=username).exists() }
        return Response(data=data, status= stt )
 

class FileManage(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk, file_id):
        try:
            room = models.Room.objects.get(author=request.user, pk=pk)
            if request.query_params.get('many') == 'true':
                delete_list = json.loads( request.query_params.get('list'))
                f = models.Files.objects.filter(room=room, id__in=delete_list)
                f.delete()
            else:
                file = models.Files.objects.get(room= room, pk=file_id)
                room.used_space -= file.file_size
                room.save()
                file.delete()
            return Response(status=status.HTTP_200_OK)

        except models.Files.DoesNotExist:
           return Response(data = {"details":"file does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except models.Room.DoesNotExist:
            return Response(data = {"details": "room does not exist"}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk, file_id):
        file = models.Files.objects.get(pk= file_id)
        if request.user == file.owner  or request.user == file.room.author:
            sr =serializers.FileUpdateSerializer(file, data = request.data, partial=True)
            if sr.is_valid():
                sr.save()
                return Response(status=status.HTTP_200_OK)

            else:
                Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"details": ["You are not authorized to perform this action."]})


class FileUpload(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [ MultiPartParser ]

    def get(self, request, pk, *args, **kwargs):
        room = models.Room.objects.get(pk=pk)
        files = models.Files.objects.filter(room= room)
        if(request.user != room.author):
            files = files.filter(visibility = True)
        
        return Response(data= serializers.FileSerializer(files, many=True).data)

    def post(self, request, pk, *args, **kwargs):
        try:
            room = models.Room.objects.get(author=request.user, pk=pk)
            file_obj = request.data['file']

            if(room.used_space + ceil(file_obj.size)) <= room.room_size:
                file = models.Files.objects.create(
                    room= room,
                    file= file_obj,
                    file_name= file_obj.name,
                    file_size= ceil(file_obj.size),
                    file_type= "file",
                    owner = request.user
                )
                file.save()
                room.used_space += ceil(file_obj.size)
                room.save()
                return Response( data = serializers.FileSerializer(file).data, status=status.HTTP_201_CREATED)
            else:
                # room do not have storage left
                return Response( data= {"details": "file size exceeds the storage available for this room."} ,status=status.HTTP_400_BAD_REQUEST)
        except models.Room.DoesNotExist:
            return Response(data= {"details": f"invalid room id {pk}, No Room exists with given room id."}, status=status.HTTP_404_NOT_FOUND)



class CheckPass(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        room = models.Room.objects.get(pk=pk)

        password = request.data.get("password")
        if not password:
            return Response(data={"details": "room password is required"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # verify password
            if check_password(password, room.room_pass):
                return Response(status=status.HTTP_202_ACCEPTED)
        return Response(status=status.HTTP_401_UNAUTHORIZED)



class JoinRoom(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        room = models.Room.objects.get(pk=pk)
        if(room.author == request.user):
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"details": ["room admin can't be a memeber."]})

        rm = models.RoomMembers.objects.filter(user=request.user, room=pk)
        if rm.exists() and rm[0].approved:
            return Response(data={"details":["user already is a member of this room."]}, status=status.HTTP_400_BAD_REQUEST) 
        else:
            m = models.RoomMembers(
                room= room,
                user= request.user,
            )

            if(room.room_type == "pub"):
                m.approved = True
                m.save()
                return Response(data={"details": ["Joined successfully"]}, status=status.HTTP_202_ACCEPTED)
            
            elif room.room_type == "pvt" and check_password(request.data.get("password"), room.room_pass):
                # password not verified dont not join user to the room
                m.approved = True
                m.save()
                return Response(data={"details": ["Joined succesfully."]}, status=status.HTTP_202_ACCEPTED)
            
        return Response(data={"details": "Invalid room password."}, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pk):
        re = models.RoomMembers.objects.filter(user=request.user, room=pk)
        if re.exists():
            re.delete()
            return Response(data={"details": "Exited"})
        return Response()

    def get(self, request, pk):
        # check if user is member of room
        temp = models.RoomMembers.objects.filter(user= request.user, room = pk, approved=True)
        if temp.exists():
            return Response(data={"ok":True, "joined_at": serializers.formatDateTime(temp[0].joined_at)} ) 
        else:
            return Response(data={"ok":False})



class ManageRoomApprovals(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        room = models.Room.objects.get(pk=pk)
        if request.user == room.author:
            return Response()
        
        if not models.RoomMembers.objects.filter( user= request.user, room= room).exists():
            models.RoomMembers.objects.create(
                room= room,
                user= request.user,
                join_requested_at = timezone.now()
            )
            # models.Notifications.objects.create(
            #     type="JoinReq",
            #     user = room.author,
            #     message = f"{request.user.get_full_name()} requested to join {room.room_name}"
            # )
            return Response(data={"details": "Request sent to room creator."}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={"details": "Already requested"} , status=status.HTTP_200_OK)


def geneRateDownloadToken(file_instance, user_instance):
    token = str(uuid4())
    models.DownLoadTokens.objects.create(
        user= user_instance,
        file= file_instance,
        token= token
    )
    return token


def download(request, token):
    d = models.DownLoadTokens.objects.get(token=token)
    d.delete()
    with open(f"{settings.BASE_DIR}/{d.file.file}", "rb") as f:
        response = HttpResponse(f, content_type='text/binary')
        response['Content-Disposition'] = f'attachment; filename={d.file.file_name}'
        return response


class GetDownloadToken(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, file_id):
        # check if user if either memeber of room or creator of room then only allow to download the file
        # else if rooom is public allow to download the file
        download_token = ""
        try:
            files = models.Files.objects.get(id=file_id)
            # chec room type:
            if( files.room.room_type == 'pub' or files.room.author == request.user or models.RoomMembers.objects.filter(room= files.room, user= request.user, approved=True).exists()):
                download_token = geneRateDownloadToken(files, request.user)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED, data={"details": "you are not authorized to download this file."})
            return Response(data={"downloadToken": download_token})
        except(models.Files.DoesNotExist):
            return Response(status=status.HTTP_404_NOT_FOUND, data={"details": 'file does not exists.'})




class UserJoinedRooms(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = serializers.JoinedRoomSerializer

    def get_queryset(self):
        return models.RoomMembers.objects.filter(user = self.request.user)
    

class ManageRoomMembers(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    
    def get(sef, request, pk):
        rm = models.RoomMembers.objects.filter(room = pk)
        return Response(data= serializers.SerializeRoomMembers(rm, many= True).data)