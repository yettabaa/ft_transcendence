# Generated by Django 4.2.11 on 2024-06-02 18:36

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_alter_tokens_expired_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tokens',
            name='expired_date',
            field=models.DateTimeField(default=datetime.datetime(2024, 6, 2, 19, 36, 48, 550162, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='user',
            name='avatar_link',
            field=models.ImageField(default='media/avatars/default.png', upload_to='avatars'),
        ),
    ]
