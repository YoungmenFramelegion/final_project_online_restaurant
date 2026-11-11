"""SQLite მონაცემთა მოდელი: თითოეული მომხმარებლის პირადი კალათა.

Django-ის User მოდელი ცალკე ინახავს username/password-ს (პაროლი ჰეშირებულია).
აქ მხოლოდ პროდუქტები ინახება: სერვერის ID, სურათი, ფასი და რაოდენობა.
"""
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


# SQLite-ში ამ მოდელისგან იქმნება კალათის ცხრილი.
# ყოველი მწკრივი არის ერთი კერძი ერთი კონკრეტული მომხმარებლისთვის.
class CartItem(models.Model):
    # მომხმარებელთან კავშირი: სხვადასხვა მომხმარებლის კალათები არ ირევა.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart_items")
    # კერძის ინფორმაცია: ID, დასახელება, ფოტო, ფასი და რაოდენობა.
    product_id = models.PositiveIntegerField()
    name = models.CharField(max_length=255)
    image = models.URLField(max_length=1000, blank=True)
    price = models.DecimalField(max_digits=9, decimal_places=2)
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(99)], default=1)
    # კერძის დამატებითი ნიშნები, რომ კალათაშიც გამოჩნდეს.
    spiciness = models.PositiveSmallIntegerField(default=0)
    nuts = models.BooleanField(default=False)
    vegeterian = models.BooleanField(default=False)
    category_id = models.PositiveIntegerField(default=0)

    # ერთ მომხმარებელს ერთი და იგივე კერძი ორჯერ ცალკე რიგად არ უნდა ჩაეწეროს.
    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "product_id"], name="unique_cart_product_per_user")]
        ordering = ["id"]

    # ადმინისტრატორის ეკრანზე კალათის ჩანაწერის გასაგები დასახელება.
    def __str__(self):
        return f"{self.user.username}: {self.name} × {self.quantity}"

    # SQLite-ის ჩანაწერს JSON-სთვის გასაგებ მონაცემებად ვაქცევთ.
    def as_api_dict(self):
        """ვაბრუნებთ ისეთ JSON ველებს, როგორსაც არსებული JavaScript ელოდება."""
        return {
            "productId": self.product_id,
            "quantity": self.quantity,
            "price": float(self.price),
            "product": {
                "id": self.product_id,
                "name": self.name,
                "price": float(self.price),
                "image": self.image,
                "nuts": self.nuts,
                "vegeterian": self.vegeterian,
                "spiciness": self.spiciness,
                "categoryId": self.category_id,
            },
        }
