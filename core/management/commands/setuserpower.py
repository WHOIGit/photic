from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'set user power'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='username (user must exist)')
        parser.add_argument('power', type=int, help='user power (integer, higher is more powerful)')

    def handle(self, *args, **options):
        # handle arguments
        username = options['username']
        power = options['power']
        # create the dataset
        try:
            user = User.objects.get(username=username)
        except:
            raise CommandError(f'unable to retrieve user {username}')
        user.annotator.power = power
        user.save()
