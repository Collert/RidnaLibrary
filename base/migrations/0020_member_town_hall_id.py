import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0019_alter_loan_due_date_alter_loan_loan_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="member",
            name="town_hall_id",
            field=models.CharField(
                blank=True,
                help_text="The staff member's 6-digit Town Hall ID (their kiosk ID). Their time in the admin is logged as a Town Hall shift. Leave empty to not track it.",
                max_length=6,
                validators=[django.core.validators.RegexValidator("^\\d{6}$", "Enter the 6-digit Town Hall ID.")],
                verbose_name="Town Hall ID",
            ),
        ),
    ]
