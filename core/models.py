import os

from django.contrib.auth.models import User
from django.db import models
from django.db.models import F
from django.db.models.expressions import Window
from django.db.models.functions import LastValue

from django.utils import timezone

from PIL import Image


class ROIManager(models.Manager):
    def create_roi(self, path):
        if not path.endswith('.png'):
            raise NameError(f'{path} is not the path to a ROI image')
        roi_id = os.path.basename(path)[:-4]  # we know it ends ".png"
        image = Image.open(path)
        width, height = image.size
        return self.create(roi_id=roi_id, width=width, height=height, path=path)


class ROI(models.Model):
    roi_id = models.CharField(max_length=255, unique=True)
    width = models.IntegerField()
    height = models.IntegerField()
    path = models.CharField(max_length=512)

    objects = ROIManager()

    def __str__(self):
        return self.roi_id


class Label(models.Model):
    name = models.CharField(max_length=255, unique=True)
    folder_name = models.CharField(max_length=512)
    description = models.TextField()

    def __str__(self):
        return self.name


class Annotator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    power = models.IntegerField(default=1)

    def __str__(self):
        return f'{self.user.username} ({self.power})'


class AnnotationQuerySet(models.QuerySet):
    def with_winning_label(self, label):  # label = Label object
        winning_label = self.annotate(
            winning_label=Window(
                expression=LastValue(F('label')),
                partition_by=[F('roi')],
                order_by=[F('user_power'), F('timestamp')]
            )
        )
        sql, params = winning_label.query.sql_with_params()
        return self.raw("""
            SELECT * FROM ({}) a
            WHERE winning_label = %s
        """.format(sql), [*params, label.id])


class AnnotationManager(models.Manager):
    def get_queryset(self):
        return AnnotationQuerySet(self.model, using=self._db)

    def create_annotation(self, roi, label, user):
        return self.create(roi=roi, label=label, user=user, user_power=user.annotator.power)

    def create_or_verify(self, roi, label, user):
        try:
            annotation = self.get(roi=roi, label=label, user=user)
            annotation.verify()
            return annotation # does not save
        except Annotation.DoesNotExistError:
            return self.create_annotation(roi=roi, label=label, user=user)

    def with_winning_label(self, label):
        return self.get_queryset().with_winning_label(label)


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
        # does not save

    def __str__(self):
        return f'{self.roi.roi_id} ({self.label.name}) by {self.user.username}'


class ImageCollection(models.Model):
    name = models.CharField(max_length=255, unique=True)
    rois = models.ManyToManyField(ROI, related_name="collections")

    def __str__(self):
        return self.name

