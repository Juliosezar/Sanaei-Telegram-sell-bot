# Generated by Django 5.0.6 on 2024-07-10 06:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0022_rename_curumer_count_offcodes_customer_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='useractiveoffcodes',
            name='used_time',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
