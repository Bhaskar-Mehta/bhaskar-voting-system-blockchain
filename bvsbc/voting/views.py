import hashlib
import secrets

from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import OTPVerifyForm, SignUpForm, VoteForm
from .models import Block, Candidate, EmailOTP, Vote, VoterProfile


def _send_otp_email(user, otp):
    subject = "Your Bhaskar Voting System verification code"
    message = (
        f"Hi {user.username},\n\n"
        f"Your one-time verification code is: {otp.code}\n"
        f"It expires in {EmailOTP.OTP_VALIDITY_MINUTES} minutes.\n\n"
        "If you didn't request this, you can ignore this email.\n"
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def home(request):
    candidates = Candidate.objects.all()
    has_voted = False
    if request.user.is_authenticated:
        has_voted = Vote.objects.filter(voter=request.user).exists()
    return render(request, "voting/home.html", {"candidates": candidates, "has_voted": has_voted})


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                user.email = form.cleaned_data["email"]
                user.is_active = False  # locked out until OTP is verified
                user.save()
                VoterProfile.objects.create(user=user)
                otp = EmailOTP.generate_for_user(user)
            _send_otp_email(user, otp)
            request.session["pending_user_id"] = user.id
            messages.info(request, "We sent a 6-digit code to your email. Check the server console if using the local mock email backend.")
            return redirect("verify_otp")
    else:
        form = SignUpForm()
    return render(request, "voting/signup.html", {"form": form})


def verify_otp(request):
    user_id = request.session.get("pending_user_id")
    if not user_id:
        messages.error(request, "Please sign up first.")
        return redirect("signup")

    from django.contrib.auth.models import User

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            otp = EmailOTP.objects.filter(user=user, code=code, is_used=False).order_by("-created_at").first()
            if otp is None:
                messages.error(request, "Invalid code. Please try again.")
            elif otp.is_expired():
                messages.error(request, "That code expired. Request a new one below.")
            else:
                otp.is_used = True
                otp.save(update_fields=["is_used"])
                user.is_active = True
                user.save(update_fields=["is_active"])
                user.voter_profile.is_email_verified = True
                user.voter_profile.save(update_fields=["is_email_verified"])
                del request.session["pending_user_id"]
                auth_login(request, user)
                messages.success(request, "Email verified! You're logged in.")
                return redirect("vote")
    else:
        form = OTPVerifyForm()

    return render(request, "voting/verify_otp.html", {"form": form, "email": user.email})


def resend_otp(request):
    user_id = request.session.get("pending_user_id")
    if not user_id:
        messages.error(request, "Please sign up first.")
        return redirect("signup")
    from django.contrib.auth.models import User

    user = get_object_or_404(User, id=user_id)
    otp = EmailOTP.generate_for_user(user)
    _send_otp_email(user, otp)
    messages.info(request, "A new code has been sent.")
    return redirect("verify_otp")


class VotingLoginView(LoginView):
    template_name = "voting/login.html"


@login_required
def vote(request):
    profile = request.user.voter_profile
    existing_vote = Vote.objects.filter(voter=request.user).first()
    if existing_vote:
        return redirect("already_voted")

    if not profile.is_email_verified:
        messages.error(request, "Please verify your email before voting.")
        return redirect("verify_otp")

    if request.method == "POST":
        form = VoteForm(request.POST)
        if form.is_valid():
            candidate = form.cleaned_data["candidate"]
            # Build a public receipt: a one-way hash tying this vote to
            # the voter without exposing their identity on the public
            # chain. A random salt is mixed in so the receipt can't be
            # brute-forced back to a username.
            salt = secrets.token_hex(16)
            raw = f"{request.user.id}:{candidate.id}:{salt}"
            receipt_code = hashlib.sha256(raw.encode()).hexdigest()

            try:
                with transaction.atomic():
                    Vote.objects.create(voter=request.user, candidate=candidate, receipt_code=receipt_code)
                    Block.add_vote_block(vote_receipt=receipt_code, candidate_name=candidate.name)
                    profile.has_voted = True
                    profile.save(update_fields=["has_voted"])
            except Exception:
                messages.error(request, "You have already voted, or your vote could not be recorded.")
                return redirect("already_voted")

            request.session["last_receipt"] = receipt_code
            messages.success(request, "Your vote has been recorded.")
            return redirect("vote_receipt")
    else:
        form = VoteForm()

    candidates = Candidate.objects.all()
    return render(request, "voting/vote.html", {"form": form, "candidates": candidates})


@login_required
def already_voted(request):
    existing_vote = Vote.objects.filter(voter=request.user).select_related("candidate").first()
    return render(request, "voting/already_voted.html", {"vote": existing_vote})


@login_required
def vote_receipt(request):
    receipt_code = request.session.get("last_receipt")
    vote_obj = None
    if receipt_code:
        vote_obj = Vote.objects.filter(receipt_code=receipt_code).select_related("candidate").first()
    if vote_obj is None:
        vote_obj = Vote.objects.filter(voter=request.user).select_related("candidate").first()
    return render(request, "voting/vote_receipt.html", {"vote": vote_obj})


def results(request):
    candidates = Candidate.objects.all()
    total = Vote.objects.count()
    rows = []
    for c in candidates:
        count = c.vote_count()
        pct = round((count / total) * 100, 1) if total else 0
        rows.append({"candidate": c, "count": count, "pct": pct})
    rows.sort(key=lambda r: r["count"], reverse=True)
    return render(request, "voting/results.html", {"rows": rows, "total": total})


def chain_explorer(request):
    from . import blockchain

    blocks = list(Block.objects.order_by("index"))
    is_valid, broken_index = blockchain.verify_chain(blocks)
    return render(
        request,
        "voting/chain.html",
        {"blocks": blocks, "is_valid": is_valid, "broken_index": broken_index},
    )
