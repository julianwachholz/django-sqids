import os

import pytest
from django import setup
from django.db.models import ExpressionWrapper, F, IntegerField
from django.test import override_settings
from sqids import Sqids

from django_sqids.exceptions import ConfigError, RealFieldDoesNotExistError

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
    from tests.test_app.models import this_sqids_instance
    from django_sqids import SqidsField

    with pytest.raises(ConfigError):

        class Foo(Model):
            class Meta:
                app_label = "tests.test_app"

            hash_id = SqidsField(min_length=10, sqids_instance=this_sqids_instance)


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
    from tests.test_app.models import SecondSubClass, FirstSubClass

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
    from tests.test_app.models import ModelB, ModelA

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
