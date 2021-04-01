import json

from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.models import Annotation, Label, ImageCollection, ROI, Annotator
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

import logging

log = logging.getLogger(__name__)

def home(request):
    numbers_list = range(1, 1000)
    page = request.GET.get('page', 1)
    paginator = Paginator(numbers_list, 20)
    try:
        numbers = paginator.page(page)
    except PageNotAnInteger:
        numbers = paginator.page(1)
    except EmptyPage:
        numbers = paginator.page(paginator.num_pages)
    return render(request, 'web/home.html', {'numbers': numbers})

def index(request):
    annotation_users = User.objects.all()
    collections = ImageCollection.objects.all()
    labels = Label.objects.order_by('name')

    requested_label = request.GET.get('label')
    requested_collection = request.GET.get('collection')

    is_filtered = requested_label is not None

    return render(request, "web/index.html", {
        "annotation_users": annotation_users,
        "labels": labels,
        "is_filtered": is_filtered,
        "collections": collections
    })


def roi_list(request):
    requested_label = request.POST.get('label')
    requested_collection = request.POST.get('collection')
    page = request.POST.get('page', 1)

    qs = ROI.objects.order_by('-height')

    if requested_collection:
        qs = qs.filter(collections__name=requested_collection)

    if requested_label:
        qs = qs.filter(collections__name=requested_collection)
        if requested_label == 'unlabeled':
            rois = qs.unlabeled()
        else:
            label = get_object_or_404(Label, name=requested_label)
            rois = qs.with_cached_label(label)
    else:
        rois = qs.all()

    roi_count = len(rois)
    paginator = Paginator(rois, 100)

    try:
        rois = paginator.page(page)
    except PageNotAnInteger:
        rois = paginator.page(1)
    except EmptyPage:
        rois = paginator.page(paginator.num_pages)


    roi_records = [{
        'id': r.id,
        'path': r.path,
    } for r in rois]

    return JsonResponse({
        'rois': roi_records,
        'roi_count': roi_count,
        'has_next_page': rois.has_next(),
    })
# class ROIView(ListView):
#     model = ROI
#     paginate_by = 5
#     context_object_name = 'roi'
#     template_name = 'blog/articles.html'

@require_POST
def roi_annotations(request):
    roi_id = request.POST.get('roi_id')  # here roi_id is the pk of the ROI table
    roi = get_object_or_404(ROI, id=roi_id)
    annotations = roi.annotations.all()
    annotation_records = [{
        'label_id': a.label.id,
        'label': a.label.name,
        'annotator_id': a.user.id,
        'annotator': a.user.username,
        'time': a.timestamp,
        'verifications': a.verifications,
    } for a in annotations]
    table_rows = [
        [a.label.name, a.user.username, a.timestamp.isoformat('T', 'minutes'), a.verifications]
        for a in annotations
    ]

    return JsonResponse({
        'annotations': annotation_records,
        'rows': table_rows,
    })


@require_POST
def create_label(request):
    label_name = request.POST.get('name')

    label, created = Label.objects.get_or_create(name=label_name)
    

    return JsonResponse({
        'label': label_name,
        'created': created,
    })


@require_POST
def create_or_verify_annotations(request):
    body = json.loads(request.body.decode("utf-8"))

    # FIXME should just use the logged-in user as the annotator
    try:
        annotator_name = body['annotator']
        annotator = User.objects.get(username=annotator_name)
    except KeyError:
        annotator = request.user

    batch = body['annotations']

    rois = {}  # roi objects by ID
    labels = {}  # label objects by name

    # cache all relevant objects

    for annotation_record in batch:
        roi_id = annotation_record['roi_id']
        roi = rois.get(roi_id)
        if roi is None:
            roi = get_object_or_404(ROI, id=roi_id)
            rois[roi_id] = roi
        label_name = annotation_record['label']
        label = labels.get(label_name)
        if label is None:
            labels[label_name] = get_object_or_404(Label, name=label_name)

    # now create/verify the annotations

    return_records = []

    for annotation_record in batch:
        roi = rois[annotation_record['roi_id']]
        label = labels[annotation_record['label']]

        annotation, created = Annotation.objects.create_or_verify(roi, label, annotator)

        return_records.append({
            'roi_id': roi.id,
            'label_name': label.name,
            'created': created
        })

    return JsonResponse({
        'annotations': return_records
    })
