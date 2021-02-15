from django.dispatch import receiver
from django.db.models.signals import post_save

from django.contrib.auth.models import User

from .models import Annotator


@receiver(post_save, sender=User, dispatch_uid='user.create_annotator')
def create_annotator(sender, instance, created, **kw):
    if created:
        Annotator.objects.create(user=instance)


@receiver(post_save, sender=User, dispatch_uid='user.save_annotator')
def save_annotator(sender, instance, **kw):
    instance.annotator.save()