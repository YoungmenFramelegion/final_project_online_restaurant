# Django-ს მიგრაცია: კალათის ცხრილის შექმნა SQLite-ში.
from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


# ეს ფაილი Django-მ შექმნა: იგი SQLite-ში CartItem ცხრილის აგების წესია.
# ჩვეულებრივ, მიგრაციის კოდს სტუდენტი ხელით არ ცვლის.
class Migration(migrations.Migration):
    initial = True
    # ჯერ Django-ის მომხმარებლის ცხრილი უნდა არსებობდეს.
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    # შემდეგ იქმნება კალათის ცხრილი და უნიკალურობის წესი.
    operations = [
        migrations.CreateModel(
            name="CartItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product_id", models.PositiveIntegerField()),
                ("name", models.CharField(max_length=255)),
                ("image", models.URLField(blank=True, max_length=1000)),
                ("price", models.DecimalField(decimal_places=2, max_digits=9)),
                ("quantity", models.PositiveSmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(99)])),
                ("spiciness", models.PositiveSmallIntegerField(default=0)),
                ("nuts", models.BooleanField(default=False)),
                ("vegeterian", models.BooleanField(default=False)),
                ("category_id", models.PositiveIntegerField(default=0)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cart_items", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.AddConstraint(
            model_name="cartitem",
            constraint=models.UniqueConstraint(fields=("user", "product_id"), name="unique_cart_product_per_user"),
        ),
    ]
