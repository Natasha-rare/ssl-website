# Generated by Django 4.2 on 2023-07-11 18:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_user_game_status_user_rating_alter_user_created_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='image',
            field=models.ImageField(blank=True, default='users_images/default.png', null=True, upload_to='users_images'),
        ),
    ]
