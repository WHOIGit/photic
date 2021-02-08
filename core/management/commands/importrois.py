import os

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from core.models import ROI, Annotation, ImageCollection, Label

class Command(BaseCommand):
    help = 'import rois'

    def add_arguments(self, parser):
        parser.add_argument('directory', type=str, help='directory containing images')
        parser.add_argument('-c','--collection', type=str, help='image collection to create or add images to')
        parser.add_argument('-u','--user', type=str, help='username for any created annotations (user must exist)')

    def handle(self, *args, **options):
        # handle arguments
        directory = options['directory']
        collection_name = options.get('collection')
        username = options.get('user')
        # validate arguments
        if not os.path.exists(directory):
            raise CommandError('specified directory does not exist')
        user = None
        if username:
            try:
                user = User.objects.get(username=username)
            except:
                raise CommandError(f'unable to retrieve user {username}')
        collection = None
        if collection_name is not None:
            collection, created = ImageCollection.objects.get_or_create(
                name=collection_name)
        # scan directory and one level of subdirectories
        def scan(dir):
            return [n[:-4] for n in os.listdir(dir) if n.endswith('.png')]
        unlabeled = scan(directory)
        labeled = {}
        for n in os.listdir(directory):
            if os.path.isdir(os.path.join(directory,n)):
                label = n
                label_dir_path = os.path.join(directory, n)
                labeled[label] = scan(label_dir_path)
        if len(labeled) > 0 and not user:
            raise CommandError('labeled ROIs found but no username specified')
        print(f'found {len(unlabeled)} images and {len(labeled)} label directories')
        # now create ROI records in the database
        for roi_name in unlabeled:
            roi = ROI.objects.create_roi(path)
            if collection:
                collection.rois.add(roi)
        for label_name, rois in labeled.items():
            label, created = Label.objects.get_or_create(name=label_name)
            for roi_name in rois:
                roi_path = os.path.join(directory, label_name, roi_name + '.png')
                roi = ROI.objects.create_roi(roi_path)
                if collection:
                    collection.rois.add(roi)
                Annotation.objects.create_annotation(roi, label, user)


