from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404, redirect, reverse

from .forms import UserForm
from .utils import staff_required


@staff_required
def index(request):
    return render(request, "manage/index.html")


@staff_required
def users(request):
    return render(request, "manage/users.html")


@staff_required
def get_users(request):
    users = User.objects.all().values("id", "first_name", "last_name", "email", "username", "is_active", "is_staff")

    return JsonResponse({
        "data": list(users)
    })

@staff_required
def edit_user(request, id=None):
    if id:
        user = get_object_or_404(User, pk=id)
    else:
        user = User()

    form = UserForm(instance=user)

    if request.method == "POST":
        form = UserForm(request.POST, instance=user)

        if form.is_valid():
            user = form.save(commit=False)

            new_password = form.cleaned_data["new_password"]
            if new_password:
                user.password = make_password(new_password)

            user.save()

            return redirect(reverse("manage:users"))

    return render(request, "manage/edit_user.html", {
        'user': user,
        'form': form,
    })


@staff_required
@require_POST
def delete_user(request, id): #no longer used by front end
    user = get_object_or_404(User, pk=id)
    user.delete()

    return JsonResponse({
        "success": True
    })


@staff_required
@require_POST
def deactivate_user(request, id):
    user = get_object_or_404(User, pk=id)
    user.is_active = False
    user.save()
    
    return JsonResponse({
        "success": True
    })

@staff_required
@require_POST
def activate_user(request, id):
    user = get_object_or_404(User, pk=id)
    user.is_active = True
    user.save()
    
    return JsonResponse({
        "success": True
    })
