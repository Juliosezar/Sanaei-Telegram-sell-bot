# Generated by Django 5.0.6 on 2024-06-27 10:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0003_alter_adminlog_timestamp_alter_configlog_timestamp_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adminlog',
            name='timestamp',
            field=models.IntegerField(default=1719482444),
        ),
        migrations.AlterField(
            model_name='configlog',
            name='timestamp',
            field=models.IntegerField(default=1719482444),
        ),
        migrations.AlterField(
            model_name='customerlog',
            name='timestamp',
            field=models.IntegerField(default=1719482444),
        ),
    ]
