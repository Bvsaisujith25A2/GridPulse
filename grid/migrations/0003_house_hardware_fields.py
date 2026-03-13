from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('grid', '0002_seed_categories')]

    operations = [
        migrations.AddField(
            model_name='house',
            name='arduino_pin',
            field=models.PositiveSmallIntegerField(default=13),
        ),
        migrations.AddField(
            model_name='house',
            name='hardware_enabled',
            field=models.BooleanField(default=False),
        ),
    ]