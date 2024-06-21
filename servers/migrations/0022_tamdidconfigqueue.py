# Generated by Django 5.0.6 on 2024-06-21 09:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('servers', '0021_msgendofconfig'),
    ]

    operations = [
        migrations.CreateModel(
            name='TamdidConfigQueue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usage_limit', models.IntegerField()),
                ('expire_time', models.IntegerField()),
                ('user_limit', models.IntegerField()),
                ('price', models.IntegerField()),
                ('sent_to_user', models.IntegerField(default=0)),
                ('pay_status', models.PositiveSmallIntegerField(default=0)),
                ('config', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='servers.configsinfo')),
            ],
        ),
    ]
