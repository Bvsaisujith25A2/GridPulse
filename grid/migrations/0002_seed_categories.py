from django.db import migrations

CATEGORIES = [
    ('CAT-PP', 'Power Plant'),
    ('CAT-GS', 'Grid Substation'),
    ('CAT-DS', 'Distribution Substation'),
    ('CAT-DT', 'Distribution Transformer'),
    ('CAT-HS', 'House'),
    ('CAT-ID', 'Industry'),
]

def seed_categories(apps, schema_editor):
    Category = apps.get_model('grid', 'Category')
    for cat_id, cat_name in CATEGORIES:
        Category.objects.get_or_create(id=cat_id, defaults={'name': cat_name})

def remove_categories(apps, schema_editor):
    Category = apps.get_model('grid', 'Category')
    Category.objects.filter(id__in=[c[0] for c in CATEGORIES]).delete()

class Migration(migrations.Migration):
    dependencies = [('grid', '0001_initial')]
    operations = [
        migrations.RunPython(seed_categories, reverse_code=remove_categories),
    ]
