# Django-ს ვეუბნებით, რომ ჩვენი აპლიკაციის სახელია restaurant.
from django.apps import AppConfig



# აპლიკაციის საბაზისო პარამეტრები; დამატებით არაფერს არ ვაკეთებთ.
class RestaurantConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "restaurant"
