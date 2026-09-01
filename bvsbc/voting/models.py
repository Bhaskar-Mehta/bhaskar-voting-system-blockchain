import random

from django.conf import settings
from django.db import models
from django.utils import timezone

from . import blockchain


class VoterProfile(models.Model):
    """Extra info attached to Django's built-in User model."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="voter_profile")
    is_email_verified = models.BooleanField(default=False)
    has_voted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile<{self.user.username}>"


class EmailOTP(models.Model):
    """
    One-time password sent to a user's email for verification.

    Kept deliberately simple: a 6-digit numeric code with a short
    expiry. In this local/dev build the OTP is sent through Django's
    console email backend, so it will print to the terminal running
    `python manage.py runserver` instead of a real inbox. See the
    README for how to switch to a real SMTP backend.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="otps")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    OTP_VALIDITY_MINUTES = 10

    @classmethod
    def generate_for_user(cls, user):
        code = f"{random.randint(0, 999999):06d}"
        return cls.objects.create(user=user, code=code)

    def is_expired(self):
        age = timezone.now() - self.created_at
        return age.total_seconds() > self.OTP_VALIDITY_MINUTES * 60

    def __str__(self):
        return f"OTP({self.user.username}, used={self.is_used})"


class Candidate(models.Model):
    """A candidate or party that can be voted for."""

    name = models.CharField(max_length=150)
    party = models.CharField(max_length=150, blank=True, help_text="Optional party/affiliation name")
    symbol = models.CharField(max_length=50, blank=True, help_text="Optional short symbol/emoji, e.g. 'Lotus' or a color")
    bio = models.TextField(blank=True, help_text="Optional short description")

    def __str__(self):
        return f"{self.name} ({self.party})" if self.party else self.name

    def vote_count(self):
        return self.votes.count()


class Vote(models.Model):
    """
    One vote cast by one voter.

    The OneToOneField on `voter` is the core "prevent double voting"
    guard at the database level: a user can have at most one Vote row
    ever, enforced by the DB, not just application logic.
    """

    voter = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vote")
    candidate = models.ForeignKey(Candidate, on_delete=models.PROTECT, related_name="votes")
    cast_at = models.DateTimeField(auto_now_add=True)
    receipt_code = models.CharField(max_length=64, unique=True, help_text="Public receipt hash the voter can use to look up their vote on the chain")

    def __str__(self):
        return f"Vote({self.voter.username} -> {self.candidate.name})"


class Block(models.Model):
    """
    A single block in the local vote blockchain.

    index 0 is always the genesis block. Every vote cast afterwards
    appends exactly one block, chained to the previous block's hash.
    """

    index = models.PositiveIntegerField(unique=True)
    timestamp = models.DateTimeField()
    data = models.JSONField()
    previous_hash = models.CharField(max_length=64)
    nonce = models.PositiveIntegerField(default=0)
    hash = models.CharField(max_length=64, unique=True)

    class Meta:
        ordering = ["index"]

    def __str__(self):
        return f"Block #{self.index}"

    @classmethod
    def latest(cls):
        return cls.objects.order_by("-index").first()

    @classmethod
    def create_genesis_if_missing(cls):
        if cls.objects.exists():
            return cls.latest()
        now = timezone.now()
        data, previous_hash, block_hash = blockchain.build_genesis_block_fields(now.isoformat())
        return cls.objects.create(index=0, timestamp=now, data=data, previous_hash=previous_hash, hash=block_hash)

    @classmethod
    def add_vote_block(cls, vote_receipt, candidate_name):
        """Append a new block recording a cast vote and return it."""
        prev = cls.create_genesis_if_missing()
        now = timezone.now()
        new_index = prev.index + 1
        data, block_hash = blockchain.build_vote_block_fields(
            new_index, now.isoformat(), prev.hash, vote_receipt, candidate_name
        )
        return cls.objects.create(
            index=new_index,
            timestamp=now,
            data=data,
            previous_hash=prev.hash,
            hash=block_hash,
        )
