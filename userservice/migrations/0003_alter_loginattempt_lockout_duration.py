# Generated by Django 4.1.7 on 2023-07-14 15:13

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("userservice", "0002_loginattempt_lockout_duration"),
    ]

    operations = [
        migrations.AlterField(
            model_name="loginattempt",
            name="lockout_duration",
            field=models.DurationField(default=15),
        ),
    ]
