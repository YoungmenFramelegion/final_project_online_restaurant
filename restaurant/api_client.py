"""აკადემიის RestaurantAPI-დან კერძებისა და კატეგორიების წამოღება.

რეალურ რეჟიმში ვიყენებთ HTTPS-ს (SSL შემოწმებით). macOS-ზე Python-ის
სერტიფიკატების შეცდომისას ვცდით სისტემურ curl-ს, *-k/--insecure-ის გარეშე*.
STEPBITE_DEMO=1 რეჟიმი ინტერნეტის ნაცვლად fixtures/*.json ფაილებს კითხულობს.
"""
import json
import logging
import shutil
import subprocess
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings

log = logging.getLogger(__name__)


# გარედან API-ის გამოძახებისას შეცდომას საკუთარი სახელით ვაბრუნებთ.
class RestaurantAPIError(Exception):
    """გამოძახების შეცდომა: ამას JSON 502 პასუხად ვაქცევთ."""


# სატესტო რეჟიმისთვის ლოკალურ JSON ფაილს ვკითხულობთ.
def _fixture(filename):
    path = Path(settings.BASE_DIR) / "fixtures" / filename
    return json.loads(path.read_text(encoding="utf-8"))


# Demo რეჟიმში იმავე პროდუქტებს ვაჩვენებთ, მაგრამ ინტერნეტის გარეშე.
def _demo_response(path, params):
    """საცდელი პროდუქტების ფილტრაცია იგივე ოთხი პარამეტრით."""
    products = _fixture("products.json")
    if path == "/api/Products/GetAll":
        return products
    if path == "/api/Categories/GetAll":
        return _fixture("categories.json")
    if path == "/api/Products/GetFiltered":
        for field, value in params.items():
            expected = value == "true" if field in ("nuts", "vegeterian") else int(value)
            products = [p for p in products if p.get(field) == expected]
        return products
    if path.startswith("/api/Categories/GetCategory/"):
        cid = int(path.rsplit("/", 1)[-1])
        cat = next((c for c in _fixture("categories.json") if c["id"] == cid), None)
        if cat is None:
            raise RestaurantAPIError("ასეთი კატეგორია არ მოიძებნა")
        return {**cat, "products": [p for p in products if p["categoryId"] == cid]}
    raise RestaurantAPIError("უცნობი API მისამართი")


# რეალური რეჟიმი: მოთხოვნა აკადემიის სერვერზე, პასუხის JSON-ად წაკითხვა.
def fetch_restaurant(path, params=None):
    """GET მოთხოვნა აკადემიის API-სკენ; არასდროს იღებს მომხმარებლის მიერ არჩეულ host-ს."""
    params = params or {}
    if settings.STEPBITE_DEMO:
        return _demo_response(path, params)

    url = settings.RESTAURANT_API_ORIGIN + path
    if params:
        url += "?" + urlencode(params)
    try:
        request = Request(url, headers={"Accept": "application/json", "User-Agent": "StepBiteCourseProject/1.0"})
        with urlopen(request, timeout=12) as response:
            return json.loads(response.read())
    # თუ სერვერი HTTP შეცდომას აბრუნებს, ამას ვატყობინებთ ჩვენს აპლიკაციას.
    except HTTPError as exc:
        log.warning("RestaurantAPI HTTP %s at %s", exc.code, path)
        raise RestaurantAPIError("რესტორნის API-მ შეცდომა დააბრუნა") from exc
    except (URLError, OSError, TimeoutError, ValueError) as exc:
        log.warning("Python HTTPS failed; attempting verified system curl: %s", exc)
        # Mac-ზე ზოგჯერ Python-ის SSL სერტიფიკატებია გაუმართავი.
        # ასეთ დროს სისტემურ curl-ს ვცდით, HTTPS შემოწმების გამორთვის გარეშე.
        curl = shutil.which("curl")
        if not curl:
            raise RestaurantAPIError("კავშირი ვერ შედგა. გადაამოწმე ინტერნეტი ან HTTPS სერტიფიკატები") from exc
        try:
            result = subprocess.run(
                [curl, "--fail", "--silent", "--show-error", "--location", "--max-time", "15", url],
                capture_output=True,
                text=True,
                timeout=17,
                check=False,
            )
            if result.returncode != 0:
                log.warning("curl failed: %s", result.stderr[:240])
                raise RestaurantAPIError("აკადემიის API მიუწვდომელია. ინტერნეტი/SSL შეამოწმე")
            return json.loads(result.stdout)
        except (OSError, subprocess.TimeoutExpired, ValueError) as curl_exc:
            raise RestaurantAPIError("API-ის პასუხი ვერ დამუშავდა") from curl_exc
