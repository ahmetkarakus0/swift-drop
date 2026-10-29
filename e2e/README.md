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
| `TEST_EMAIL_DOMAIN` | Testlerin oluşturduğu tüm kullanıcıların e-posta domain'i; temizlik buna göre yapılır |
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

`actors` mümkün olan her adımı gerçek API üzerinden yapar; endpoint'i olmayan adımlar (admin oluşturma, kurye onayı) DB üzerinden yapılır:

- `actors.customer(verified=True, login=True, **overrides)`
- `actors.courier(verified=True, approved=True, login=True, **overrides)`
- `actors.merchant(verified=True, admin_verified=True, status="approved", login=True, **overrides)`
- `actors.admin()`
- `actors.verification_token(actor)`, `actors.verify_email(actor)`, `actors.approve_courier(actor)`, `actors.login(actor)`

Dönen `Actor` nesnesinde `user_id`, `email`, `password`, `role`, `profile_id` (customer/courier/merchant id), `access_token`, `refresh_token` ve kayıt yanıtı (`registration`) bulunur.

## Case Yazma Kuralları

- Her case kendi dosyasında: `tests/<alan>/test_<case_adi>.py`. Dosya bir senaryoyu anlatır, içindeki adımlar sırayla yazılır.
- Case dosyası eklendiğinde aşağıdaki case listesindeki satır güncellenir (dosya adı ve durum).
- Kullanıcı e-postaları her zaman `framework.data.unique_email()` ile üretilir; temizlik bu domain'e göre yapılır ve testler birbirini etkilemez.
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

Oturum başında (önceki koşulardan kalanlar için) ve sonunda `TEST_EMAIL_DOMAIN` ile biten tüm kullanıcılar silinir. Profil ve adresler `users` tablosundan cascade ile, bu kullanıcılara ait merchant'ların restoranları (kategori ve ürünleriyle birlikte) `restaurant_db`'den silinir. Debug için `KEEP_TEST_DATA=true` ayarlanabilir.

## Case Listesi

Durum: `Planlandı` = henüz yazılmadı, `Yazıldı` = test dosyası mevcut.

### User Service

| # | Case | Test dosyası | Durum |
|---|---|---|---|
| U1 | Müşteri kayıt olur, doğrulama linkiyle e-postasını doğrular, giriş yapar ve `/me` ile `customer_id` bilgisini görür | `tests/user_service/test_customer_registration_flow.py` | Planlandı |
| U2 | Kurye kayıt olur; onaylanmadan `/me` 403 döner, onaylandıktan sonra erişebilir | `tests/user_service/test_courier_approval_flow.py` | Planlandı |
| U3 | Merchant kayıt olur (`pending`); admin doğrulayıp onaylayana kadar `/me` 403 döner, sonra erişebilir | `tests/user_service/test_merchant_onboarding_flow.py` | Planlandı |
| U4 | Admin merchant'ı reddeder; merchant durumu `rejected` olur | `tests/user_service/test_merchant_rejection_flow.py` | Planlandı |
| U5 | Aynı e-postayla ikinci kayıt 409 döner, DB'de tek kullanıcı kalır | `tests/user_service/test_duplicate_registration.py` | Planlandı |
| U6 | Doğrulama linki ikinci kez kullanılamaz ve DB'de link temizlenir | `tests/user_service/test_email_verification_link.py` | Planlandı |
| U7 | Yanlış şifre ve olmayan kullanıcıyla giriş 401 döner; pasif kullanıcı 403 alır | `tests/user_service/test_login_failures.py` | Planlandı |
| U8 | Refresh token yeni token çifti verir; eski refresh token tekrar kullanılamaz | `tests/user_service/test_token_refresh_rotation.py` | Planlandı |
| U9 | Logout sonrası access ve refresh token'lar geçersiz olur (Redis'te iptal kaydı oluşur) | `tests/user_service/test_logout_revokes_tokens.py` | Planlandı |
| U10 | Admin olmayan kullanıcı merchant doğrulama/durum endpoint'lerine 403 alır | `tests/user_service/test_merchant_admin_authorization.py` | Planlandı |
| U11 | Geçersiz payload'lar (kurye plaka kuralları, IBAN, telefon) 422 döner | `tests/user_service/test_registration_validation.py` | Planlandı |

### Restaurant Service

| # | Case | Test dosyası | Durum |
|---|---|---|---|
| R1 | Onaylı merchant restoran açar, kategori ve ürün ekler; restoran detayında menü eksiksiz görünür | `tests/restaurant_service/test_merchant_builds_menu.py` | Planlandı |
| R2 | Merchant restoran, kategori ve ürünü günceller; sadece gönderilen alanlar değişir | `tests/restaurant_service/test_menu_partial_updates.py` | Planlandı |
| R3 | Restoran silinince restoran, kategorileri ve ürünleri pasif olur; DB'den kayıt silinmez | `tests/restaurant_service/test_restaurant_deactivation.py` | Planlandı |
| R4 | Kategori silinince ürünleriyle birlikte DB'den silinir | `tests/restaurant_service/test_category_deletion.py` | Planlandı |
| R5 | Merchant başka bir merchant'ın restoran/kategori/ürününe erişemez (404) | `tests/restaurant_service/test_merchant_isolation.py` | Planlandı |

### Servisler Arası

| # | Case | Test dosyası | Durum |
|---|---|---|---|
| X1 | Token'sız veya geçersiz token'la restaurant-service istekleri 401 döner | `tests/cross_service/test_restaurant_auth_required.py` | Planlandı |
| X2 | Müşteri ve kurye token'larıyla restaurant-service 403 döner | `tests/cross_service/test_restaurant_non_merchant_forbidden.py` | Planlandı |
| X3 | Doğrulanmamış veya admin onayı almamış merchant restaurant-service'te 403 alır | `tests/cross_service/test_unverified_merchant_forbidden.py` | Planlandı |
| X4 | Merchant logout olduktan sonra eski token'la restaurant-service'e erişemez | `tests/cross_service/test_logout_blocks_restaurant_access.py` | Planlandı |
