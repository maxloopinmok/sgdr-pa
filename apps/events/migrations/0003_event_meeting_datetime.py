from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0002_alter_event_event_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='meeting_datetime',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
