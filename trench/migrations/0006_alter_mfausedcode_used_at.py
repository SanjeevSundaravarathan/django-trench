# Generated by Django 4.1.5 on 2023-01-10 09:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trench", "0005_mfausedcode_remove_mfamethod_primary_is_active_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mfausedcode",
            name="used_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="used_at"),
        ),
    ]
