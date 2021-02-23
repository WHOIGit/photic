from django.shortcuts import render

from core.models import Annotation

def index(request):
    # TODO: Group by ROI...
    annotations = Annotation.objects.all()

    return render(request, "web/index.html", {
        "annotations": annotations,
    })
