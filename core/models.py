import os
from datetime import datetime
import json

from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models import F
from django.db.models.expressions import Window, ValueRange
from django.db.models.functions import LastValue

from django.utils import timezone

from PIL import Image


class ROIQuerySet(models.QuerySet):
    def with_label(self, label):
        label_id = label.id
        winner = Annotation.objects.get_queryset().\
            winner_window().order_by('roi_id', 'winner').values('roi_id', 'winner').distinct()
        roi_sql, roi_params = self.query.sql_with_params()
        winner_sql, winner_params = winner.query.sql_with_params()
        params = roi_params + winner_params
        return self.raw(f"""
           SELECT a.* FROM ({roi_sql}) a, ({winner_sql}) b
           WHERE a.id = b.roi_id
           AND %s = (
               SELECT label_id
               FROM core_annotation c
               WHERE c.id = b.winner)
           ORDER BY a.height DESC
        """, [*params, label_id])

    def with_cached_label(self, label):
        return self.filter(winning_annotation__label=label)

    def winning_annotations(self):
        """ returns the winning annotation for each ROI in the queryset """
        all_annotations = Annotation.objects.get_queryset()
        winner = all_annotations.\
            winner_window().order_by('roi_id', 'winner').values('roi_id', 'winner').distinct()
        winner_sql, winner_params = winner.query.sql_with_params()
        roi_sql, roi_params = self.query.sql_with_params()
        ann_sql, _ = all_annotations.query.sql_with_params()
        return Annotation.objects.raw(f"""
            SELECT a.* FROM ({ann_sql}) a, ({roi_sql}) b, ({winner_sql}) c
            WHERE b.id = c.roi_id
            AND a.roi_id = c.roi_id
            AND a.id = c.winner
            ORDER BY a.roi_id
        """, roi_params + winner_params)

    def unlabeled(self):
        return self.exclude(id__in=Annotation.objects.values_list('roi__id', flat=True))


class ROIManager(models.Manager):
    def get_queryset(self):
        return ROIQuerySet(self.model, using=self._db)

    def create_or_update_roi(self, path, collection=None):
        if not path.endswith('.png') and not path.endswith('.jpg'):
            raise NameError(f'{path} is not the path to a ROI image')
        roi_id = os.path.basename(path)[:-4]  # we know it ends with a 3-character image extension

        with transaction.atomic():
            try:
                roi = self.get(roi_id=roi_id)
                if roi.path != path:
                    roi.path = path
                    roi.save()
                if collection is not None:
                    if not roi.collections.filter(id=collection.id).exists():
                        roi.collections.add(collection)
            except ROI.DoesNotExist:
                with Image.open(path) as image:
                    width, height = image.size
                roi = self.create(roi_id=roi_id, width=width, height=height, path=path)
                if collection is not None:
                    roi.collections.add(collection)
        return roi

    def with_label(self, label):
        return self.get_queryset().with_label(label)

    def unlabeled(self):
        return self.get_queryset().unlabeled()


class ROI(models.Model):
    roi_id = models.CharField(max_length=255, unique=True)
    width = models.IntegerField()
    height = models.IntegerField()
    path = models.CharField(max_length=512)
    winning_annotation = models.ForeignKey('Annotation', on_delete=models.CASCADE, null=True,\
                                           related_name='associated_roi')

    objects = ROIManager()

    @property
    def image_type(self):
        _, ext = os.path.splitext(self.path)
        return ext[1:]

    def assign_label(self, label, user):  # does not save
        return Annotation.objects.create_or_verify(self, label, user)

    @property
    def tags(self):
        tags = [[a.label.name, a.user.username, a.timestamp.strftime("%m/%d/%Y, %H:%M:%S")] for a in self.annotations.all()]

        # The conversion to json is important. Without it, we get [['1','2','3']]. With it we get double quotes
        #   [["1","2","3"]]. This is necessary for the HTML on the front end to work properly
        return json.dumps(tags)

    def cache_winning_annotation(self):
        winning_annotation = list(self.annotations.winner())
        if winning_annotation:
            self.winning_annotation = winning_annotation[0]
            self.save()

    def __str__(self):
        return self.roi_id


class Label(models.Model):
    name = models.CharField(max_length=255, unique=True)
    folder_name = models.CharField(max_length=512)
    description = models.TextField()
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Annotator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    power = models.IntegerField(default=1)

    def __str__(self):
        return f'{self.user.username} ({self.power})'


class AnnotationQuerySet(models.QuerySet):
    def winner_window(self):
        return self.annotate(
            winner=Window(
                expression=LastValue(F('id')),
                partition_by=(F('roi')),
                order_by=[F('user_power'), F('timestamp')],
                frame=ValueRange()
            )
        )

    def winner(self):
        winner = self.winner_window().order_by('winner').values('winner').distinct()
        sql, params = winner.query.sql_with_params()
        return self.raw(f"""
           SELECT a.* FROM core_annotation a, ({sql}) b
           WHERE a.id = b.winner
        """, params)


class AnnotationManager(models.Manager):
    def get_queryset(self):
        return AnnotationQuerySet(self.model, using=self._db)

    def create_annotation(self, roi, label, user):
        return self.create(roi=roi, label=label, user=user, user_power=user.annotator.power)

    def create_or_verify(self, roi, label, user):
        with transaction.atomic():
            try:
                annotation = self.get(roi=roi, label=label, user=user)
                annotation.verify()
                annotation.save()
                created = False
            except Annotation.DoesNotExist:
                annotation = self.create_annotation(roi=roi, label=label, user=user)
                created = True
            roi.cache_winning_annotation()
            return annotation, created

    def winner(self):
        return self.get_queryset().winner()


class Annotation(models.Model):
    roi = models.ForeignKey(ROI, on_delete=models.CASCADE, related_name='annotations')
    label = models.ForeignKey(Label, on_delete=models.CASCADE, related_name='annotations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='annotations')
    user_power = models.IntegerField(default=1)
    timestamp = models.DateTimeField(auto_now_add=True)
    verifications = models.IntegerField(default=0)

    objects = AnnotationManager()

    def verify(self):
        self.verifications += 1
        self.timestamp = timezone.now()
        self.user_power = self.user.annotator.power # update user power
        return self

    def __str__(self):
        return f'{self.roi.roi_id} ({self.label.name}) by {self.user.username}'


class ImageCollection(models.Model):
    name = models.CharField(max_length=255, unique=True)
    rois = models.ManyToManyField(ROI, related_name="collections")

    def __str__(self):
        return self.name

