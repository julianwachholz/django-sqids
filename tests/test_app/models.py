from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Model
from sqids import Sqids

from django_sqids import SqidsField


class TestModel(Model):
    sqid = SqidsField(real_field_name="id")


class TestModelWithPrefix(Model):
    sqid = SqidsField(real_field_name="id", prefix="P-")


class TestModelWithDifferentConfig(Model):
    sqid = SqidsField(min_length=5, alphabet="OPQRST1234567890")


this_sqids_instance = Sqids()


class TestModelWithOwnInstance(Model):
    sqid = SqidsField(sqids_instance=this_sqids_instance)


class TestUser(AbstractUser):
    sqid = SqidsField(real_field_name="id")


class TestUserWithPrefix(AbstractUser):
    sqid = SqidsField(real_field_name="id", prefix="U-")


class TestUserRelated(Model):
    sqid = SqidsField(real_field_name="id")

    user = models.ForeignKey(
        "TestUser", related_name="related", on_delete=models.CASCADE
    )


class TestUserRelatedWithPrefix(Model):
    sqid = SqidsField(real_field_name="id", prefix="R-")

    user = models.ForeignKey(
        "TestUserWithPrefix", related_name="related", on_delete=models.CASCADE
    )


class FirstSubClass(TestModel):
    pass


class SecondSubClass(FirstSubClass):
    pass


class TestAbstractModel(models.Model):
    sqid = SqidsField(real_field_name="id")

    class Meta:
        abstract = True


class ModelA(TestAbstractModel):
    pass


class ModelB(ModelA):
    pass


class ModelUsingPKAsRealFieldName(Model):
    sqid = SqidsField(real_field_name="pk")
