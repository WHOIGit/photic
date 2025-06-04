# define a management command that loops over every ROI in the database

import os

from django.core.management.base import BaseCommand, CommandError

from core.models import ROI

from ifcb.data.identifiers import parse

import requests

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-d', '--dashboard', type=str, help='base URL for the dashboard')

    def handle(self, *args, **options):
        dashboard_base_url = options.get('dashboard')
        if not dashboard_base_url:
            raise CommandError('Please provide a base URL for the dashboard using -d or --dashboard, e.g. "https://example.edu/"')
        if not dashboard_base_url.endswith('/'):
            dashboard_base_url += '/'
        # loop over every ROI in the database
        for roi in ROI.objects.all():
            # is this an IFCB ROI?
            if os.path.exists(roi.path):
                # Do not print anything normally - many paths are not IFCB images and will errors that cannot be fixed
                #   using this command
                #print(f"ROI {roi.path} already exists, skipping download.")
                continue
            try:
                pid = parse(roi.path)
            except ValueError:
                print(f"Unable to parse ROI path {roi.path}, skipping.")
                continue
            lid = pid['lid']
            roi_url = f"{dashboard_base_url}data/{lid}.jpg"
            # fetch the ROI data and write it to the ROI path
            roi_resp = requests.get(roi_url)
            if roi_resp.status_code == 404:
                print(f"ROI {lid} not found at {roi_url}, skipping.")
                continue
            roi_resp.raise_for_status()  # raise an error for bad responses
            roi_bytes = roi_resp.content
            os.makedirs(os.path.dirname(roi.path), exist_ok=True)
            with open(roi.path, 'wb') as f:
                f.write(roi_bytes)
            
            
        