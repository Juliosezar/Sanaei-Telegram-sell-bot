# Generated by Django 5.0.6 on 2024-06-28 11:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('connection', '0019_remove_endofconfigcounter_timestamp'),
    ]

    operations = [
        migrations.AddField(
            model_name='endofconfigcounter',
            name='timestamp',
            field=models.IntegerField(default=1719574430),
        ),
    ]
