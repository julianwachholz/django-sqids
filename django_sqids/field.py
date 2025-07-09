import random

from django.conf import settings
from django.core.exceptions import FieldError
from django.db.models import CharField, Field
from django.utils.functional import cached_property
from sqids import Sqids
from sqids.constants import DEFAULT_ALPHABET, DEFAULT_MIN_LENGTH

from .exceptions import ConfigError, RealFieldDoesNotExistError


def shuffle_alphabet(seed, alphabet=None):
    """
    Randomize the order of the alphabet.

    :param seed: Used to initialize Random(seed).
    :param str alphabet: Override the default alphabet used.

    """
    if alphabet is None:
        alphabet = getattr(settings, "DJANGO_SQIDS_ALPHABET", None) or DEFAULT_ALPHABET
    letters = list(alphabet)
    random.Random(seed).shuffle(letters)
    return "".join(letters)


class SqidsField(CharField):
    concrete = False
    allowed_lookups = ("exact", "in", "gt", "gte", "lt", "lte", "isnull")

    def __init__(
        self,
        real_field_name="id",
        *args,
        sqids_instance=None,
        alphabet=None,
        min_length=None,
        prefix="",
        **kwargs,
    ):
        kwargs.pop("editable", None)
        super().__init__(*args, editable=False, **kwargs)
        self.real_field_name = real_field_name
        self.min_length = min_length
        self.alphabet = alphabet
        self.prefix = prefix
        self._explicit_sqids_instance = sqids_instance

        self.sqids_instance = None
        self.attached_to_model = None

    def contribute_to_class(self, cls, name):
        self.attname = name
        self.name = name

        if getattr(self, "model", None) is None and cls._meta.abstract is False:
            self.model = cls

        if self.attached_to_model is not None:  # pragma: no cover
            raise FieldError(
                "Field '%s' is already attached to another model(%s)."
                % (self.name, self.attached_to_model)
            )
        self.attached_to_model = cls

        self.column = None

        if self.verbose_name is None:
            self.verbose_name = self.name

        setattr(cls, name, self)

        cls._meta.add_field(self, private=True)

        self.sqids_instance = self.get_sqid_instance()

    def get_sqid_instance(self):
        if self._explicit_sqids_instance:
            if self.alphabet is not None or self.min_length is not None:
                raise ConfigError(
                    "if sqids_instance is set, min_length and alphabet should not be set"
                )
            return self._explicit_sqids_instance
        min_length = self.min_length
        alphabet = self.alphabet
        if min_length is None:
            min_length = (
                getattr(settings, "DJANGO_SQIDS_MIN_LENGTH", None) or DEFAULT_MIN_LENGTH
            )
        if alphabet is None:
            alphabet = (
                getattr(settings, "DJANGO_SQIDS_ALPHABET", None) or DEFAULT_ALPHABET
            )
        return Sqids(min_length=min_length, alphabet=alphabet)

    def get_internal_type(self):
        return "CharField"

    def get_prep_value(self, value):
        if self.prefix:
            if value.startswith(self.prefix):
                value = value[len(self.prefix) :]
            else:
                return None
        decoded_values = self.sqids_instance.decode(value)
        if not decoded_values:
            return None
        if len(decoded_values) > 1:
            return None
        return decoded_values[0]

    def from_db_value(self, value, expression, connection, *args):
        # Prepend the prefix when encoding for display
        encoded_value = self.sqids_instance.encode([value])
        return f"{self.prefix}{encoded_value}" if encoded_value is not None else None

    def get_col(self, alias, output_field=None):
        if output_field is None:
            output_field = self
        col = self.real_col.get_col(alias, output_field)
        return col

    @cached_property
    def real_col(self):
        # `maybe_field` is intended for `pk`, which does not appear in `_meta.fields`
        maybe_field = getattr(self.attached_to_model._meta, self.real_field_name, None)
        if isinstance(maybe_field, Field):
            return maybe_field
        try:
            field = next(
                col
                for col in self.attached_to_model._meta.fields
                if col.name == self.real_field_name
                or col.attname == self.real_field_name
            )
        except StopIteration:
            raise RealFieldDoesNotExistError(
                "%s(%s) can't find real field using real_field_name: %s"
                % (self.__class__.__name__, self, self.real_field_name)
            )
        return field

    def __get__(self, instance, name=None):
        if not instance:
            return self
        real_value = getattr(instance, self.real_field_name, None)
        # the instance is not saved yet?
        if real_value is None:
            return ""
        assert isinstance(real_value, int)
        # Prepend the prefix when encoding for display
        encoded_value = self.sqids_instance.encode([real_value])
        return f"{self.prefix}{encoded_value}"

    def __set__(self, instance, value):
        pass

    def __deepcopy__(self, memo=None):
        new_instance = super().__deepcopy__(memo)
        for attr in ("sqids_instance", "attached_to_model"):
            if hasattr(new_instance, attr):
                setattr(new_instance, attr, None)
        # remove cached values from cached_property
        for key in ("real_col",):
            if key in new_instance.__dict__:
                del new_instance.__dict__[key]  # pragma: no cover
        return new_instance

    @classmethod
    def get_lookups(cls):
        all_lookups = super().get_lookups()
        return {k: all_lookups[k] for k in cls.allowed_lookups}
