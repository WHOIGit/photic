# Generated by Django 3.1.6 on 2021-02-05 21:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_annotator'),
    ]

    operations = [
        migrations.AlterField(
            model_name='annotator',
            name='power',
            field=models.IntegerField(default=1),
        ),
    ]
