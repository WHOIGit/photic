import csv
import os

from django.core.management.base import BaseCommand, CommandError
from core.models import Annotation, ROI, Label
from django.db import connection
from django.db.models import Count

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
                reader = csv.reader(csvin)
                row = next(reader)

                for row in reader:
                    res = 0
                    res = Label.objects.filter(name=row[0]).update(name=row[1])
                    if res == 0:
                        print("Error: Source Label, " + row[0] + " not found!")
                        continue
                    # Number of ROIs affected with this particular Label change
                    i = Annotation.objects.filter(label__name__contains=row[1]).count()
                    print(row[0] + " -> " + row[1] + ", affected ROIs: " + str(i))
        print("Done.")

