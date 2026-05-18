from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0004_company_is_active"),
    ]

    operations = [
        migrations.AddField(
            model_name="company",
            name="country",
            field=models.CharField(blank=True, max_length=64),
        ),
    ]
