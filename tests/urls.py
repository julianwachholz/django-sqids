from django.urls import path
from django.contrib import admin

from .test_app.views import test_model_view, test_model_with_prefix_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("without-prefix/<str:sqid>/", test_model_view, name="without-prefix"),
    path(
        "with-prefix/<str:sqid>/",
        test_model_with_prefix_view,
        name="with-prefix",
    ),
]
