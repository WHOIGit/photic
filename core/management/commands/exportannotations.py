import json

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import ROI, Annotation


class Command(BaseCommand):
    help = 'export annotations'

    def add_arguments(self, parser):
        parser.add_argument('collection', type=str, help='image collection to export')
        parser.add_argument('output_file', type=str, help='output filename')
        parser.add_argument('--all', dest='all', action='store_true',
                            help='export all annotations (not just winning ones)')
        parser.set_defaults(all=False)

    def handle(self, *args, **options):
        # handle arguments
        collection_name = options['collection']
        export_all = options['all']
        output_file = options['output_file']

        if not output_file.endswith('.json'):
            output_file = f'{output_file}.json'

        if export_all:
            annotations = Annotation.objects.filter(roi__collections__name=collection_name)
        else:
            annotations = []
            rois = ROI.objects.filter(collections__name=collection_name)
            for roi in rois:
                if roi.winning_annotation:
                    annotations.append(roi.winning_annotation)

        annotation_records = []

        for a in annotations:
            annotation_records.append({
                'roi': a.roi.roi_id,
                'label': a.label.name,
                'annotator': a.user.username,
                'power': a.user_power,
                'timestamp': a.timestamp.isoformat('T', 'seconds'),
                'verifications': a.verifications,
            })

        with open(output_file, 'w') as outfile:
            json.dump({
                'collection': collection_name,
                'export_time': timezone.now().isoformat('T', 'seconds'),
                'annotations': annotation_records,
            }, outfile)
