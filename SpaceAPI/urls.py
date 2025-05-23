from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views


urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/register/', views.Register.as_view(), name=''),
    path('user/update/', views.UserUpdate.as_view(), name=''),
    path('user/rooms/', views.UserRooms.as_view(), name=''),
    path('user/rooms/joined/', views.UserJoinedRooms.as_view(), name=''),
    path('rooms/<int:pk>/', views.RoomDetailedApiView.as_view(), name=''),

    path('rooms/<int:pk>/join/', views.JoinRoom.as_view(), name=''),

    path("rooms/<int:pk>/files/", views.FileUpload.as_view(), name=''),

    path('rooms/', views.GetRoomRecommendations.as_view()),
    path("rooms/<int:pk>/files/<int:file_id>/", views.FileManage.as_view(), name=''),  
    path("rooms/<int:pk>/members/", views.ManageRoomMembers.as_view(), name=''),

    path("files/<int:file_id>/get-download-token/", views.GetDownloadToken.as_view(), name=''),
    path("download/<str:token>", views.download),
    path('rooms/search/', views.RoomSearchAPIView.as_view(), name='room_search'),
    path('user/rooms/<int:pk>/', views.RetrieveUserRooms.as_view()),
    path('user/username/', views.CheckUsernameAvailability.as_view(), name=''),

    # path("rooms/<int:pk>/approval/", views.ManageRoomApprovals.as_view(), name=''),
]
