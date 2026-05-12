from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("companies", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DailyBar",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("date", models.DateField(db_index=True)),
                ("open", models.DecimalField(decimal_places=4, max_digits=12)),
                ("high", models.DecimalField(decimal_places=4, max_digits=12)),
                ("low", models.DecimalField(decimal_places=4, max_digits=12)),
                ("close", models.DecimalField(decimal_places=4, max_digits=12)),
                ("volume", models.BigIntegerField()),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("company", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="daily_bars",
                    to="companies.company",
                )),
            ],
            options={
                "ordering": ["-date", "company__ticker"],
                "unique_together": {("company", "date")},
            },
        ),
        migrations.AddIndex(
            model_name="dailybar",
            index=models.Index(fields=["company", "-date"], name="prices_dail_company_b1aaff_idx"),
        ),
    ]
