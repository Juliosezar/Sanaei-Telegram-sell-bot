# Generated by Django 5.0.6 on 2024-05-30 09:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0014_alter_confirmpaymentqueue_image'),
    ]

    operations = [
        migrations.RenameField(
            model_name='confirmpaymentqueue',
            old_name='userid',
            new_name='custumer',
        ),
    ]
