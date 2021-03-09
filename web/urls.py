from django.urls import path

from . import views

app_name = 'web'
urlpatterns = [
    path('', views.index, name='index'),
    path('api/roi_annotations', views.roi_annotations, name='annotations'),
    path('api/create_label', views.create_label, name='create_label'),
    path('api/create_or_verify_annotations', views.create_or_verify_annotations, name='create_or_verify_annotations'),
]
