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
        parser.add_argument('-f', '--flag', type=str, help='indicate whether annotation is manual or auto. Defaulted to manual, if not specified')
        parser.add_argument('-cl', '--classifier', type=str, help='if auto annotated, indicate associated classifier')

    def handle(self, *args, **options):
        # handle arguments
        directory = options['directory']
        collection_name = options.get('collection')
        username = options.get('user')
        flag = options.get('flag')
        classifier = options.get('classifier') or ''
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

        auto = False
        # If flag not specified, auto defaulted to False
        if flag:
            if not(flag == "auto" or flag == "manual"):
                raise CommandError('values of flag should either be auto or manual')
            if flag == "auto":
                auto = True
                if not classifier:
                    raise CommandError('classifier must be specified if auto annotated')
            # if flag == manual, auto already set to False


        # scan directory and one level of subdirectories
        def scan(dir):
            result = []
            for fn in os.listdir(dir):
                name, ext = os.path.splitext(fn)
                if ext not in ['.png', '.jpg']:
                    continue
                result.append(fn)
            return result
        unlabeled = scan(directory)
        labeled = {}
        for n in os.listdir(directory):
            if os.path.isdir(os.path.join(directory, n)):
                label = n
                label_dir_path = os.path.join(directory, n)
                labeled[label] = scan(label_dir_path)
        if len(labeled) > 0 and not user:
            raise CommandError('labeled ROIs found but no username specified')
        print(f'found {len(unlabeled)} unlabeled images and {len(labeled)} label directories')
        # now create ROI records in the database
        print(f'importing {len(unlabeled)} unlabeled ROIs...')
        for roi_filename in unlabeled:
            path = os.path.join(directory, roi_filename)
            roi = ROI.objects.create_or_update_roi(path, collection=collection)
        for label_name, rois in labeled.items():
            print(f'importing {len(rois)} ROIs labeled "{label_name}"...')
            label, created = Label.objects.get_or_create(name=label_name)
            for roi_filename in rois:
                roi_path = os.path.join(directory, label_name, roi_filename)
                roi = ROI.objects.create_or_update_roi(roi_path, collection=collection)
                Annotation.objects.create_or_verify(roi, label, user, auto, classifier)



