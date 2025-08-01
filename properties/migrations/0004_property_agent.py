# Generated by Django 5.2.3 on 2025-07-01 11:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agents', '0004_agent_additional_contacts_agent_city_and_more'),
        ('properties', '0003_property_description_property_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='agent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='managed_properties', to='agents.agent'),
        ),
    ]
