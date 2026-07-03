from django.core.management.base import BaseCommand
from api.models import Role, RequestCategory

class Command(BaseCommand):
    help = "Seed initial roles and request categories"
    def handle(self, *args, **options):
        self.stdout.write("Seeding roles...")
        roles = [
            {"name": "student",             "description": "University student"},
            {"name": "staff",               "description": "University staff member"},
            {"name": "maintenance_officer", "description": "Maintenance department officer"},
            {"name": "admin",               "description": "System administrator"},
        ]
        for r in roles:
            obj, created = Role.objects.get_or_create(
                name=r["name"], defaults={"description": r["description"]})
            self.stdout.write(f'  Role "{r["name"]}" — {"created" if created else "already exists"}')
        self.stdout.write("\nSeeding categories...")
        categories = [
            {"name": "Electricity",           "icon": "zap"},
            {"name": "Plumbing",              "icon": "droplets"},
            {"name": "Furniture",             "icon": "armchair"},
            {"name": "Internet / Network",    "icon": "wifi"},
            {"name": "Classroom Equipment",   "icon": "monitor"},
            {"name": "Hostel Maintenance",    "icon": "building"},
            {"name": "Air Conditioning",      "icon": "wind"},
            {"name": "Security / Access",     "icon": "shield"},
            {"name": "Cleaning / Sanitation", "icon": "trash-2"},
            {"name": "Other",                 "icon": "more-horizontal"},
        ]
        for c in categories:
            obj, created = RequestCategory.objects.get_or_create(
                name=c["name"], defaults={"icon": c["icon"]})
            self.stdout.write(f'  Category "{c["name"]}" — {"created" if created else "already exists"}')
        self.stdout.write(self.style.SUCCESS("\n✅ Database seeded successfully!"))
