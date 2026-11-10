"""Django-ის WSGI entry point."""
# WSGI-ის შესვლის წერტილი სერვერზე გასაშვებად. ჩვეულებრივ არ ვეხებით.
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stepbite.settings")
# აქ Django ქმნის ვებაპლიკაციას.
application = get_wsgi_application()