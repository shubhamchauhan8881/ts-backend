
from django.contrib import admin
from django.urls import path, include, re_path
from django.contrib.auth.models import User
from django.conf import settings
from django.conf.urls.static import static
from . import views


urlpatterns =[
    path('admin/', admin.site.urls),
    # re_path(r'^app(?:/.*)?$', views.home),
    path('api/v1/', include('SpaceAPI.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)