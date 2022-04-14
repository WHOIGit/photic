import csv
import os

from tqdm import tqdm

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from core.models import ROI, Annotation, ImageCollection, Label

class Command(BaseCommand):
    help = 'import rois'

    def add_arguments(self, parser):
        parser.add_argument('csv', type=str, help='file containing relative image path, label, and score')
        parser.add_argument('root', type=str, help='root directory in the container for relative paths')
        parser.add_argument('-c', '--collection', type=str, help='image collection to create or add images to')
        parser.add_argument('-u', '--user', type=str, help='username for any created annotations (user must exist)')

    def handle(self, *args, **options):
        csv_path = options['csv']
        root_path = options['root']
        collection_name = options.get('collection')
        username = options.get('user')
        if not os.path.exists(csv_path):
            raise CommandError(f'csv not found at {csv_path}')
        if not os.path.exists(root_path) and os.path.isdir(root_path):
            raise CommandError(f'root directory not found at {root_path}')
        if not username:
            raise CommandError('username must be specified with -u')
        try:
            user = User.objects.get(username=username)
        except:
            raise CommandError(f'unable to retrieve user {username}')
        collection = None
        if collection_name is not None:
            collection, created = ImageCollection.objects.get_or_create(name=collection_name)
        labels_handled = {}
        rows = []
        with open(csv_path) as fin:
            reader = csv.DictReader(fin)
            for row in reader:
                rows.append(row)
        for row in tqdm(rows):
            image_path = row['image_path']
            image_abspath = os.path.join(root_path, image_path)
            if not os.path.exists(image_abspath):
                print(f'warning: no image found at {image_abspath}')
                continue
            class_label = row['class_label']
            if class_label in labels_handled:
                label = labels_handled[class_label]
            else:
                label, _ = Label.objects.get_or_create(name=class_label)
                labels_handled[class_label] = label
            image_id, _ = os.path.splitext(os.path.basename(image_path))
            roi = ROI.objects.create_or_update_roi(image_abspath, collection=collection)
            Annotation.objects.create_or_verify(roi, label, user)
