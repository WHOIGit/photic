# Generated by Django 3.1.6 on 2021-02-08 20:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20210208_2049'),
    ]

    operations = [
        migrations.AlterField(
            model_name='imagecollection',
            name='rois',
            field=models.ManyToManyField(related_name='collections', to='core.ROI'),
        ),
    ]