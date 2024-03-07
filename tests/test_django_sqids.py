import os

import pytest
from django import setup
from django.db.models import ExpressionWrapper, F, IntegerField
from django.test import override_settings
from django.urls import reverse
from rest_framework import serializers
from sqids import Sqids

from django_sqids import SqidsField
from django_sqids.exceptions import (
    ConfigError,
    IncorrectPrefixError,
    RealFieldDoesNotExistError,
)
from django_sqids.field import shuffle_alphabet

os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"
setup()

pytestmark = pytest.mark.django_db


def test_can_get_sqids():
    from django.conf import settings

    from tests.test_app.models import TestModel

    instance = TestModel.objects.create()
    sqid = instance.sqid
    sqids_instance = Sqids()
    assert sqids_instance.decode(sqid)[0] == instance.pk


def test_can_get_field_from_model():
    from tests.test_app.models import TestModel

    TestModel.sqid


def test_can_use_per_field_config():
    from tests.test_app.models import TestModelWithDifferentConfig

    instance = TestModelWithDifferentConfig.objects.create()
    sqid = instance.sqid
    sqids_instance = Sqids(min_length=5, alphabet="OPQRST1234567890")
    assert sqids_instance.decode(sqid)[0] == instance.pk


def test_can_use_per_field_instance():
    from tests.test_app.models import TestModelWithOwnInstance, this_sqids_instance

    instance = TestModelWithOwnInstance.objects.create()
    assert this_sqids_instance.decode(instance.sqid)[0] == instance.pk


def test_throws_when_setting_both_instance_and_config():
    from django.db.models import Model

    from django_sqids import SqidsField
    from tests.test_app.models import this_sqids_instance

    with pytest.raises(ConfigError):

        class Foo(Model):
            class Meta:
                app_label = "tests.test_app"

            hash_id = SqidsField(min_length=10, sqids_instance=this_sqids_instance)


def test_shuffle_alphabet_uses_seed():
    assert shuffle_alphabet("one") != shuffle_alphabet("two")


def test_shuffle_alphabet_uses_alphabet():
    alphabet = "LOREMIPSU"
    assert shuffle_alphabet("same", alphabet) == shuffle_alphabet("same", alphabet)
    assert shuffle_alphabet("one", alphabet) != shuffle_alphabet("two", alphabet)


def test_updates_when_changing_real_column_value():
    from django.conf import settings

    from tests.test_app.models import TestModel

    instance = TestModel.objects.create()
    instance.id = 3
    # works before saving
    sqids_instance = Sqids()
    assert sqids_instance.decode(instance.sqid)[0] == 3
    # works after saving
    instance.save()
    sqids_instance = Sqids()
    assert sqids_instance.decode(instance.sqid)[0] == 3


def test_ignores_changes_to_value():
    from django.conf import settings

    from tests.test_app.models import TestModel

    instance = TestModel.objects.create()
    instance.id = 3
    instance.sqid = "FOO"

    sqids_instance = Sqids()
    assert sqids_instance.decode(instance.sqid)[0] == 3
    # works after saving
    instance.save()

    instance.sqid = "FOO"
    sqids_instance = Sqids()
    assert sqids_instance.decode(instance.sqid)[0] == 3


def test_can_use_exact_lookup():
    from tests.test_app.models import TestModel

    instance = TestModel.objects.create()
    got_instance = TestModel.objects.filter(sqid=instance.sqid).first()
    assert instance == got_instance
    # assert id field still works
    got_instance = TestModel.objects.filter(id=instance.id).first()
    assert instance == got_instance


def test_can_use_in_lookup():
    from tests.test_app.models import TestModel

    instance = TestModel.objects.create()
    instance2 = TestModel.objects.create()
    sqids = [instance.sqid, instance2.sqid]
    qs = TestModel.objects.filter(sqid__in=sqids)
    assert set([instance, instance2]) == set(qs)


def test_can_use_lookup_when_value_does_not_exists():
    # https://github.com/ericls/django-sqids/issues/4
    from tests.test_app.models import TestModel

    # exact lookup
    instance = TestModel.objects.create()
    sqid = instance.sqid + "A"
    qs = TestModel.objects.filter(sqid=sqid)
    assert list(qs) == []

    # lookup
    instance = TestModel.objects.create()
    instance2 = TestModel.objects.create()
    sqids = [instance.sqid + "A", instance2.sqid + "A"]
    qs = TestModel.objects.filter(sqid__in=sqids)
    assert list(qs) == []


def test_can_use_lt_gt_lte_gte_lookup():
    from tests.test_app.models import TestModel

    instance = TestModel.objects.create()
    instance2 = TestModel.objects.create()
    qs = TestModel.objects.filter(sqid__lt=instance2.sqid)
    assert set([instance]) == set(qs)
    qs = TestModel.objects.filter(sqid__lte=instance2.sqid)
    assert set([instance, instance2]) == set(qs)
    qs = TestModel.objects.filter(sqid__gt=instance.sqid)
    assert set([instance2]) == set(qs)
    qs = TestModel.objects.filter(sqid__gte=instance.sqid)
    assert set([instance, instance2]) == set(qs)


def test_can_get_values():
    from tests.test_app.models import TestModel

    instance = TestModel.objects.create()
    instance2 = TestModel.objects.create()

    sqids = TestModel.objects.values("sqid")
    assert set([instance, instance2]) == set(TestModel.objects.filter(sqid__in=sqids))
    sqids = list(TestModel.objects.values_list("sqid", flat=True))
    assert set([instance, instance2]) == set(TestModel.objects.filter(sqid__in=sqids))
    # assert id field still works
    ids = list(TestModel.objects.values_list("id", flat=True))
    assert set([instance, instance2]) == set(TestModel.objects.filter(id__in=ids))


def test_can_select_as_integer():
    from tests.test_app.models import TestModel

    instance = TestModel.objects.create()
    instance2 = TestModel.objects.create()

    integer_ids = list(
        TestModel.objects.annotate(
            hid=ExpressionWrapper(F("sqid"), output_field=IntegerField())
        ).values_list("hid", flat=True)
    )
    assert set([instance.id, instance2.id]) == set(integer_ids)


@override_settings(DJANGO_SQIDS_MIN_LENGTH=10)
def test_can_use_min_length_from_settings():
    from tests.test_app.models import TestModel

    TestModel.sqid.sqids_instance = None
    TestModel.sqid.sqids_instance = TestModel.sqid.get_sqid_instance()

    instance = TestModel.objects.create()
    assert len(instance.sqid) >= 10


@override_settings(DJANGO_SQIDS_ALPHABET='!@#$%^&*(){}[]:"')
def test_can_use_min_length_from_settings():
    from tests.test_app.models import TestModel

    TestModel.sqid.sqids_instance = None
    TestModel.sqid.sqids_instance = TestModel.sqid.get_sqid_instance()

    instance = TestModel.objects.create()
    assert all(c in '!@#$%^&*(){}[]:"' for c in instance.sqid)


def test_not_saved_instance():
    from tests.test_app.models import TestModel

    instance = TestModel()
    assert instance.sqid == ""


def test_create_user():
    # https://github.com/ericls/django-sqids/issues/2
    from tests.test_app.models import TestUser

    u = TestUser.objects.create_user("username", password="password")
    assert TestUser.sqid.sqids_instance.decode(u.sqid)[0] == u.id


def test_multiple_level_inheritance():
    # https://github.com/ericls/django-sqids/issues/25
    from tests.test_app.models import FirstSubClass, SecondSubClass

    instance = SecondSubClass.objects.create()
    SecondSubClass.objects.filter(id=1).first() == SecondSubClass.objects.filter(
        sqid=instance.sqid
    ).first()

    instance = FirstSubClass.objects.create()
    FirstSubClass.objects.filter(id=1).first() == FirstSubClass.objects.filter(
        sqid=instance.sqid
    ).first()


def test_multiple_level_inheritance_from_abstract_model():
    # https://github.com/ericls/django-sqids/issues/25
    from tests.test_app.models import ModelA, ModelB

    instance = ModelB.objects.create()
    ModelB.objects.filter(id=1).first() == ModelB.objects.filter(
        sqid=instance.sqid
    ).first()

    instance = ModelA.objects.create()
    ModelA.objects.filter(id=1).first() == ModelA.objects.filter(
        sqid=instance.sqid
    ).first()


def test_related_queries():
    from tests.test_app.models import TestUser, TestUserRelated

    u = TestUser.objects.create()
    r = TestUserRelated.objects.create(user=u)

    assert TestUserRelated.objects.filter(user__sqid=u.sqid).first() == r
    assert TestUser.objects.filter(related__sqid=r.sqid).first() == u


def test_using_pk_as_real_field_name():
    # https://github.com/ericls/django-sqids/issues/31
    from tests.test_app.models import ModelUsingPKAsRealFieldName

    a = ModelUsingPKAsRealFieldName.objects.create()
    assert a.sqid
    assert ModelUsingPKAsRealFieldName.objects.get(sqid=a.sqid) == a
    assert ModelUsingPKAsRealFieldName.objects.get(sqid__lte=a.sqid) == a
    assert ModelUsingPKAsRealFieldName.objects.filter(sqid__lt=a.sqid).exists() is False


def test_no_real_field_error_message():
    from django.db.models import Model

    from django_sqids import SqidsField

    class Foo(Model):
        class Meta:
            app_label = "tests.test_app"

        hash_id = SqidsField(real_field_name="does_not_exist")

    with pytest.raises(RealFieldDoesNotExistError):
        Foo.objects.filter(hash_id="foo")


def test_prefix_is_applied_correctly():
    from tests.test_app.models import TestModelWithPrefix

    instance = TestModelWithPrefix.objects.create()
    assert instance.sqid.startswith("P-"), "The sqid field value should start with 'P-'"


def test_lookups_work_with_manual_prefix():
    from tests.test_app.models import TestModelWithPrefix

    instance = TestModelWithPrefix.objects.create()
    sqids = Sqids()
    sqids_with_prefix = f"P-{sqids.encode([instance.pk])}"

    got_instance = TestModelWithPrefix.objects.filter(
        sqid__exact=sqids_with_prefix
    ).first()
    assert instance == got_instance, "Exact lookup with prefix should work"


def test_lookups_ignore_prefix():
    from tests.test_app.models import TestModelWithPrefix

    instance = TestModelWithPrefix.objects.create()
    fetched_instance = TestModelWithPrefix.objects.get(sqid=instance.sqid)

    assert (
        fetched_instance == instance
    ), "Should be able to fetch the instance by sqid even with prefix"


def test_prefix_does_not_affect_filtering():
    from tests.test_app.models import TestModelWithPrefix

    instance1 = TestModelWithPrefix.objects.create()
    instance2 = TestModelWithPrefix.objects.create()
    sqids = [instance1.sqid, instance2.sqid]

    filtered_instances = set(TestModelWithPrefix.objects.filter(sqid__in=sqids))
    assert filtered_instances == {
        instance1,
        instance2,
    }, "Filtering by sqid with prefix should return correct instances"


def test_prefix_with_exact_lookup():
    from tests.test_app.models import TestModelWithPrefix

    instance = TestModelWithPrefix.objects.create()
    got_instance = TestModelWithPrefix.objects.filter(sqid__exact=instance.sqid).first()
    assert instance == got_instance, "Exact lookup with prefix should work"


def test_prefix_with_in_lookup():
    from tests.test_app.models import TestModelWithPrefix

    instance1 = TestModelWithPrefix.objects.create()
    instance2 = TestModelWithPrefix.objects.create()
    sqids_with_prefix = [instance1.sqid, instance2.sqid]

    qs = TestModelWithPrefix.objects.filter(sqid__in=sqids_with_prefix)
    assert set([instance1, instance2]) == set(
        qs
    ), "IN lookup with prefix should return correct instances"


def test_lookup_with_incorrect_prefix():
    """Tests behavior when an incorrect prefix is used in a lookup."""
    from tests.test_app.models import TestModelWithPrefix

    instance = TestModelWithPrefix.objects.create()
    incorrect_sqid = "X-" + instance.sqid[2:]
    with pytest.raises(IncorrectPrefixError):
        TestModelWithPrefix.objects.get(sqid=incorrect_sqid)


def test_case_sensitivity_with_prefix():
    """Tests case sensitivity in lookups involving prefixes."""
    from tests.test_app.models import TestModelWithPrefix

    instance = TestModelWithPrefix.objects.create()
    # Use a different case for the prefix in the lookup
    mixed_case_sqid = "p-" + instance.sqid[2:].lower()
    with pytest.raises(IncorrectPrefixError):
        TestModelWithPrefix.objects.get(sqid=mixed_case_sqid)


def test_complex_query_with_prefix():
    """Tests a complex query (e.g., join) to ensure prefix doesn't interfere."""
    from tests.test_app.models import TestUserRelatedWithPrefix, TestUserWithPrefix

    user = TestUserWithPrefix.objects.create()
    related = TestUserRelatedWithPrefix.objects.create(user=user)

    fetched_related = (
        TestUserRelatedWithPrefix.objects.select_related("user")
        .filter(user__sqid=user.sqid)
        .first()
    )
    assert (
        fetched_related == related
    ), "Complex query with prefix should return correct related instance"


def test_serialization_with_prefix():
    """Test serialization and deserialization with prefix, assuming Django REST Framework."""
    from tests.test_app.models import TestModelWithPrefix

    class TestModelWithPrefixSerializer(serializers.ModelSerializer):
        class Meta:
            model = TestModelWithPrefix
            fields = ["sqid"]

    instance = TestModelWithPrefix.objects.create()
    serializer = TestModelWithPrefixSerializer(instance)

    # Simulate serialization
    serialized_data = serializer.data
    assert serialized_data["sqid"].startswith(
        "P-"
    ), "Serialized data should contain prefixed sqid"

    # Simulate deserialization and validation
    input_data = {"sqid": serialized_data["sqid"]}
    new_serializer = TestModelWithPrefixSerializer(data=input_data)
    assert new_serializer.is_valid(), "Deserialized data with prefix should be valid"


def test_url_for_model_without_prefix(client):
    """Test that the URL for a model without prefix can be resolved."""
    from tests.test_app.models import TestModel

    instance = TestModel.objects.create()
    url = reverse("without-prefix", kwargs={"sqid": instance.sqid})
    response = client.get(url)
    assert response.status_code == 200
    assert response.context["object"] == instance


def test_incorrect_url_for_model_without_prefix(client):
    """Tests that url fails when adding a prefix to the sqid."""
    from tests.test_app.models import TestModel

    instance = TestModel.objects.create()
    url = reverse("without-prefix", kwargs={"sqid": "P-" + instance.sqid})
    response = client.get(url)
    assert response.status_code == 404, "URL with incorrect prefix should fail"


def test_url_for_model_with_prefix(client):
    """Test that the URL for a model with prefix can be resolved."""
    from tests.test_app.models import TestModelWithPrefix

    instance = TestModelWithPrefix.objects.create()
    url = reverse("with-prefix", kwargs={"sqid": instance.sqid})
    response = client.get(url)
    assert response.status_code == 200
    assert response.context["object"] == instance


def test_incortect_url_for_model_with_prefix(client):
    """Tests that IncorrectPrefixError is raised when resolving URL with incorrect prefix."""
    from tests.test_app.models import TestModelWithPrefix

    instance = TestModelWithPrefix.objects.create()
    with pytest.raises(IncorrectPrefixError):
        url = reverse("with-prefix", kwargs={"sqid": instance.sqid[2:]})
        response = client.get(url)

    with pytest.raises(IncorrectPrefixError):
        url = reverse("with-prefix", kwargs={"sqid": f"R-{instance.sqid[2:]}"})
        response = client.get(url)


def test_url_manually_with_prefix(client):
    """Test that the URL for a model with prefix can be resolved manually."""
    from tests.test_app.models import TestModelWithPrefix

    instance = TestModelWithPrefix.objects.create()
    sqids = Sqids()
    sqids_with_prefix = f"P-{sqids.encode([instance.pk])}"

    url = reverse("with-prefix", kwargs={"sqid": sqids_with_prefix})
    response = client.get(url)
    assert response.status_code == 200
    assert response.context["object"] == instance
