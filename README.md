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
- Can be used as sort key
- Allows specifying a min_length and alphabet globally
- Supports custom min_length, and alphabet per field
- Supports Django REST Framework Serializers
- Supports exact ID searches in Django Admin when field is specified in search_fields.
- Supports common filtering lookups, such as `__iexact`, `__contains`, `__icontains`, though matching is the same as `__exact`.
- Supports other lookups: isnull, gt, gte, lt and lte.

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

The folloing attributes can be added in settings file to set default arguments of `SqidsField`:

1. `DJANGO_SQIDS_MIN_LENGTH`: default minimum length
2. `DJANGO_SQIDS_ALPHABET`: default alphabet

`SqidsField` does not reqiure any arguments but the following arguments can be supplied to modify its behavior.

| Name              |                       Description                       |
| ----------------- | :-----------------------------------------------------: |
| `real_field_name` |                 The proxied field name                  |
| `sqids_instance`  | The sqids instance used to encode/decode for this field |
| `min_length`      |  The minimum length of sqids generated for this field   |
| `alphabet`        |    The alphabet used by this field to generate sqids    |

The argument `sqids_instance` is mutually exclusive to `min_length` and `alphabet`. See [sqids-python](https://github.com/sqids/sqids-python) for more info about the arguments.

Some common Model arguments such as `verbose_name` are also supported.

## Where did the Salt go?

[Sqids removed the "salt" parameter](https://sqids.org/faq#salt) to prevent association with security or safety.
`django_sqids` provides a useful `shuffle_alphabet` function that helps reintroduce the same idea:

```python
from django_sqids import SqidsField, shuffle_alphabet

class MyModel(models.Model):
    # will use your configured default alphabet
    sqid = SqidsField(alphabet=shuffle_alphabet(seed='randomSeed'))

class HexModel(models.Model):
    sqid = SqidsField(alphabet=shuffle_alphabet(seed='randomSeed', alphabet='0123456789abcdef'))

```
