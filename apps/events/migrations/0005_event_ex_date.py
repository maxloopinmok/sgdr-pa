from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0004_event_meeting_datetime'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='ex_date',
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
    ]
