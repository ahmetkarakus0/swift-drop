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
   - order-service: http://127.0.0.1:8002 (sadece sepet/sipariş case'leri için gerekli)
   - courier-service: http://127.0.0.1:8003 (sadece kurye konum case'leri için gerekli)
   - gateway: http://127.0.0.1:8080 (sadece `tests/gateway` case'leri için gerekli)

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
| `USER_SERVICE_URL`, `RESTAURANT_SERVICE_URL`, `ORDER_SERVICE_URL`, `COURIER_SERVICE_URL` | Servislerin adresleri |
| `GATEWAY_URL` | Gateway adresi |
| `USER_DB_URL`, `RESTAURANT_DB_URL`, `ORDER_DB_URL` | Servis veritabanlarına doğrudan bağlantı |
| `REDIS_URL` | user-service ve courier-service'in kullandığı Redis (token iptali ve kurye konumu kontrolleri için) |
| `COURIER_LOCATIONS_KEY` | courier-service'in kurye konumlarını tuttuğu Redis GEO anahtarı (varsayılan `courier-locations`) |
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

Tanımlı marker'lar: `user_service`, `restaurant_service`, `cross_service`, `gateway`, `story`, `smoke` (bkz. `pytest.ini`).

## Klasör Yapısı

```
e2e/
  conftest.py            ortak fixture'lar (DB, Redis, servis client'ları, actor'lar, temizlik)
  pytest.ini             pytest ayarları ve marker'lar
  framework/
    config.py            .env okuyan ayarlar
    db.py                ham SQL ile DB erişimi (fetch_one, fetch_all, scalar, execute)
    http_client.py       httpx tabanlı client, istek/yanıt loglama, expect_status
    services.py          endpoint wrapper'ları (UserServiceApi, CourierServiceApi, RestaurantServiceApi, OrderServiceApi)
    data.py              geçerli request payload'ları (override ile varyasyon üretilir)
    actors.py            hazır durumda kullanıcılar (doğrulanmış müşteri, onaylı merchant, admin...)
    menus.py             hazır restoran menüleri (restoran + kategori + ürünler)
    cleanup.py           test verisinin temizlenmesi
    courier_locations.py Redis'teki kurye konumlarını okuma ve temizleme
  tests/
    user_service/        sadece user-service'i ilgilendiren case'ler
    restaurant_service/  restaurant-service case'leri
    cross_service/       birden fazla servisi kapsayan case'ler
    gateway/             istekleri gateway üzerinden atan case'ler
    stories/             birden fazla aktör ve servisi baştan sona kapsayan kullanıcı hikâyeleri
```

## Fixture'lar

| Fixture | Ne verir |
|---|---|
| `settings` | `.env` ayarları |
| `user_db`, `restaurant_db`, `order_db` | `Database` nesnesi; doğrudan SQL çalıştırmak için |
| `redis_client` | user-service Redis bağlantısı |
| `user_api`, `restaurant_api` | Servis endpoint'lerine istek atan wrapper'lar; her metot ham `httpx.Response` döner. `restaurant_api` merchant'ın sipariş işlemlerini (listeleme, accept, prepare, ready-for-pickup, cancel) de içerir |
| `order_api` | order-service'e (sepet ve sipariş) istek atan wrapper; sadece isteyen case'ler order-service'in ayakta olmasını gerektirir |
| `menus` | `menus.create(merchant, is_open=True, prices=("99.90",))` ile API üzerinden restoran + kategori + fiyat başına bir ürün kurar; dönen `Menu` nesnesinde `restaurant`, `category`, `items`, `item` (ilk ürün) ve `restaurant_id` bulunur |
| `courier_api` | courier-service'e doğrudan istek atan wrapper; sadece isteyen case'ler courier-service'in ayakta olmasını gerektirir |
| `courier_locations` | Redis'teki kurye konumlarını okur (`position(courier_id)` → `(lat, lon)` veya `None`); sorulan kuryelerin kayıtlarını case sonunda siler |
| `gateway_client` | Gateway'e istek atan `ApiClient`; sadece isteyen case'ler gateway'in ayakta olmasını gerektirir |
| `gateway_user_api` | `UserServiceApi` wrapper'ı, ama istekleri gateway üzerinden atar |
| `gateway_courier_api` | `CourierServiceApi` wrapper'ı; istekleri gateway üzerinden courier-service'e atar |
| `actors` | Senaryonun ihtiyaç duyduğu kullanıcıyı tek satırda hazırlar |

`actors` mümkün olan her adımı gerçek API üzerinden yapar; endpoint'i olmayan tek adım olan admin oluşturma DB üzerinden yapılır:

- `actors.customer(verified=True, login=True, **overrides)`
- `actors.courier(verified=True, admin_verified=True, login=True, **overrides)`
- `actors.merchant(verified=True, admin_verified=True, status="approved", login=True, **overrides)`
- `actors.admin()`
- `actors.verification_token(actor)`, `actors.verify_email(actor)`, `actors.login(actor)`

Dönen `Actor` nesnesinde `user_id`, `email`, `password`, `role`, `profile_id` (customer/courier/merchant id), `access_token`, `refresh_token` ve kayıt yanıtı (`registration`) bulunur.

## Case Yazma Kuralları

- E2E testleri tam kullanıcı hikâyelerini (story) test eder. Tek bir endpoint'in doğrulama kuralları (aynı e-postayla tekrar kayıt → 409, geçersiz payload → 422, bozuk token → 401 gibi) unit testlerin işidir, buraya yazılmaz. Hata yanıtları sadece hikâyenin doğal bir adımıysa kontrol edilir (ör. onaylanmamış kurye önce engellenir, onaydan sonra aynı token kabul edilir).
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
| `order_db` | prefix'li alan yok; `baskets.user_id` / `orders.user_id` test kullanıcılarının id'leri | — |

Oturum başında (önceki koşulardan kalanlar için) ve sonunda her veritabanına ayrı ayrı bağlanılır ve prefix ile başlayan tüm kayıtlar silinir (`framework/cleanup.py`):

- `order_db`: önce `user_db`'den prefix'li kullanıcıların id'leri okunur, bu kullanıcılara ait sepetler ve siparişler silinir (kalemleri cascade ile gider). Kullanıcılar silindikten sonra bu eşleşme kurulamayacağı için ilk bu adım çalışır.

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

Bu kurallar S1, S2 ve S3 hikâyeleri içinde test edilir.

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
| C1 | Merchant doğrulanmadan restoran oluşturamaz (önce `User is not verified`, e-posta doğrulandıktan sonra `Merchant is not verified`); admin merchant'ı doğruladıktan sonra aynı token ile restoran oluşturur | `tests/cross_service/test_merchant_verification_gates_restaurant_creation.py` | Yazıldı |
| C2 | Doğrulanmış müşteri ve onaylı merchant; merchant açık restoran, kategori ve ürün ekler; müşteri ürünü sepete ekleyip sipariş verir (sepet silinir). Merchant ilk siparişi sırayla accept → prepare → ready-for-pickup yapar (sonrasında cancel 409); ikinci siparişi accept → prepare → cancel yapar (sonrasında ready-for-pickup 409). Her adım `order_db` üzerinden de doğrulanır | `tests/cross_service/test_customer_order_lifecycle.py` | Yazıldı |

### Gateway

| # | Case | Test dosyası | Durum |
|---|---|---|---|
| G1 | Müşteri gateway üzerinden kayıt olur, e-postasını doğrular, giriş yapar ve `/api/auth/me` ile kendi bilgilerini alır | `tests/gateway/test_customer_auth_through_gateway.py` | Yazıldı |
| G2 | Kurye gateway üzerinden kayıt olur, e-postasını doğrular, admin kuryeyi onaylar; kurye `PUT /api/couriers/location` ile konumunu gönderir ve konum Redis'teki `courier-locations` GEO anahtarına yazılır | `tests/gateway/test_courier_location_update_through_gateway.py` | Yazıldı |

### Kullanıcı Hikâyeleri

Her hikâye bir veya birkaç aktörü baştan sona takip eder ve birden fazla servisten geçer. Bazı hikâyeler (S5, S6) servisler arası sınırlarda kimsenin veriyi tekrar kontrol etmediği yerleri test eder; bunlar mevcut davranışı sabitler ve bulgular hikâyenin açıklamasında yazılır.

#### Kayıt ve Onay

| # | Hikâye | Test dosyası | Durum |
|---|---|---|---|
| S1 | Kurye onboarding: kurye kayıt olur ve giriş yapar; konum göndermeye çalışır ve önce `User is not verified`, e-postasını doğruladıktan sonra `Courier is not verified` ile engellenir (Redis'e yazılmaz). Admin kuryeyi onaylar; aynı token ile konum gönderilir ve Redis'e yazılır | `tests/stories/test_s01_courier_onboarding.py` | Yazıldı |
| S2 | Müşteri onboarding: müşteri kayıt olup giriş yapar; e-postasını doğrulamadan sepete ürün eklemeye çalışır ve `User is not verified` ile engellenir. E-postasını doğruladıktan sonra aynı token ile sepete ekler ve sipariş verir | `tests/stories/test_s02_customer_onboarding.py` | Yazıldı |
| S3 | Admin başvuruları inceler: birkaç kurye ve merchant kayıt olur; admin kullanıcıları rol bazında listeler, bazılarını onaylar, bir merchant'ı `rejected` yapar. Sadece onaylananlar courier-service / restaurant-service'i kullanabilir (merchant `status` uygunluğu etkilemez; reddedilen merchant onaylanmadığı için engellenir) | `tests/stories/test_s03_admin_reviews_applicants.py` | Yazıldı |

#### Merchant ve Menü

| # | Hikâye | Test dosyası | Durum |
|---|---|---|---|
| S4 | Merchant işe başlar: kapalı restoran açar, menüyü kurar; müşteri sipariş vermeye çalışır ve `Restaurant is closed` alır. Merchant restoranı açar, müşteri sipariş verir ve sipariş merchant'ın listesine düşer. Gün sonunda merchant restoranı kapatır, müşteri tekrar `Restaurant is closed` alır | `tests/stories/test_s04_merchant_opens_for_business.py` | Yazıldı |
| S5 | Müşteri alışveriş yaparken merchant menüyü değiştirir: ürün sepetteyken fiyatı değişir, sonra ürün pasife alınır; müşteri siparişi verir / ürünü tekrar ekler. Siparişin hangi fiyatla ve hangi koşulda oluştuğu sabitlenir. **Bulgu:** sepet ürünün eklendiği andaki fiyatı tutar ve sipariş verilirken restaurant-service'e tekrar sorulmaz; fiyatı artmış ürün eski fiyattan, pasife alınmış ürün de sorunsuz sipariş edilir. Menü sadece ürün sepete eklenirken tekrar okunur (aynı ürünü tekrar eklemek satırın fiyatını günceller, pasif ürün eklenemez) | `tests/stories/test_s05_menu_changes_while_customer_shops.py` | Yazıldı |
| S6 | Merchant restoranı kapatır: müşterinin dolu bir sepeti ve bekleyen siparişi varken merchant restoranı siler. Sepetin siparişe dönüşüp dönüşmediği ve bekleyen siparişin akıbeti sabitlenir. **Bulgu:** restoran silinmesi order-service'e yansımaz; silinmiş restoranın sepeti hâlâ siparişe dönüşür, bekleyen siparişler ise `pending` olarak kalır ve merchant bunları artık listeleyemez, kabul veya iptal edemez (`Restaurant not found`) | `tests/stories/test_s06_merchant_deletes_restaurant.py` | Yazıldı |
| S7 | İki merchant, ayrı veri: A ve B'nin restoranları sipariş alır; her biri sadece kendi siparişlerini görür ve yönetir, B, A'nın siparişine (kendi restoran id'si üzerinden bile), menüsüne ve restoranına dokunamaz (404); A'nın verisi değişmeden kalır | `tests/stories/test_s07_merchants_see_only_their_own_data.py` | Yazıldı |

#### Müşteri Siparişi

| # | Hikâye | Test dosyası | Durum |
|---|---|---|---|
| S8 | İki restorandan sepet: müşteri iki restorandan ürün ekler (iki sepet), miktar değiştirir, ürün çıkarır, bir sepeti sipariş eder; diğer sepet kalır ve sonra sipariş edilir. Her merchant sadece kendi siparişini alır | `tests/stories/test_s08_baskets_from_two_restaurants.py` | Yazıldı |
| S9 | Tekrar gelen müşteri: müşteri zaman içinde birkaç sipariş verir; merchant bazılarını kabul eder, bazılarını iptal eder ve durum filtresiyle bekleyen / hazırlanan / biten siparişleri görür | | Planlandı |
| S10 | Logout her yerde geçerli: müşteri sipariş sürecinin ortasında çıkış yapar; eski token'ı order-service ve restaurant-service tarafından da reddedilir. Tekrar giriş yapıp siparişi tamamlar | | Planlandı |
| S11 | Akış ortasında hesap pasife alınır: aktif siparişleri olan merchant pasife alınır (endpoint olmadığı için DB üzerinden); merchant siparişleri yönetemez, müşterinin siparişi olduğu durumda kalır | | Planlandı |

#### Gateway

| # | Hikâye | Test dosyası | Durum |
|---|---|---|---|
| S12 | Gateway üzerinden tam teslimat yolu: müşteri, merchant ve kurye onboarding; müşteri sipariş verir, merchant siparişi ready-for-pickup'a getirir, kurye konum gönderir. Tüm platform için smoke test | | Planlandı |

#### Olaylar ve Dispatch

| # | Hikâye | Test dosyası | Durum |
|---|---|---|---|
| S13 | Sipariş olayları: sipariş verilip ready-for-pickup'a kadar ilerler; her adımda Kafka'daki `order-events` topic'ine doğru `previous_status` / `status` ile olay sırayla yayınlanır | | Planlandı |
| S14 | Dispatch: birkaç kurye konum paylaşır; sipariş ready-for-pickup olunca dispatch en yakın kuryeyi atar; kurye siparişi alır, sipariş on-the-way ve delivered olur. dispatch-service henüz iskelet olduğu için beklemede | | Planlandı |