from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0002_company_listed_date_raw"),
    ]

    operations = [
        migrations.AddField(
            model_name="company",
            name="listings_json",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
