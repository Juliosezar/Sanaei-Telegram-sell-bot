# Generated by Django 5.0.6 on 2024-06-08 08:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('servers', '0016_configsinfo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='createconfigqueue',
            name='sent_to_user',
            field=models.IntegerField(default=0),
        ),
    ]
