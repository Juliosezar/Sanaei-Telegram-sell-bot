# Generated by Django 5.0.6 on 2024-06-12 12:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0015_rename_userid_confirmpaymentqueue_custumer'),
    ]

    operations = [
        migrations.RenameField(
            model_name='confirmpaymentqueue',
            old_name='price',
            new_name='pay_price',
        ),
    ]
