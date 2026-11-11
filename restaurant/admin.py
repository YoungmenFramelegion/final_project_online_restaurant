"""სურვილისამებრ Admin პანელში კალათის ჩანაწერების ნახვა."""
# Django-ის ჩაშენებულ ადმინისტრატორში კალათის ჩანაწერებს ვაჩვენებთ.
from django.contrib import admin
from .models import CartItem


# ეს მხოლოდ ადმინისტრატორის ცხრილის სვეტებსა და ძებნას განსაზღვრავს.
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "quantity", "price")
    list_filter = ("user",)
    search_fields = ("user__username", "name")
