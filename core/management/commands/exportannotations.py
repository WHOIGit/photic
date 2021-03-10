import json

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import ROI


class Command(BaseCommand):
    help = 'export annotations'

    def add_arguments(self, parser):
        parser.add_argument('collection', type=str, help='image collection to export')

    def handle(self, *args, **options):
        # handle arguments
        collection_name = options['collection']

        winning_annotations = ROI.objects.filter(collections__name=collection_name).\
            winning_annotations()

        annotation_records = []
        for a in winning_annotations:
            annotation_records.append({
                'roi': a.roi.roi_id,
                'label': a.label.name,
                'annotator': a.user.username,
                'power': a.user_power,
                'timestamp': a.timestamp.isoformat('T', 'seconds'),
                'verifications': a.verifications,
            })

        print(json.dumps({
            'collection': collection_name,
            'export_time': timezone.now().isoformat('T', 'seconds'),
            'annotations': annotation_records,
        }))