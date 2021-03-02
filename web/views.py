from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404

from core.models import Annotation, Label, ImageCollection, ROI

def index(request):
    annotation_users = User.objects.all()
    collections = ImageCollection.objects.all()
    labels = Label.objects.all()

    if request.GET.get("label"):
        label = get_object_or_404(Label, name=request.GET.get('label'))
        rois = list(ROI.objects.with_label(label))
    else:
        rois = ROI.objects.all()

    # TODO: Hook up annotator filter

    is_filtered = request.GET.get("label") or request.GET.get("annotator")

    return render(request, "web/index.html", {
        "annotation_users": annotation_users,
        "labels": labels,
        "is_filtered": is_filtered,
        "collections": collections,
        "rois": rois,
        "roi_count": len(rois),
    })
