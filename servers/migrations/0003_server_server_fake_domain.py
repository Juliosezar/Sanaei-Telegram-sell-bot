# Generated by Django 5.0.6 on 2024-05-26 18:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('servers', '0002_server_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='server',
            name='server_fake_domain',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
