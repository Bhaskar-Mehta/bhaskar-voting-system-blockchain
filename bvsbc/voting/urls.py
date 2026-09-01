from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup, name="signup"),
    path("verify-otp/", views.verify_otp, name="verify_otp"),
    path("resend-otp/", views.resend_otp, name="resend_otp"),
    path("login/", views.VotingLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),
    path("vote/", views.vote, name="vote"),
    path("vote/already-voted/", views.already_voted, name="already_voted"),
    path("vote/receipt/", views.vote_receipt, name="vote_receipt"),
    path("results/", views.results, name="results"),
    path("chain/", views.chain_explorer, name="chain"),
]
