# Generated by Django 5.0.6 on 2024-05-27 17:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0002_payment_config_in_queue'),
    ]

    operations = [
        migrations.CreateModel(
            name='Prices',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usage_limit', models.PositiveIntegerField()),
                ('expire_limit', models.PositiveIntegerField()),
                ('price', models.PositiveIntegerField()),
            ],
        ),
    ]
