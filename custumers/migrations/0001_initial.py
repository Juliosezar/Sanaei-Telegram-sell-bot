# Generated by Django 5.0.6 on 2024-05-26 14:20

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('servers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('userid', models.IntegerField(primary_key=True, serialize=False, unique=True)),
                ('first_name', models.CharField(max_length=50)),
                ('username', models.CharField(max_length=50, unique=True)),
                ('wallet', models.IntegerField(default=0)),
                ('purchase_number', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Config',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('config_uuid', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('config_name', models.CharField(max_length=70)),
                ('change_location_number', models.IntegerField(default=0)),
                ('server', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='servers.server')),
                ('userid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='custumers.customer')),
            ],
        ),
    ]
