# Generated by Django 5.0.6 on 2024-06-27 12:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custumers', '0014_customer_restrict'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='first_name',
            field=models.CharField(max_length=25),
        ),
        migrations.AlterField(
            model_name='customer',
            name='username',
            field=models.CharField(max_length=32, null=True),
        ),
    ]
