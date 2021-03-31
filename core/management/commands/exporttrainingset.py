import os
import shutil

from django.core.management.base import BaseCommand

from core.models import ROI


class Command(BaseCommand):
    help = 'export training set'

    def add_arguments(self, parser):
        parser.add_argument('collection', type=str, help='image collection to export as training set')
        parser.add_argument('directory', type=str, help='destination directory')
        parser.add_argument('--move', dest='move', action='store_true',
                            help='move files rather than copying them')
        parser.set_defaults(move=False)

    def handle(self, *args, **options):
        # handle arguments
        collection_name = options['collection']
        destination_root_directory = options['directory']
        move = options['move']

        winning_annotations = ROI.objects.filter(collections__name=collection_name).\
            winning_annotations()

        destination_directories = {}  # keyed by label

        for i, a in enumerate(winning_annotations):
            label_name = a.label.name
            destination_directory = destination_directories.get(label_name)
            if destination_directory is None:
                print(f'found ROIs labeled "{label_name}"')
                destination_directory = os.path.join(destination_root_directory, label_name)
                os.makedirs(destination_directory, exist_ok=True)
                destination_directories[label_name] = destination_directory
            roi_path = a.roi.path
            if move:
                roi_filename = os.path.basename(roi_path)
                destination_path = os.path.join(destination_directory, roi_filename)
                shutil.move(roi_path, destination_path)
                a.roi.path = destination_path  # record new location of ROI
                a.roi.save()
            else:
                shutil.copy(roi_path, destination_directory)

        print(f'exported {i+1} ROIs')
