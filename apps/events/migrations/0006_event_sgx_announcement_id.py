from django.db import migrations, models
from django.db.models import Q


def backfill_sgx_announcement_id(apps, schema_editor):
    """Copy sgx_announcement_id from details_json into the new column on
    existing OTHER rows so the new UniqueConstraint can hold."""
    Event = apps.get_model("events", "Event")
    for e in Event.objects.filter(view_category="OTHER").iterator():
        ann_id = (e.details_json or {}).get("sgx_announcement_id") or ""
        if ann_id and ann_id != e.sgx_announcement_id:
            e.sgx_announcement_id = ann_id
            e.save(update_fields=["sgx_announcement_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0005_event_ex_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="sgx_announcement_id",
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
        migrations.RunPython(backfill_sgx_announcement_id, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name="event",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="event",
            constraint=models.UniqueConstraint(
                condition=~Q(view_category="OTHER"),
                fields=("company", "event_type", "event_date"),
                name="event_uniq_per_type_date_nonother",
            ),
        ),
        migrations.AddConstraint(
            model_name="event",
            constraint=models.UniqueConstraint(
                condition=Q(view_category="OTHER") & ~Q(sgx_announcement_id=""),
                fields=("company", "sgx_announcement_id"),
                name="event_uniq_other_by_announcement_id",
            ),
        ),
    ]
