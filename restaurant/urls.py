"""აკადემიის API-ის სახელების შენარჩუნება, რათა არსებული app.js იმუშაოს."""
from django.urls import path
from . import views

# თითოეული URL კონკრეტულ ფუნქციაზე გადადის.
# Products და Categories გარედან მოდის, Baskets კი ჩვენს SQLite-ზე მუშაობს.
urlpatterns = [
    path("Products/GetAll", views.products_all),
    path("Products/GetFiltered", views.products_filtered),
    path("Categories/GetAll", views.categories_all),
    path("Categories/GetCategory/<int:category_id>", views.category_detail),
    # კალათის ნახვა, დამატება, რაოდენობის შეცვლა და წაშლა.
    path("Baskets/GetAll", views.cart_all),
    path("Baskets/AddToBasket", views.cart_add),
    path("Baskets/UpdateBasket", views.cart_update),
    path("Baskets/DeleteProduct/<int:product_id>", views.cart_delete),
]
