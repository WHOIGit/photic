from django.urls import path

from . import views

app_name = 'web'
urlpatterns = [
    path('', views.index, name='index'),
    path('api/roi_annotations', views.roi_annotations, name='annotations'),
    path('api/create_label', views.create_label, name='create_label'),
    path('api/roi_list', views.roi_list, name='roi_list'),
    path('api/create_or_verify_annotations', views.create_or_verify_annotations, name='create_or_verify_annotations'),
    path('api/move_or_copy_to_collection', views.move_or_copy_to_collection, name='move_or_copy_to_collection'),
    path('api/get_labels', views.get_labels, name='get_labels'),
    path('api/get_collections', views.get_collections, name='get_collections'),

    # external REST endpoints
    path('api/winning_annotations/<collection_name>', views.api_winning_annotations, name='winning_annotations'),
]
