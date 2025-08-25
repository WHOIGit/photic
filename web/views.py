import csv
import os
from pprint import pprint
import json

from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.models import Annotation, Label, ImageCollection, ROI, Annotator
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

import logging

log = logging.getLogger(__name__)

def index(request):
    annotation_users = User.objects.all()
    collections = ImageCollection.objects.all()

    requested_label = request.GET.get('label')
    requested_collection = request.GET.get('collection')

    is_filtered = requested_label is not None

    return render(request, "web/index.html", {
        "annotation_users": annotation_users,
        "is_filtered": is_filtered,
        "collections": collections
    })

SORTBY_OPTIONS = {
    'HEIGHT_ASC': ['height', 'roi_id'],
    'HEIGHT_DESC': ['-height', 'roi_id'],
    'ROI_ID_ASC': ['roi_id'],
    'ROI_ID_DESC': ['-roi_id'],
}

def export_roi_list(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden()

    collection = request.POST.get('collection')
    if not collection:
        return HttpResponseBadRequest()

    rois = ROI.objects \
        .filter(collections__name=collection) \
        .order_by("roi_id") \
        .values_list('collections__name', 'winning_annotation__label__name', 'path')

    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{collection}-rois.csv"'},
    )

    writer = csv.writer(response)
    writer.writerow(["Collection", "Label", "Filename", "Path"])
    for roi in rois:
        writer.writerow([
            roi[0],
            roi[1],
            os.path.basename(roi[2]),
            os.path.dirname(roi[2]),
        ])

    return response

@require_POST
def roi_list(request):
    requested_label = request.POST.get('label')
    requested_collection = request.POST.get('collection')
    sortby = request.POST.get('sortby')
    
    page = request.POST.get('page', 1)
    
    sortby_query = SORTBY_OPTIONS[sortby]

    qs = ROI.objects

    if requested_collection:
        qs = qs.filter(collections__name=requested_collection)

    if requested_label:
        if requested_label == 'unlabeled':
            rois = qs.unlabeled()
        else:
            label = get_object_or_404(Label, name=requested_label)
            rois = qs.with_cached_label(label)
    else:
        rois = qs.all()

    rois = rois.order_by(*sortby_query)
    roi_count = rois.count()
    rois_list = rois.values_list('id', 'path')

    paginator = Paginator(rois_list, 1000)
    
    try:
        roi_page = paginator.page(page)
    except PageNotAnInteger:
        roi_page = paginator.page(1)
    except EmptyPage:
        roi_page = paginator.page(paginator.num_pages)

    roi_records = [{
        'id': rid,
        'path': path,
    } for rid, path in roi_page]

    return JsonResponse({
        'rois': roi_records,
        'roi_count': roi_count,
        'page_num':roi_page.number,
        'has_next_page': roi_page.has_next(),
    })

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
        'roi_id': roi.roi_id,
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


@require_POST
def get_labels(request):
    collection_name = request.POST.get('collection')

    if collection_name is None:
        labels = Label.objects.all().order_by('name')
    else:
        rc = get_object_or_404(ImageCollection, name=collection_name)
        labels = rc.labels(check_if_has_winning=True) # This is currently our switch to enable/disable skipping empty labels

    return JsonResponse({
        'labels': labels,
    })


@require_POST
def get_collections(request):
    collections = ImageCollection.objects.all()

    return JsonResponse({
        'collections': [collection.name for collection in collections],
    })


@require_POST
def move_or_copy_to_collection(request):
    body = json.loads(request.body.decode("utf-8"))

    collection_name = body['collection_name']
    delete_from_collection_name = body['delete_from_collection_name']
    rois = body['rois']

    collection_created = None
    collection = ImageCollection.objects.filter(name=collection_name).first()
    if not collection:
        collection = ImageCollection.objects.create(name=collection_name)
        collection_created = collection_name

    if delete_from_collection_name:
        delete_from_collection = get_object_or_404(ImageCollection, name=delete_from_collection_name)

    for roi_id in rois:
        roi = get_object_or_404(ROI, id=roi_id)
        collection.rois.add(roi)

        if delete_from_collection_name:
            delete_from_collection.rois.remove(roi)

    return JsonResponse({
        'success': True,
        'collection_created': collection_created
    })


def api_winning_annotations(request, collection_name):
    output = ROI.objects.filter(collections__name=collection_name).\
        values_list('roi_id', 'winning_annotation__label__name', 'winning_annotation__user__username',
                    'winning_annotation__timestamp', 'winning_annotation__verifications')
    # non-Pandas CSV generation
    lines = ['roi_id,label,annotator,timestamp,verifications\n']
    lines += [','.join(map(str, row)) + '\n' for row in output if row[1] is not None]
    # response as attachment CSV file
    response = HttpResponse(lines, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{collection_name}_annotations.csv"'
    return response

