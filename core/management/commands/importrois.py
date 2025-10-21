import os
import boto3
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from core.models import ROI, Annotation, ImageCollection, Label
from services.s3_service import S3Service
from constants import StorageOrigin, ALLOWED_FILE_TYPES, S3_DELIMITER



class Command(BaseCommand):
    help = 'import rois'

    def add_arguments(self, parser):
        parser.add_argument('directory', type=str, help='directory (or prefix if using S3) containing images')
        parser.add_argument('-c','--collection', type=str, help='image collection to create or add images to')
        parser.add_argument('-b', '--bucket', type=str, help='the bucket when importing from S3')
        parser.add_argument('-u','--user', type=str, help='username for any created annotations (user must exist)')
        parser.add_argument('--include-rois', type=str, help='only import rois matching a comma separated list')
        parser.add_argument('--include-rois-file', type=str, help='only import rois found in a file (new line separated)')
        parser.add_argument('--prefix', type=str, help='a prefix to prepend to all ROIs used with --include-rois or --include-rois-file')

        origin_choices = [StorageOrigin.LOCAL.value, StorageOrigin.S3.value,]
        parser.add_argument('-o','--origin', type=str, choices=origin_choices, default='local', help='storage type to use (local or s3)')

    def is_roi_included(self, filename, included_rois):
        if not included_rois:
            return True

        is_included = any(roi in filename for roi in included_rois)

        return is_included

    def scan_local(self, directory, included_rois=None):
        unlabeled = []
        labeled = {}
        folders = []

        # First, loop through the directory and sort entries into unlabeled files and top level folders
        for entry in os.listdir(directory):
            name, ext = os.path.splitext(entry)
            if ext in ALLOWED_FILE_TYPES and self.is_roi_included(name, included_rois):
                unlabeled.append(entry)
                continue

            path = os.path.join(directory, entry)
            if os.path.isdir(path):
                folders.append(entry)
                continue

        # For each top level folder, use that as the label and get all the files inside
        for folder in folders:
            labeled[folder] = []

            path = os.path.join(directory, folder)
            for entry in os.listdir(path):
                name, ext = os.path.splitext(entry)
                if ext not in ALLOWED_FILE_TYPES or not self.is_roi_included(name, included_rois):
                    continue

                labeled[folder].append(entry)

        return unlabeled, labeled

    def scan_s3(self, s3_client, bucket, directory, included_rois=None):
        unlabeled = []
        labeled = {}
        folders = []

        # Intentionally using "list_objects" here instead of "list_objects_v2" to work around potential permission or
        #   feature restrictions when using VAST as the backend storage resource
        paginator = s3_client.get_paginator('list_objects')

        for page in paginator.paginate(Bucket=bucket, Delimiter=S3_DELIMITER, Prefix=directory):
            for cp in page.get("CommonPrefixes", []):
                folder = cp.get("Prefix")

                if directory != "":
                    folder = folder.removeprefix(directory)

                folders.append(folder)

            for obj in page.get("Contents", []):
                filename = obj['Key']

                # Ignore folders and files within folders
                if filename.endswith('/'):
                    continue

                # Remove the directory/path if there is one
                if directory != "":
                    filename = filename.removeprefix(directory)

                name, ext = os.path.splitext(filename)
                if ext not in ALLOWED_FILE_TYPES or not self.is_roi_included(name, included_rois):
                    continue

                unlabeled.append(filename)

        for folder in folders:
            key = folder.rstrip("/")
            labeled[key] = []
            prefix = os.path.join(directory, folder)

            for page in paginator.paginate(Bucket=bucket, Delimiter=S3_DELIMITER, Prefix=prefix):

                for obj in page.get("Contents", []):
                    filename = obj['Key'].removeprefix(prefix)

                    # Ignore subfolders and files within subfolders
                    if "/" in filename:
                        continue

                    # Remove the directory/path if there is one
                    if directory != "":
                        filename = filename.removeprefix(directory)

                    name, ext = os.path.splitext(filename)
                    if ext not in ALLOWED_FILE_TYPES or not self.is_roi_included(name, included_rois):
                        continue

                    labeled[key].append(filename)

        return unlabeled, labeled

    def handle(self, *args, **options):
        # handle arguments
        directory = options['directory']
        collection_name = options.get('collection')
        username = options.get('user')
        origin = options.get('origin')
        bucket = options.get('bucket')
        rois_list = options.get('include_rois')
        rois_file = options.get('include_rois_file')
        prefix = options.get('prefix') or ''
        s3_client = S3Service.get_client() if origin == StorageOrigin.S3.value else None

        # validate arguments

        if rois_list and rois_file:
            raise CommandError('the include-rois and include-rois-file arguments cannot be used at the same time')

        if rois_file:
            path = Path(rois_file)
            if not path.exists() or not path.is_file():
                raise CommandError(f"file not found: {path}")

        # Only verify the path physically exists when using local storage
        if origin == StorageOrigin.LOCAL.value and not os.path.exists(directory):
            raise CommandError('specified directory does not exist')

        # When using S3 for storage, a bucket is required
        if origin == StorageOrigin.S3.value and (bucket or "") == "":
            raise CommandError('bucket must be specified')

        # For S3, if the user wants to look in root, the options are a bit unclear so we should allow them to an empty
        #   string (with ""), or a single slash. However, as far as AWS is concerned, directory in this case should be
        #   set to an empty string (slash will not work properly)
        if origin == StorageOrigin.S3.value and directory == "/":
            directory = ""

        # For S3, if the user entered a directory, it must end in a trailing slash. Rather than require it, we can just
        #   add one if it's not there
        if origin == StorageOrigin.S3.value and directory != "" and not directory.endswith("/"):
            directory += "/"

        # Load any filters
        included_rois = []

        if rois_list:
            included_rois = [prefix + item.strip() for item in rois_list.split(',') if item.strip()]

        if rois_file:
            path = Path(rois_file)
            try:
                with path.open('r') as f:
                    included_rois = [prefix + line.strip() for line in f if line.strip()]
            except Exception as e:
                raise CommandError(f"could not read file {rois_file}: {e}")

        user = None
        if username:
            try:
                user = User.objects.get(username=username)
            except:
                raise CommandError(f'unable to retrieve user {username}')

        collection = None
        if collection_name is not None:
            collection, _ = ImageCollection.objects.get_or_create(name=collection_name)

        if origin == StorageOrigin.S3.value:
            unlabeled, labeled = self.scan_s3(s3_client, bucket, directory, included_rois=included_rois)
        else:
            unlabeled, labeled = self.scan_local(directory, included_rois=included_rois)

        if len(labeled) > 0 and not user:
            raise CommandError('labeled ROIs found but no username specified')

        print(f'found {len(unlabeled)} unlabeled images and {len(labeled)} label directories')

        # now create ROI records in the database
        if len(unlabeled) > 0:
            print(f'importing {len(unlabeled)} unlabeled ROIs...')
            for roi_filename in unlabeled:
                path = os.path.join(directory, roi_filename)
                _ = ROI.objects.create_or_update_roi(path, collection=collection, origin=origin, bucket=bucket, s3_client=s3_client)

        for label_name, rois in labeled.items():
            print(f'importing {len(rois)} ROIs labeled "{label_name}"...')
            label, _ = Label.objects.get_or_create(name=label_name)
            for roi_filename in rois:
                roi_path = os.path.join(directory, label_name, roi_filename)
                roi = ROI.objects.create_or_update_roi(roi_path, collection=collection, origin=origin, bucket=bucket, s3_client=s3_client)
                Annotation.objects.create_or_verify(roi, label, user)
