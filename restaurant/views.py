"""Django Views — გვერდები, რეგისტრაცია და API მოთხოვნები.

სამუშაოს განაწილება:
* Django რენდერავს გვერდებს, მართავს მომხმარებელს/სესიას/SQLite კალათას.
* აკადემიის API იძლევა პროდუქტებსა და კატეგორიებს.
* app.js ამ მონაცემებს ბრაუზერში ხატავს.
"""
import json
from decimal import Decimal, InvalidOperation

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .api_client import RestaurantAPIError, fetch_restaurant
from .forms import RegisterForm
from .models import CartItem


@ensure_csrf_cookie
@require_GET
def menu_page(request):
    """მთავარი გვერდი — კერძების მენიუ და ფილტრები."""
    return render(request, "restaurant/index.html")


@ensure_csrf_cookie
@login_required
@require_GET
def cart_page(request):
    """კალათის გვერდზე მხოლოდ შესული მომხმარებელი გადადის."""
    return render(request, "restaurant/cart.html")


def register(request):
    """მომხმარებლის შექმნა SQLite-ში Django-ის სტანდარტული User მოდელით."""
    if request.user.is_authenticated:
        return redirect("menu")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()  # პაროლი ჰეშად ინახება და არა ჩვეულებრივ ტექსტად
        login(request, user)
        return redirect("menu")
    return render(request, "restaurant/register.html", {"form": form})


# Python-ის მონაცემებს Django აბრუნებს JSON პასუხად.
def _api_json(payload, status=200):
    return JsonResponse(payload, status=status, safe=not isinstance(payload, list), json_dumps_params={"ensure_ascii": False})


def _remote(path, params=None):
    """კერძებისა და კატეგორიებისთვის API-ის პასუხის გადაცემა ბრაუზერს."""
    try:
        return _api_json(fetch_restaurant(path, params))
    except RestaurantAPIError as exc:
        return _api_json({"error": str(exc)}, 502)


# მენიუს პროდუქტებისა და კატეგორიების მოთხოვნები (GET).
@require_GET
def products_all(request):
    return _remote("/api/Products/GetAll")


@require_GET
def categories_all(request):
    return _remote("/api/Categories/GetAll")


@require_GET
def category_detail(request, category_id):
    return _remote(f"/api/Categories/GetCategory/{category_id}")


@require_GET
def products_filtered(request):
    """მხოლოდ PDF-ში მოცემულ ოთხ ფილტრს ვიღებთ და ვამოწმებთ."""
    accepted = {}
    for key in ("categoryId", "spiciness", "nuts", "vegeterian"):
        if key not in request.GET:
            continue
        value = request.GET[key]
        if key in ("nuts", "vegeterian"):
            if value not in ("true", "false"):
                return _api_json({"error": "არასწორი ფილტრი: " + key}, 400)
        else:
            if not value.isdecimal() or (key == "spiciness" and not 0 <= int(value) <= 4) or (key == "categoryId" and int(value) < 1):
                return _api_json({"error": "არასწორი ფილტრი: " + key}, 400)
        accepted[key] = value
    return _remote("/api/Products/GetFiltered", accepted)


# ანონიმურ მომხმარებელს კალათის API-ზე JSON შეცდომას ვუბრუნებთ.
def _account_required(request):
    """რადგან ეს AJAX API-ია, login redirect-ის ნაცვლად JSON 401-ს ვაბრუნებთ."""
    if not request.user.is_authenticated:
        return _api_json({"error": "კალათის გამოსაყენებლად ჯერ შედი ანგარიშში"}, 401)
    return None


# კითხულობს ბრაუზერიდან გამოგზავნილ პროდუქტის ID-სა და რაოდენობას.
# ფასს არ ვენდობით — რეალური ფასი პროდუქტების API-დან მოწმდება.
def _read_json(request):
    """POST/PUT მოთხოვნის მონაცემების კითხვა — არ ვენდობით ბრაუზერიდან მოსულ ფასს."""
    if len(request.body) > 4096:
        raise ValueError("მოთხოვნა ძალიან დიდია")
    try:
        data = json.loads(request.body)
    except (UnicodeDecodeError, ValueError) as exc:
        raise ValueError("საჭიროა სწორი JSON მონაცემები") from exc
    if not isinstance(data, dict):
        raise ValueError("მოთხოვნა უნდა იყოს ობიექტი")
    if type(data.get("productId")) is not int or type(data.get("quantity")) is not int:
        raise ValueError("პროდუქტის ID და რაოდენობა მთელი რიცხვები უნდა იყოს")
    product_id, quantity = data["productId"], data["quantity"]
    if product_id < 1 or quantity < 1 or quantity > 99:
        raise ValueError("რაოდენობა უნდა იყოს 1-დან 99-მდე")
    return product_id, quantity


# ქვემოთ მოცემულია კალათის ოთხი ოპერაცია: ნახვა, დამატება, ცვლილება, წაშლა.
@require_GET
def cart_all(request):
    """SQLite-დან მხოლოდ მიმდინარე მომხმარებლის კალათის წაკითხვა."""
    error = _account_required(request)
    if error is not None:
        return error
    return _api_json([row.as_api_dict() for row in CartItem.objects.filter(user=request.user)])


@require_POST
def cart_add(request):
    """კალათაში კერძის დამატება; ფასი რეალური API-დან მოწმდება."""
    error = _account_required(request)
    if error is not None:
        return error
    try:
        product_id, quantity = _read_json(request)
        # პროდუქტს გარეთ ვამოწმებთ, რომ მომხმარებელმა ფასი არ შეცვალოს.
        products = fetch_restaurant("/api/Products/GetAll")
        product = next((p for p in products if int(p["id"]) == product_id), None)
        if product is None:
            return _api_json({"error": "კერძი ვერ მოიძებნა"}, 404)
        price = Decimal(str(product["price"]))
        if not price.is_finite() or not 0 <= price <= 9999999:
            return _api_json({"error": "არასწორი ფასი სერვერიდან"}, 502)
    except ValueError as exc:
        return _api_json({"error": str(exc)}, 400)
    except (RestaurantAPIError, InvalidOperation, KeyError, TypeError) as exc:
        return _api_json({"error": "პროდუქტის შემოწმება ვერ მოხერხდა"}, 502)

    # SQLite-ში ვამატებთ ახალ კერძს ან არსებულს რაოდენობას ვუმატებთ.
    # transaction.atomic ორივე ნაბიჯს ერთ მოქმედებად იცავს.
    with transaction.atomic():
        item, created = CartItem.objects.get_or_create(
            user=request.user,
            product_id=product_id,
            defaults={
                "name": str(product["name"])[:255],
                "image": str(product.get("image", ""))[:1000],
                "price": price,
                "quantity": quantity,
                "spiciness": int(product.get("spiciness", 0)),
                "nuts": bool(product.get("nuts", False)),
                "vegeterian": bool(product.get("vegeterian", False)),
                "category_id": int(product.get("categoryId", 0)),
            },
        )
        if not created:
            if item.quantity + quantity > 99:
                return _api_json({"error": "ერთი კერძის მაქსიმუმ 99 ცალია"}, 400)
            item.quantity += quantity
            item.save(update_fields=["quantity"])
    return _api_json(item.as_api_dict())


@require_http_methods(["PUT"])
def cart_update(request):
    """კალათაში უკვე არსებული პროდუქტის რაოდენობის შეცვლა."""
    error = _account_required(request)
    if error is not None:
        return error
    try:
        product_id, quantity = _read_json(request)
    except ValueError as exc:
        return _api_json({"error": str(exc)}, 400)
    # ვცვლით მხოლოდ იმ კერძს, რომელიც ამ მომხმარებლის კალათაშია.
    changed = CartItem.objects.filter(user=request.user, product_id=product_id).update(quantity=quantity)
    if not changed:
        return _api_json({"error": "ეს კერძი კალათაში არ არის"}, 404)
    return _api_json({"success": True})


@require_http_methods(["DELETE"])
def cart_delete(request, product_id):
    """მიმდინარე მომხმარებლის კალათიდან კერძის წაშლა."""
    error = _account_required(request)
    if error is not None:
        return error
    # სხვა მომხმარებლის ჩანაწერს ეს მოთხოვნა ვერ შეეხება.
    CartItem.objects.filter(user=request.user, product_id=product_id).delete()
    return _api_json({"success": True})
