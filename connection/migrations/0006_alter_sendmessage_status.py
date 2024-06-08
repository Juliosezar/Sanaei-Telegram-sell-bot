# Generated by Django 5.0.6 on 2024-06-07 18:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('connection', '0005_alter_sendmessage_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sendmessage',
            name='status',
            field=models.CharField(choices=[('Succes', 'Succes'), ('Created', 'Created'), ('Pending', 'Pending'), ('Faild', 'Faild'), ('Timeout', 'Timeout'), ('Cancelled', 'Cancelled'), ('Banned', 'Banned')], default='Created', max_length=15),
        ),
    ]
