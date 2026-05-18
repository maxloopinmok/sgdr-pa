from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0003_company_listings_json"),
    ]

    operations = [
        migrations.AddField(
            model_name="company",
            name="is_active",
            field=models.BooleanField(db_index=True, default=True),
        ),
    ]
