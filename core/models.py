from django.contrib.auth.models import User
from django.db import models


class ROI(models.Model):
    roi_id = models.CharField(max_length=255)
    width = models.IntegerField()
    height = models.IntegerField()
    path = models.CharField(max_length=512)

    def __str__(self):
        return self.roi_id


class Label(models.Model):
    name = models.CharField(max_length=255)
    folder_name = models.CharField(max_length=512)
    description = models.TextField()

    def __str__(self):
        return self.name


class Annotator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    power = models.IntegerField(default=1)


class Annotation(models.Model):
    roi = models.ForeignKey(ROI, on_delete=models.CASCADE, related_name='annotations')
    label = models.ForeignKey(Label, on_delete=models.CASCADE, related_name='annotations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='annotations')
    timestamp = models.DateTimeField(auto_now_add=True)


class ImageCollection(models.Model):
    name = models.CharField(max_length=255)
    rois = models.ManyToManyField(ROI, related_name="rois")

    def __str__(self):
        return self.name

