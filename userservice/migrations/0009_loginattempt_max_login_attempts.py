# Generated by Django 4.1.7 on 2023-07-18 14:24

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("userservice", "0008_alter_loginattempt_lockout_duration"),
    ]

    operations = [
        migrations.AddField(
            model_name="loginattempt",
            name="max_login_attempts",
            field=models.PositiveIntegerField(default=3),
        ),
    ]
