# Generated by Django 3.1.6 on 2021-02-05 22:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20210205_2158'),
    ]

    operations = [
        migrations.AddField(
            model_name='annotation',
            name='user_power',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='annotation',
            name='verifications',
            field=models.IntegerField(default=0),
        ),
    ]
