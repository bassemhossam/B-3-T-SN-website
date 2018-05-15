"""socialNetworkFinal URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,re_path
from django.conf.urls import include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.urlpatterns import format_suffix_patterns
from SN import views

urlpatterns = [
    path('admin/', admin.site.urls, ),
    path('SN/', include('SN.urls')),
    path('usersxml/', views.UsersList.as_view()),
    re_path(r'^usersxml/(?P<pk>[0-9]+)/', views.SNUserDetail.as_view()),
    path('postsxml/', views.PostsList.as_view()),

]

urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'html', 'xml'])

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

