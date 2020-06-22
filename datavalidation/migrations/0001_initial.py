# Generated by Django 2.2 on 2020-06-22 00:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='ValidationMethod',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('method_name', models.CharField(max_length=80)),
                ('description', models.TextField(max_length=100)),
                ('is_class_method', models.BooleanField()),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='contenttypes.ContentType')),
            ],
            options={
                'unique_together': {('content_type', 'method_name')},
                'index_together': {('content_type', 'method_name')},
            },
        ),
        migrations.CreateModel(
            name='ValidationSummary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exc_type', models.CharField(blank=True, default=None, max_length=250, null=True)),
                ('traceback', models.TextField(blank=True, default=None, max_length=2000, null=True)),
                ('exc_obj_pk', models.PositiveIntegerField(blank=True, null=True)),
                ('passed', models.BooleanField(blank=True, null=True)),
                ('num_passed', models.PositiveIntegerField(blank=True, null=True)),
                ('num_failed', models.PositiveIntegerField(blank=True, null=True)),
                ('num_na', models.PositiveIntegerField(blank=True, null=True)),
                ('num_allowed_to_fail', models.PositiveIntegerField(blank=True, null=True)),
                ('last_run_time', models.DateTimeField(auto_now=True)),
                ('method', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='datavalidation.ValidationMethod')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FailingObjects',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_pk', models.PositiveIntegerField()),
                ('comment', models.TextField(db_index=True, max_length=250, unique=True)),
                ('allowed_to_fail', models.BooleanField(default=False)),
                ('valid', models.BooleanField()),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='contenttypes.ContentType')),
                ('method', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='results', to='datavalidation.ValidationMethod')),
            ],
            options={
                'unique_together': {('content_type', 'object_pk', 'method')},
                'index_together': {('content_type', 'object_pk', 'method')},
            },
        ),
    ]
