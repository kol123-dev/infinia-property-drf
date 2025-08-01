# Generated by Django 5.2.3 on 2025-06-13 13:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('landlords', '0001_initial'),
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SmsMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField()),
                ('status', models.CharField(choices=[('queued', 'Queued'), ('sent', 'Sent'), ('failed', 'Failed'), ('delivered', 'Delivered')], default='queued', max_length=20)),
                ('external_message_id', models.CharField(blank=True, max_length=100, null=True)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('landlord', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sms_messages', to='landlords.landlord')),
                ('recipients', models.ManyToManyField(related_name='received_sms', to='tenants.tenant')),
            ],
        ),
    ]
