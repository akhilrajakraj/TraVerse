from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_auditlogentry"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="auditlogentry",
            old_name="core_audit_user_id_4a5d2c_idx",
            new_name="core_auditl_user_id_688426_idx",
        ),
    ]
