# Generated by Django 2.2 on 2020-06-22 00:45

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TestModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('even_number', models.IntegerField()),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField(blank=True, null=True)),
                ('limit', models.IntegerField()),
                ('last_modified', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
