from django.shortcuts import get_object_or_404, render

from .models import TestModel, TestModelWithPrefix


def test_model_view(request, sqid):
    test_model = get_object_or_404(TestModel, sqid=sqid)
    return render(request, "test_app/testmodel.html", {"object": test_model})


def test_model_with_prefix_view(request, sqid):
    test_model_with_prefix = get_object_or_404(TestModelWithPrefix, sqid=sqid)
    return render(
        request, "test_app/testmodel.html", {"object": test_model_with_prefix}
    )
