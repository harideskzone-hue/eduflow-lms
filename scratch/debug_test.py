import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()
client = Client()

# Create a staff user if not exists
username = "debug_admin"
if not User.objects.filter(username=username).exists():
    User.objects.create_user(
        username=username,
        email="debug_admin@example.com",
        password="password123",
        is_staff=True
    )

client.login(username=username, password="password123")
url = reverse("monitoring_dashboard")
response = client.get(url)
print("Response status code:", response.status_code)
print(response.content.decode('utf-8'))
