# Generated by Django 5.0.6 on 2024-05-29 20:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0010_alter_confirmpaymentqueue_config_uuid'),
    ]

    operations = [
        migrations.RenameField(
            model_name='confirmpaymentqueue',
            old_name='amount',
            new_name='price',
        ),
    ]
