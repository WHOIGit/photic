import os
import shutil

from django.core.management.base import BaseCommand

from core.models import ROI


class Command(BaseCommand):
    help = 'export training set'

    def add_arguments(self, parser):
        parser.add_argument('collection', type=str, help='image collection to export as training set')
        parser.add_argument('directory', type=str, help='destination directory')

    def handle(self, *args, **options):
        # handle arguments
        collection_name = options['collection']
        destination_root_directory = options['directory']

        winning_annotations = ROI.objects.filter(collections__name=collection_name).\
            winning_annotations()

        destination_directories = {}  # keyed by label

        for a in winning_annotations:
            label_name = a.label.name
            destination_directory = destination_directories.get(label_name)
            if destination_directory is None:
                destination_directory = os.path.join(destination_root_directory, label_name)
                os.makedirs(destination_directory, exist_ok=True)
                destination_directories[label_name] = destination_directory
            shutil.copy(a.roi.path, destination_directory)
