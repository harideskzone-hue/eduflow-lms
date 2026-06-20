import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.test import RequestFactory
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
from django.core.cache import cache

cache.clear()

@ratelimit(key="ip", rate="2/m", method="POST", block=True)
def dummy_view(request):
    return "OK"

factory = RequestFactory()
request = factory.post("/dummy/", REMOTE_ADDR="127.0.0.1")

print("Request 1:")
try:
    print(dummy_view(request))
except Ratelimited:
    print("Ratelimited raised!")

print("Request 2:")
try:
    print(dummy_view(request))
except Ratelimited:
    print("Ratelimited raised!")

print("Request 3:")
try:
    print(dummy_view(request))
except Ratelimited:
    print("Ratelimited raised!")
