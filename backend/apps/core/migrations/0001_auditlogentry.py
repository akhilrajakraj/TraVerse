from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditLogEntry",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("action", models.CharField(db_index=True, max_length=50)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_log_entries",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Audit Log Entry",
                "verbose_name_plural": "Audit Log Entries",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="auditlogentry",
            index=models.Index(
                fields=["user", "action", "created_at"],
                name="core_audit_user_id_4a5d2c_idx",
            ),
        ),
    ]
