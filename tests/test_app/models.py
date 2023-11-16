from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Model
from sqids import Sqids

from django_sqids import SqidsField


class TestModel(Model):
    sqids = SqidsField(real_field_name="id")


class TestModelWithDifferentConfig(Model):
    sqids = SqidsField(min_length=5, alphabet="OPQRST1234567890")


this_sqids_instance = Sqids()


class TestModelWithOwnInstance(Model):
    sqids = SqidsField(sqids_instance=this_sqids_instance)


class TestUser(AbstractUser):
    sqids = SqidsField(real_field_name="id")


class TestUserRelated(Model):
    sqids = SqidsField(real_field_name="id")

    user = models.ForeignKey(
        "TestUser", related_name="related", on_delete=models.CASCADE
    )


class FirstSubClass(TestModel):
    pass


class SecondSubClass(FirstSubClass):
    pass


class TestAbstractModel(models.Model):
    sqids = SqidsField(real_field_name="id")

    class Meta:
        abstract = True


class ModelA(TestAbstractModel):
    pass


class ModelB(ModelA):
    pass


class ModelUsingPKAsRealFieldName(Model):
    sqids = SqidsField(real_field_name="pk")
