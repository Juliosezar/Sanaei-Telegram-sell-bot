# Generated by Django 5.0.6 on 2024-05-29 20:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('servers', '0010_createconfigqueue_sent_to_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='createconfigqueue',
            name='pay_confirm',
            field=models.BooleanField(default=False),
        ),
    ]
