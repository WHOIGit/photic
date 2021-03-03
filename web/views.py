from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404

from core.models import Annotation, Label, ImageCollection, ROI

def index(request):
    annotation_users = User.objects.all()
    collections = ImageCollection.objects.all()
    labels = Label.objects.all()

    requested_label = request.GET.get('label')
    requested_collection = request.GET.get('collection')

    qs = ROI.objects

    if requested_collection:
        qs = qs.filter(collections__name=requested_collection)

    if requested_label:
        if requested_label == 'unlabeled':
            rois = qs.unlabeled()
        else:
            label = get_object_or_404(Label, name=requested_label)
            rois = qs.with_label(label)
    else:
        rois = qs.all()

    # TODO: Hook up annotator filter

    is_filtered = requested_label is not None

    return render(request, "web/index.html", {
        "annotation_users": annotation_users,
        "labels": labels,
        "is_filtered": is_filtered,
        "collections": collections,
        "rois": rois,
        "roi_count": len(rois),
    })
