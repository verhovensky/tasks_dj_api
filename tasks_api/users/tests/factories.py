import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from factory import Faker
from factory.django import DjangoModelFactory


class UserFactory(DjangoModelFactory):
    email = Faker("email")
    name = Faker("name")
    password = factory.LazyFunction(lambda: make_password("pi3.1415"))

    class Meta:
        model = get_user_model()
        django_get_or_create = ["email"]
