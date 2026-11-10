"""Django-ის ASGI entry point."""
# ASGI გამოიყენება აპლიკაციის სერვერზე გასაშვებად. ლოკალურ დაცვაზე შეცვლა არ გვჭირდება.
import os
from django.core.asgi import get_asgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stepbite.settings")
# Django-ის ASGI აპლიკაციის გაშვების წერტილი.
application = get_asgi_application()
