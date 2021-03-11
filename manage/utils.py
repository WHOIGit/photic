from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def staff_required(function=None, redirect_url="/"):
    """
    Decorator for views that checks that the user is staff, redirecting to the homepage if necessary.
    """
    @login_required
    def _wrapper(request, *args, **kwargs):
        if request.user.is_staff:
            return function(request, *args, **kwargs)

        # Note that if the user isn't logged in at all, the login_required decorator will take
        #   take over and redirect the user back to the login screen
        return redirect(redirect_url)

    return _wrapper

