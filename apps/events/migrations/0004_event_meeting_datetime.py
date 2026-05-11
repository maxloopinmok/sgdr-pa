from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0003_event_event_datetime'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='meeting_datetime',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
