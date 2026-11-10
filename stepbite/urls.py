"""URL მისამართები — გვერდები, ანგარიშები და API."""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from restaurant import views
from restaurant.forms import LoginForm

# ეს არის პროექტის მთავარი „მისამართების რუკა“.
# მაგალითად /cart/ აჩვენებს კალათას, /login/ — შესვლის გვერდს.
urlpatterns = [
    # Django-ის ჩაშენებული ადმინისტრატორის გვერდი (პროექტის ჩვეულებრივ გამოყენებას არ სჭირდება).
    path("admin/", admin.site.urls),
    # ჩვენი მენიუ, კალათა და რეგისტრაცია.
    path("", views.menu_page, name="menu"),
    path("cart/", views.cart_page, name="cart"),
    path("register/", views.register, name="register"),
    # შესვლა და გამოსვლა Django-ის მზა სისტემით.
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html", authentication_form=LoginForm), name="login"),
    # LogoutView POST-ით მუშაობს: logout ღილაკი დაცული ფორმაა.
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    # /api/... მოთხოვნებს restaurant/urls.py ამუშავებს.
    path("api/", include("restaurant.urls")),
]
