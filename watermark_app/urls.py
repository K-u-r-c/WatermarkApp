from django.urls import path, re_path
from . import views
from django.views.generic.base import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path("", views.apply_watermark, name="apply_watermark"),
    path(
        "favicon.ico",
        RedirectView.as_view(url=staticfiles_storage.url("images/favicon.png")),
    ),
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
