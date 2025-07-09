# Django Sqids

[![Github Actions](https://github.com/julianwachholz/django-sqids/workflows/test/badge.svg)](https://github.com/julianwachholz/django-sqids/actions)
[![Python Version](https://img.shields.io/pypi/pyversions/django-sqids.svg)](https://pypi.org/project/django-sqids/)
[![PyPI Package](https://img.shields.io/pypi/v/django-sqids.svg)](https://pypi.org/project/django-sqids/)
[![License](https://img.shields.io/pypi/l/django-sqids.svg)](https://github.com/julianwachholz/django-sqids/blob/main/LICENSE)

django-sqids is a simple and non-intrusive [sqids](https://sqids.org/) library for Django. It acts as a model field, but it does not touch the database or change the model.

The project was forked from [django-hashids](https://github.com/ericls/django-hashids) to provide the same functionality with the newer Sqids library.

# Features

- Proxy the internal model `pk` field without storing the value in the database.
- Allows lookups and filtering by sqid string.
- Can be used as sort key.
- Allows specifying a min_length and alphabet globally.
- Supports custom min_length, prefix, and alphabet per field.
- Supports Django REST Framework Serializers.
- Supports exact ID searches in Django Admin when field is specified in search_fields.
- Supports other lookups: `in`, `isnull`, `gt`, `gte`, `lt`, and `lte`.

# Install

```bash
pip install django-sqids
```

`django-sqids` is tested with Django 3.2, 4.2, 5.0 and Python 3.8 - 3.12.

# Usage

Add `SqidsField` to any model

```python
from django_sqids import SqidsField

class TestModel(Model):
    sqid = SqidsField(real_field_name="id")
```

`TestModel.sqid` field will proxy `TestModel.id` field but all queries will return and receive sqids strings. `TestModel.id` will work as before.

## Examples

```python
instance = TestModel.objects.create()
instance2 = TestModel.objects.create()
instance.id  # 1
instance2.id  # 2

# Allows access to the field
instance.sqid  # '1Z'
instance2.sqid  # '4x'

# Allows querying by the field
TestModel.objects.get(sqid="1Z")
TestModel.objects.filter(sqid="1Z")
TestModel.objects.filter(sqid__in=["1Z", "4x"])
TestModel.objects.filter(sqid__gt="1Z")  # same as id__gt=1, would return instance 2

# Allows usage in queryset.values
TestModel.objects.values_list("sqid", flat=True) # ["1Z", "4x"]
TestModel.objects.filter(sqid__in=TestModel.objects.values("sqid"))
```

## Using with URLs

You can use sqids to identify items in your URLs by treating them as slugs.

In `urls.py`:

```python
urlpatterns = [
    path("item/<slug>/", YourDetailView.as_view(), name="item-detail"),
]
```

And in your view:

```python
class YourDetailView(DetailView):
    model = Item
    slug_field = 'sqid'
```

## Using with Django Admin

Add the field to your ModelAdmin's `search_fields` to quickly find a record by its Sqid:

```python
class MyModelAdmin(admin.ModelAdmin):
    search_fields = [
        "sqid__exact",
    ]
```

## Config

The following attributes can be added in settings file to set default arguments of `SqidsField`:

1. `DJANGO_SQIDS_MIN_LENGTH`: default minimum length
2. `DJANGO_SQIDS_ALPHABET`: default alphabet

`SqidsField` does not require any arguments but the following arguments can be supplied to modify its behavior.

| Name              |                       Description                       | Example                                                     |
| ----------------- | :-----------------------------------------------------: | ----------------------------------------------------------- |
| `real_field_name` |                 The proxied field name                  | sqid = SqidsField(real_field_name="id")                     |
| `sqids_instance`  | The sqids instance used to encode/decode for this field | sqid = SqidsField(sqids_instance=sqids_instance)            |
| `min_length`      |  The minimum length of sqids generated for this field   | sqid = SqidsField(min_length=10)                            |
| `alphabet`        |    The alphabet used by this field to generate sqids    | sqid = SqidsField(alphabet="KHE5J3L2M4N6P7Q8R9T0V1W2X3Y4Z") |
| `prefix`          |     The prefix used by this field to generate sqids     | sqid = SqidsField(prefix="item-")                           |

The argument `sqids_instance` is mutually exclusive to `min_length` and `alphabet`. See [sqids-python](https://github.com/sqids/sqids-python) for more info about the arguments.

Some common Model arguments such as `verbose_name` are also supported.

## Where did the Salt go?

When the Hashids project transitioned to Sqids, [Sqids removed the "salt" parameter](https://sqids.org/faq#salt) to prevent the appearance that
it provides security or safety. In Sqids, the order of the alphabet affects the generated sqids. `django_sqids` provides a useful `shuffle_alphabet` 
function that helps reintroduce the same idea as the "salt" parameter by shuffling the alphabet. This can be used to generate a unique alphabet for each
instance of `SqidsField` to prevent the same id from generating the same sqid across different instances of `SqidsField`.

The `seed` parameter is used to generate a unique ordering of alphabet for each instance of `SqidsField`. The `alphabet` parameter can be used to specify a custom alphabet.

```python
from django_sqids import SqidsField, shuffle_alphabet

class MyModel(models.Model):
    # will use your configured default alphabet
    sqid = SqidsField(alphabet=shuffle_alphabet(seed='randomSeed'))

class HexModel(models.Model):
    sqid = SqidsField(alphabet=shuffle_alphabet(seed='randomSeed', alphabet='0123456789abcdef'))

```
