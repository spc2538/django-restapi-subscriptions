from django.urls import path
from .views import FirebaseLoginView

urlpatterns = [
    path("firebase-login/", FirebaseLoginView.as_view()),
]
