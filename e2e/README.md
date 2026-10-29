# Swift Drop E2E Testleri

Servislerin çalışan hâllerine gerçek HTTP istekleri atan ve sonuçları doğrudan veritabanından kontrol eden uçtan uca (e2e) test ortamı. Testler tek tek fonksiyonları değil, kullanıcı senaryolarını (case) baştan sona doğrular.

## Ön Koşullar

1. Postgres ve Redis ayakta olmalı (repo kökünden):

   ```bash
   docker compose up -d
   ```

2. Servislerin migration'ları uygulanmış ve servisler çalışıyor olmalı:

   - user-service: http://127.0.0.1:8000
   - restaurant-service: http://127.0.0.1:8001

   Servisler veya veritabanı erişilemezse test oturumu açıklayıcı bir hata mesajıyla hemen durur.

## Kurulum

```bash
cd e2e
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # Linux/macOS: cp .env.example .env
```

`.env` içindeki DB/Redis bilgileri servislerin `.env` dosyalarındaki değerlerle aynı olmalı.

| Değişken | Açıklama |
|---|---|
| `USER_SERVICE_URL`, `RESTAURANT_SERVICE_URL` | Servislerin adresleri |
| `USER_DB_URL`, `RESTAURANT_DB_URL` | Servis veritabanlarına doğrudan bağlantı |
| `REDIS_URL` | user-service'in kullandığı Redis (token iptali kontrolleri için) |
| `TEST_DATA_PREFIX` | Testlerin oluşturduğu tüm kayıtların başına eklenen prefix (varsayılan `e2e_test`); temizlik buna göre yapılır |
| `TEST_EMAIL_DOMAIN` | Test kullanıcılarının e-posta domain'i |
| `DEFAULT_PASSWORD` | Test kullanıcılarının şifresi |
| `KEEP_TEST_DATA` | `true` ise test verisi koşu sonunda silinmez (debug için) |

## Çalıştırma

```bash
pytest                                  # tüm case'ler
pytest tests/user_service               # tek klasör
pytest -m smoke                         # sadece smoke case'leri
pytest -k merchant                      # isminde "merchant" geçenler
pytest --log-cli-level=INFO             # tüm HTTP istek/yanıtlarını canlı göster
```

Tanımlı marker'lar: `user_service`, `restaurant_service`, `cross_service`, `smoke` (bkz. `pytest.ini`).

## Klasör Yapısı

```
e2e/
  conftest.py            ortak fixture'lar (DB, Redis, servis client'ları, actor'lar, temizlik)
  pytest.ini             pytest ayarları ve marker'lar
  framework/
    config.py            .env okuyan ayarlar
    db.py                ham SQL ile DB erişimi (fetch_one, fetch_all, scalar, execute)
    http_client.py       httpx tabanlı client, istek/yanıt loglama, expect_status
    services.py          endpoint wrapper'ları (UserServiceApi, RestaurantServiceApi)
    data.py              geçerli request payload'ları (override ile varyasyon üretilir)
    actors.py            hazır durumda kullanıcılar (doğrulanmış müşteri, onaylı merchant, admin...)
    cleanup.py           test verisinin temizlenmesi
  tests/
    user_service/        sadece user-service'i ilgilendiren case'ler
    restaurant_service/  restaurant-service case'leri
    cross_service/       birden fazla servisi kapsayan case'ler
```

## Fixture'lar

| Fixture | Ne verir |
|---|---|
| `settings` | `.env` ayarları |
| `user_db`, `restaurant_db` | `Database` nesnesi; doğrudan SQL çalıştırmak için |
| `redis_client` | user-service Redis bağlantısı |
| `user_api`, `restaurant_api` | Servis endpoint'lerine istek atan wrapper'lar; her metot ham `httpx.Response` döner |
| `actors` | Senaryonun ihtiyaç duyduğu kullanıcıyı tek satırda hazırlar |

`actors` mümkün olan her adımı gerçek API üzerinden yapar; endpoint'i olmayan tek adım olan admin oluşturma DB üzerinden yapılır:

- `actors.customer(verified=True, login=True, **overrides)`
- `actors.courier(verified=True, admin_verified=True, login=True, **overrides)`
- `actors.merchant(verified=True, admin_verified=True, status="approved", login=True, **overrides)`
- `actors.admin()`
- `actors.verification_token(actor)`, `actors.verify_email(actor)`, `actors.login(actor)`

Dönen `Actor` nesnesinde `user_id`, `email`, `password`, `role`, `profile_id` (customer/courier/merchant id), `access_token`, `refresh_token` ve kayıt yanıtı (`registration`) bulunur.

## Case Yazma Kuralları

- Her case kendi dosyasında: `tests/<alan>/test_<case_adi>.py`. Dosya bir senaryoyu anlatır, içindeki adımlar sırayla yazılır.
- Case dosyası eklendiğinde aşağıdaki case listesindeki satır güncellenir (dosya adı ve durum).
- Kullanıcı e-postaları her zaman `framework.data.unique_email()`, restoran/kategori/ürün isimleri `framework.data.unique_name()` ile üretilir. İkisi de `TEST_DATA_PREFIX` ile başlar; temizlik bu prefix'e göre yapılır ve testler birbirini etkilemez. Payload override'larında e-posta veya isim verilecekse yine bu fonksiyonlar kullanılmalı, yoksa kayıt temizlenmez.
- Yanıt kontrolünde `expect_status(response, 201)` kullanılırsa hata mesajında yanıt gövdesi de görünür.
- API'nin döndüğü değerler, gerektiğinde `user_db` / `restaurant_db` üzerinden DB'deki kayıtla da doğrulanır.

Örnek iskelet:

```python
import pytest

from framework import data
from framework.http_client import expect_status


@pytest.mark.restaurant_service
def test_merchant_builds_menu(actors, restaurant_api, restaurant_db):
    merchant = actors.merchant()

    restaurant = expect_status(
        restaurant_api.create_restaurant(merchant.access_token, data.restaurant_payload()), 201
    ).json()

    row = restaurant_db.fetch_one("SELECT * FROM restaurants WHERE id = :id", id=restaurant["id"])
    assert str(row["merchant_id"]) == merchant.profile_id
```

## Test Verisi ve Temizlik

Testlerin oluşturduğu her kayıt `TEST_DATA_PREFIX` (varsayılan `e2e_test`) ile başlar:

| Veritabanı | Prefix'li alan | Örnek |
|---|---|---|
| `user_db` | `users.email` | `e2e_test.customer.3f9a1c2b7d4e@e2e.swiftdrop.test` |
| `restaurant_db` | `restaurants.name`, `categories.name`, `items.name` | `e2e_test Restaurant 3f9a1c2b7d4e` |

Oturum başında (önceki koşulardan kalanlar için) ve sonunda her veritabanına ayrı ayrı bağlanılır ve prefix ile başlayan tüm kayıtlar silinir (`framework/cleanup.py`):

- `user_db`: prefix'li e-postaya sahip kullanıcılar silinir; profil (customer/courier/merchant) ve adresler cascade ile gider.
- `restaurant_db`: prefix'li isme sahip restoranlar (kategori ve ürünleriyle birlikte cascade), ardından başka bir üst kayda bağlı kalmış prefix'li kategori ve ürünler silinir.

Eşleşme `starts_with()` ile yapılır (`LIKE` kullanılmaz, çünkü `_` orada joker karakterdir). Debug için `KEEP_TEST_DATA=true` ayarlanabilir.

## Hesap Uygunluk Kuralları

Bir kullanıcının istek atabilmesi (token'ının kabul edilmesi) için hesabının rolüne göre şu koşulları sağlaması gerekir:

| Rol | Koşullar |
|---|---|
| customer | `users.is_active = true` ve `users.is_verified = true` |
| courier | customer koşulları + `couriers.is_verified = true` (admin onayı) |
| merchant | customer koşulları + `merchants.is_verified = true` (admin onayı) |

- Giriş (`/api/auth/login`) sadece `is_active` kontrol eder; uygun olmayan hesaplar da token alır, ama koşullar her istekte kontrol edildiği için bu token'la yapılan istekler 403 döner. Koşul sağlandığı anda aynı token yeniden kabul edilir.
- Kontrol `/api/auth/me` üzerinden yapılır; restaurant-service de token'ı bu endpoint'e sorduğu için aynı kurallar orada da geçerlidir.
- Merchant'ın `status` alanı (`pending`/`approved`/`rejected`) uygunluğu etkilemez; sadece `is_verified` bakılır.
- 403 yanıtlarının `detail` değerleri: `User is inactive`, `User is not verified`, `Courier is not verified`, `Merchant is not verified`.

Bu kurallar U12 case'i ile test edilecek.

## Case Listesi

Durum: `Planlandı` = henüz yazılmadı, `Yazıldı` = test dosyası mevcut.

### User Service

| # | Case | Test dosyası | Durum |
|---|---|---|---|

### Restaurant Service

| # | Case | Test dosyası | Durum |
|---|---|---|---|

### Servisler Arası

| # | Case | Test dosyası | Durum |
|---|---|---|---|