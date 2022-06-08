import csv
import os
from django.core.management.base import BaseCommand, CommandError

from core.models import Label


class Command(BaseCommand):
    help = 'change labels'

    def add_arguments(self, parser):
        parser.add_argument('-m','--mapping', type=str, help='Path to csv of mapping of old and new label names')

    def handle(self, *args, **options):
        # handle arguments
        mapping_csv = options['mapping']
        # validate arguments
        if not mapping_csv:
            raise CommandError('Input mapping file not specified')
        if not os.path.exists(mapping_csv):
            raise CommandError('specified file does not exist')
        with open(mapping_csv,'r') as csvin:
            with open('/rois/output.csv', 'w') as csvout:
                writer = csv.writer(csvout, lineterminator='\n')
                reader = csv.reader(csvin)

                all = []
                row = next(reader)
                row.append('Status')
                all.append(row)

                for row in reader:
                    res = 0
                    res = Label.objects.filter(name=row[0]).update(name=row[1])
                    row.append(res)
                    all.append(row)

                writer.writerows(all)
        print("Status of update in /rois/output.csv.")
