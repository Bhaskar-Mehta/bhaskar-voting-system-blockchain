from django.contrib import admin

from .models import Block, Candidate, EmailOTP, Vote, VoterProfile


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("name", "party", "symbol", "vote_count")


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("voter", "candidate", "cast_at", "receipt_code")
    readonly_fields = ("voter", "candidate", "cast_at", "receipt_code")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ("index", "timestamp", "previous_hash", "hash")
    readonly_fields = ("index", "timestamp", "data", "previous_hash", "nonce", "hash")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(VoterProfile)
class VoterProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "is_email_verified", "has_voted")


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "created_at", "is_used")
