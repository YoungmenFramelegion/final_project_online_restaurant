#!/usr/bin/env python3
"""Django-ის პროექტის მართვა: migrate, runserver, test."""

# Django-ის ბრძანებებს აქედან ვუშვებთ: runserver, migrate, test.
import os
import sys



# Django-ს ვუთითებთ, სადაა პარამეტრები, შემდეგ ვასრულებთ Terminal-ის ბრძანებას.
def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stepbite.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)



# ეს ნაწილი მუშაობს მაშინ, როცა Terminal-ში ვწერთ python manage.py ...
if __name__ == "__main__":
    main()
