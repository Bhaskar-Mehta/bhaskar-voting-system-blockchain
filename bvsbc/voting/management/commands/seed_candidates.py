from django.core.management.base import BaseCommand

from voting.models import Candidate

SAMPLE_CANDIDATES = [
    {"name": "Aarav Sharma", "party": "Unity Party", "symbol": "Sun", "bio": "Focused on campus infrastructure and student welfare."},
    {"name": "Priya Koirala", "party": "Progress Front", "symbol": "Tree", "bio": "Advocates for digital literacy and scholarships."},
    {"name": "Sandeep Rai", "party": "Independent", "symbol": "Star", "bio": "Running on a platform of transparency and open budgets."},
]


class Command(BaseCommand):
    help = "Seed the database with a few sample candidates for local testing."

    def handle(self, *args, **options):
        created = 0
        for entry in SAMPLE_CANDIDATES:
            _, was_created = Candidate.objects.get_or_create(name=entry["name"], defaults=entry)
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Done. {created} candidate(s) created, {len(SAMPLE_CANDIDATES) - created} already existed."))
