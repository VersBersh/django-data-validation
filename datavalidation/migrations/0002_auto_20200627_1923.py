# Generated by Django 2.2 on 2020-06-27 19:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('datavalidation', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='validator',
            old_name='traceback',
            new_name='exc_traceback',
        ),
    ]