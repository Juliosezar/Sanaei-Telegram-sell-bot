# Generated by Django 5.0.6 on 2024-06-07 18:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('connection', '0003_alter_sendmessage_uuid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sendmessage',
            name='status',
            field=models.CharField(choices=[('Succes', 'Succes'), ('Created', 'Created'), ('Pending', 'Pending'), ('Faild', 'Faild'), ('Timeout', 'Timeout'), ('Cancelled', 'Cancelled'), ('Banned', 'Banned')], max_length=15),
        ),
    ]
