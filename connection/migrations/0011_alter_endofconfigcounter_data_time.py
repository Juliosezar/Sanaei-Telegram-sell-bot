# Generated by Django 5.0.6 on 2024-06-25 11:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('connection', '0010_endofconfigcounter_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='endofconfigcounter',
            name='data_time',
            field=models.DateTimeField(default='1403-04-05 15:07:02.386722+03:30'),
        ),
    ]