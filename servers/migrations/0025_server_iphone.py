# Generated by Django 5.0.6 on 2024-06-29 16:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('servers', '0024_infinitcongislimit'),
    ]

    operations = [
        migrations.AddField(
            model_name='server',
            name='iphone',
            field=models.BooleanField(default=False),
        ),
    ]
