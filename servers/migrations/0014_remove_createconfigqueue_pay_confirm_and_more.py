# Generated by Django 5.0.6 on 2024-05-30 10:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('servers', '0013_rename_userid_createconfigqueue_custumer'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='createconfigqueue',
            name='pay_confirm',
        ),
        migrations.AddField(
            model_name='createconfigqueue',
            name='pay_status',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
