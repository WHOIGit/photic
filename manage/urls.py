from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm

app_name = 'manage'
urlpatterns = [
    path('', views.index, name='index'),
    path(
        'login',
        auth_views.LoginView.as_view(
            template_name="manage/login.html",
            authentication_form=LoginForm,
        ),
        name="login"
    ),
    path('logout', auth_views.logout_then_login, name="logout"),
    path('users', views.users, name="users"),
    path('edit-user/<int:id>', views.edit_user, name="edit-user"),
    path('edit-user', views.edit_user, name="create-user"),
    path('api/get-users', views.get_users, name="get-users"),
    # path('api/delete-user/<int:id>', views.delete_user, name="delete-user"),
    path('api/deactivate-user/<int:id>', views.deactivate_user, name="deactivate-user"),
    path('api/activate-user/<int:id>', views.activate_user, name="activate-user"),
]
