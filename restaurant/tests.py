"""Django-ის ავტომატური ტესტები — არ საჭიროებს ინტერნეტს (Demo fixtures).

გასაშვებად: python3 manage.py test restaurant
"""
import json
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from .models import CartItem


@override_settings(STEPBITE_DEMO=True)
class StepBiteTests(TestCase):
    # ყოველი ტესტისთვის ორ დამოუკიდებელ მომხმარებელს ვქმნით.
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="student1", password="StrongPass#2026")
        self.other = get_user_model().objects.create_user(username="student2", password="StrongPass#2026")

    # დამხმარე ფუნქცია: ტესტის დროს POST/PUT მოთხოვნას JSON-ით აგზავნის.
    def send_json(self, path, payload, method="post"):
        return getattr(self.client, method)(path, data=json.dumps(payload), content_type="application/json")

    # ამოწმებს, რომ მენიუ, პროდუქტები და კატეგორიები იტვირთება.
    def test_menu_and_public_api(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        products = self.client.get("/api/Products/GetAll")
        self.assertEqual(products.status_code, 200)
        self.assertEqual(len(products.json()), 27)
        self.assertEqual(len(self.client.get("/api/Categories/GetAll").json()), 8)

    # ამოწმებს ფილტრის შედეგსა და არასწორი ფილტრის დაბლოკვას.
    def test_api_filters(self):
        response = self.client.get("/api/Products/GetFiltered", {"categoryId": "2", "spiciness": "3"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json())
        self.assertTrue(all(p["categoryId"] == 2 and p["spiciness"] == 3 for p in response.json()))
        self.assertEqual(self.client.get("/api/Products/GetFiltered", {"nuts": "maybe"}).status_code, 400)

    # ანგარიშის შექმნა, შესვლა, გამოსვლა და პაროლის დაცული შენახვა.
    def test_register_login_and_logout(self):
        response = self.client.post("/register/", {
            "username": "newstudent",
            "password1": "GoodTestPass#2026",
            "password2": "GoodTestPass#2026",
        })
        self.assertRedirects(response, "/")
        saved = get_user_model().objects.get(username="newstudent")
        self.assertNotEqual(saved.password, "GoodTestPass#2026")
        self.assertTrue(saved.check_password("GoodTestPass#2026"))
        self.assertEqual(self.client.get("/cart/").status_code, 200)
        self.assertRedirects(self.client.post("/logout/"), "/")
        self.assertRedirects(self.client.get("/cart/"), "/login/?next=/cart/")
        self.assertRedirects(self.client.post("/login/", {"username":"newstudent", "password":"GoodTestPass#2026"}), "/")

    # შესვლის გარეშე კალათის შეცვლა აკრძალულია.
    def test_anonymous_basket_is_blocked(self):
        self.assertEqual(self.client.get("/api/Baskets/GetAll").status_code, 401)
        self.assertEqual(self.send_json("/api/Baskets/AddToBasket", {"productId": 1, "quantity": 1, "price": 10}).status_code, 401)
        self.assertRedirects(self.client.get("/cart/"), "/login/?next=/cart/")

    # დამატება, რაოდენობის შეცვლა და კალათიდან წაშლა.
    def test_cart_add_update_remove_and_total_fields(self):
        self.client.force_login(self.user)
        # კლიენტი არ ადგენს ფასს: API-ის სწორი ფასი უნდა ჩაიწეროს SQLite-ში.
        added = self.send_json("/api/Baskets/AddToBasket", {"productId": 3, "quantity": 1, "price": 0})
        self.assertEqual(added.status_code, 200)
        self.assertEqual(added.json()["price"], 7)
        self.assertEqual(self.send_json("/api/Baskets/AddToBasket", {"productId": 3, "quantity": 1}).json()["quantity"], 2)
        self.assertEqual(len(self.client.get("/api/Baskets/GetAll").json()), 1)
        self.assertEqual(self.send_json("/api/Baskets/UpdateBasket", {"productId": 3, "quantity": 4}, method="put").status_code, 200)
        self.assertEqual(self.client.get("/api/Baskets/GetAll").json()[0]["quantity"], 4)
        self.assertEqual(self.client.delete("/api/Baskets/DeleteProduct/3").status_code, 200)
        self.assertEqual(self.client.get("/api/Baskets/GetAll").json(), [])

    # სხვადასხვა მომხმარებლის კალათები ერთმანეთს არ ერევა.
    def test_private_basket_two_users(self):
        self.client.force_login(self.user)
        self.send_json("/api/Baskets/AddToBasket", {"productId": 3, "quantity": 1})
        self.client.force_login(self.other)
        self.assertEqual(self.client.get("/api/Baskets/GetAll").json(), [])
        self.client.force_login(self.user)
        self.assertEqual(len(self.client.get("/api/Baskets/GetAll").json()), 1)

    # არასწორი ID და რაოდენობა არ მიიღება.
    def test_input_validation(self):
        self.client.force_login(self.user)
        self.assertEqual(self.send_json("/api/Baskets/AddToBasket", {"productId": 3, "quantity": 0}).status_code, 400)
        self.assertEqual(self.send_json("/api/Baskets/AddToBasket", {"productId": 9999, "quantity": 1}).status_code, 404)
        self.assertEqual(self.send_json("/api/Baskets/AddToBasket", {"productId": 3, "quantity": 100}).status_code, 400)
        self.assertEqual(self.send_json("/api/Baskets/UpdateBasket", {"productId": 3, "quantity": 2}, method="put").status_code, 404)

    # CSRF დაცვის გარეშე POST მოთხოვნა იბლოკება.
    def test_csrf_post_is_enforced(self):
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.user)
        response = strict.post("/api/Baskets/AddToBasket", data=json.dumps({"productId": 3, "quantity": 1}), content_type="application/json")
        self.assertEqual(response.status_code, 403)
