from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404

from core.models import Annotation, Label, ImageCollection, ROI

def index(request):
    annotation_users = User.objects.all()
    collections = ImageCollection.objects.all()
    labels = Label.objects.all()

    requested_label = request.GET.get('label')

    if requested_label:
        if requested_label == 'unlabeled':
            rois = ROI.objects.unlabeled()
        else:
            label = get_object_or_404(Label, name=requested_label)
            rois = list(ROI.objects.with_label(label))
    else:
        rois = ROI.objects.all()

    # TODO: Hook up annotator filter

    is_filtered = requested_label or request.GET.get("annotator")

    return render(request, "web/index.html", {
        "annotation_users": annotation_users,
        "labels": labels,
        "is_filtered": is_filtered,
        "collections": collections,
        "rois": rois,
        "roi_count": len(rois),
    })
