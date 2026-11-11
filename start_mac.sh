#!/bin/bash
# StepBite-ის მარტივი გაშვება macOS-ზე (ერთი ბრძანებით).
# თუ რომელიმე აუცილებელი ბრძანება ვერ შესრულდა, გაშვება შეწყდეს.
set -e
cd "$(dirname "$0")"
# ვამოწმებთ, არის თუ არა Mac-ზე Python 3.
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Python 3 არ მოიძებნა. ჯერ დააყენე Python 3.10 ან ახალი.'
  exit 1
fi
# .venv: იზოლირებული გარემო, სადაც Django და სხვა პაკეტები ყენდება.
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# ამ გარემოს ვრთავთ; Django პირველად უნდა დაყენდეს, შემდეგ ხელახლა აღარ ვტვირთავთ.
. .venv/bin/activate
if ! python -c "import django" >/dev/null 2>&1; then
  python -m pip install -r requirements.txt
fi
# SQLite-ში საჭირო ცხრილებს ვქმნით, თუ ჯერ არ არსებობს.
python manage.py migrate --noinput
printf '\nStepBite მზადაა: http://127.0.0.1:8000\n'
printf 'გასაჩერებლად დააჭირე Control+C\n\n'
# საიტს ვუშვებთ საკუთარ კომპიუტერზე პორტი 8000-ით.
python manage.py runserver 127.0.0.1:8000
