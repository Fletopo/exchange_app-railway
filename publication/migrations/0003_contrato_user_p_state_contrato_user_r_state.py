# Generated by Django 5.1.2 on 2024-12-25 19:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('publication', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contrato',
            name='user_p_state',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='contrato',
            name='user_r_state',
            field=models.BooleanField(default=False),
        ),
    ]
