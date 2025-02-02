# Generated by Django 4.1.5 on 2023-01-10 15:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("trench", "0004_alter_mfamethod_id_mfamethod_unique_user_is_primary_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="MFABackupCodes",
            fields=[
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        related_name="mfa_backup_codes",
                        serialize=False,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="user",
                    ),
                ),
                ("_values", models.TextField(verbose_name="backup codes")),
            ],
            options={
                "verbose_name": "MFA Backup Code",
                "verbose_name_plural": "MFA Backup Codes",
            },
        ),
        migrations.CreateModel(
            name="MFAUsedCode",
            fields=[
                (
                    "id",
                    models.CharField(
                        default=uuid.uuid4,
                        max_length=255,
                        primary_key=True,
                        serialize=False,
                        verbose_name="id",
                    ),
                ),
                ("code", models.CharField(max_length=6, verbose_name="code")),
                (
                    "used_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="used_at"),
                ),
                ("expires_at", models.DateTimeField(verbose_name="expires_at")),
                ("method", models.CharField(max_length=255, verbose_name="method")),
            ],
            options={
                "verbose_name": "MFA Last Used Code",
                "verbose_name_plural": "MFA Last Used Codes",
            },
        ),
        migrations.RemoveConstraint(
            model_name="mfamethod",
            name="primary_is_active",
        ),
        migrations.RemoveField(
            model_name="mfamethod",
            name="_backup_codes",
        ),
        migrations.AlterField(
            model_name="mfamethod",
            name="id",
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AddConstraint(
            model_name="mfamethod",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(("is_primary", True), ("is_active", True)),
                    ("is_primary", False),
                    _connector="OR",
                ),
                name="primary_is_active",
            ),
        ),
        migrations.AddField(
            model_name="mfausedcode",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="mfa_used_codes",
                to=settings.AUTH_USER_MODEL,
                verbose_name="user",
            ),
        ),
    ]
