from django.urls import path

from . import views

app_name = 'web'
urlpatterns = [
    path('', views.index, name='index'),
    path('api/roi_annotations', views.roi_annotations, name='annotations'),
]