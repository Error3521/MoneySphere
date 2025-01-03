# Generated by Django 5.1.3 on 2024-11-23 19:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ms', '0009_transfer_user_delete_userprofile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='currency',
            field=models.ForeignKey(blank=True, default=1, null=True, on_delete=django.db.models.deletion.SET_NULL, to='ms.currency'),
        ),
        migrations.AlterField(
            model_name='transfer',
            name='transaction_date',
            field=models.DateField(),
        ),
    ]
