# Generated by Django 5.0.6 on 2024-05-27 17:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('servers', '0005_server_password_server_username'),
    ]

    operations = [
        migrations.RenameField(
            model_name='server',
            old_name='server_username',
            new_name='server_id',
        ),
    ]
