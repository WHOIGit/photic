from django.shortcuts import render

from core.models import Annotation
from core.models import Label
from django.contrib.auth.models import User

def index(request):
    # TODO: Group by ROI...
    annotations = Annotation.objects.all()

    annotation_users = User.objects.all()

    labels = Label.objects.all()

    # TODO: Hook up to "winning" label filter"
    if request.GET.get("label"):
        annotations = annotations.filter(label__name=request.GET.get("label"))

    # TODO: Hook up annotator filter

    is_filtered = request.GET.get("label") or request.GET.get("annotator")

    return render(request, "web/index.html", {
        "annotations": annotations,
        "annotation_users": annotation_users,
        "labels": labels,
        "is_filtered": is_filtered,
    })
