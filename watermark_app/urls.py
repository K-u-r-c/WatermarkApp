from django.urls import path
from . import views

urlpatterns = [
    path("", views.apply_watermark, name="apply_watermark"),
]
