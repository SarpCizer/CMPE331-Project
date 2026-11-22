# Sarp Çizer - Backend Developer 2

Bu paket charter'daki **alışveriş listesi, favoriler, tarif geçmişi ve ilgili API desteğini** uygular (US-10–US-14). GET tarif detayı, geçmiş kaydını aynı işlemde tamamlayabilmek için bir entegrasyon noktasıdır. Kayıt/giriş/JWT üretimi, dolap CRUD, AI öneri üretimi, frontend veya deployment uygulaması bu pakette yoktur.

23 Kasım görev/entegrasyon rehberi: [Sarp handoff](docs/sarp-handoff.md). Burada #31–#34 eşlemesi, #30 ortak DTO sözleşmesi, dosyaların görevleri, gerçek RED/GREEN kayıtları ve arkadaşların ortak host'u ile tekrarlanabilir uyumluluk kontrolü bulunur. `backend_work` korunur; başka dallara merge/push yapılmaz. #22 için yalnızca [repo sahibi ayar önerisi](docs/main-protection.md) hazırlanmıştır.

Gönderilen `backend.zip` FastAPI/SQLAlchemy kullandığı ve charter Python/FastAPI seçeneğine izin verdiği için bu paket o yapıya takılabilen bir Python modülüdür. Ayrı `design_work` raporu Express önerir; bu uygulama o raporu değiştirmez. Son uygulama Express seçilirse Python router doğrudan Express'e eklenemez; API sözleşmesi korunarak servis sınırı veya bir port gerekir. Burada yeni bir genel teknoloji kararı alınmıyor.

## ZIP dosyalarıyla uyum

| Kaynak | Değerlendirme / bağlantı |
|---|---|
| `backend.zip` | FastAPI/SQLAlchemy oturum yapısı kullanılabilir. `zip_inventory_reader` mevcut `UserInventory` ve `Ingredient` modellerinden sadece doğrulanmış kullanıcının malzeme adlarını okur; `quantity`, `expiry_date` ve stok değerlerini yazmaz. |
| ZIP'in `Recipe` tablosu | Global ve kullanıcı sahipliği yok; ayrıca sözleşmedeki süre/kalori/porsiyon alanları eksik. Doğrudan kişisel favori/geçmiş kaynağı olarak kullanılmaz. `recipe_lookup` kabul edilmiş tarifi gerçek sahibiyle ve tam verisiyle döndürmelidir. |
| `recipe_recommendation.zip` | `recipe_from_zip_record`, önerideki `name`/`recipe` başlığını ortak DTO'ya uyarlar. İç uygulama ID'si, miktarsız kanonik malzeme adları, sıralı adımlar, süre/kalori tahminleri ve porsiyon sayısı tarif entegrasyonundan açıkça verilir. Miktar metinlerinden tahmin yapılmaz; `score` ve sağlayıcı ID'si API'ye taşınmaz. |
| `food_expiration_dates.zip` | Son kullanma/bozulma tahmini charter'da kapsam dışıdır; bu modüle alınmaz. |

Arşivler, notebook'lar, eğitim verileri ve ML ağırlıkları repoya kopyalanmadı. Paket pickle/XGBoost/Pandas yüklemez ve AI servisini başlatmaz. ZIP'in mevcut `main.py` dosyası açılışta CSV ve ML dosyalarını yüklediğinden bu modül onu import etmez. ZIP'te ayrıca shopping/favorites/history veya güvenilir JWT sahiplik kontrolü bulunmuyor; bunlar varmış gibi kabul edilmez.

## API

Yanıtlar doğrudan sözleşmedeki gövdedir. Hatalar `{ "error": "..." }` biçimindedir. Hatalı giriş 400, eksik/geçersiz doğrulama 401, bulunmayan veya başka kullanıcıya ait nesne 404 döndürür. 204 yanıtlarının gövdesi yoktur.

| Yöntem | Yol | Sonuç |
|---|---|---|
| GET | `/shopping-items` | Kullanıcının alışveriş listesi |
| POST | `/shopping-items` | `{name}`; yeni kayıt 201, normalize edilmiş tekrar 200 ve aynı ID |
| DELETE | `/shopping-items/{id}` | Kullanıcıya ait kaydı siler, 204 |
| POST | `/recipes/{id}/shopping-items` | Dolapta olmayan malzemeleri tek işlemde ekler; 200 liste |
| POST | `/favorites` | `{recipeId}`; tekrar kayıtta da aynı tam tarif, 200 |
| GET | `/favorites` | Tam tariflerden oluşan liste |
| DELETE | `/favorites/{recipeId}` | Yalnızca favori ilişkisini siler, 204 |
| GET | `/history` | `[{recipe,lastViewedAt}]`, en son görüntülenen önce |
| GET | `/recipes/{id}` | Tam tarif; başarılı yanıt öncesinde geçmişi kaydeder |

Ad eşleştirme `strip()` + Unicode `casefold()` kullanır; miktar çıkarma, eşanlamlı bulma veya besin çıkarımı yapmaz. Var olan alışveriş ID'leri ve görünen adları korunur. Dolap hiçbir işlemde azaltılmaz/artırılmaz. Favori eklemek geçmiş oluşturmaz; favoriden silmek tarifi veya geçmişi silmez. Aynı tarifin eski zamanlı bir isteği son görüntülenme zamanını geriye götürmez. Zamanlar UTC, eşit zamanlarda sıralama tarif ID'sidir.

## Ana backend'e bağlama

Paket import sırasında uygulama, tablo, kullanıcı veya dosya oluşturmaz. Doğrulama ve çekirdek veri için güvensiz varsayılan yoktur. Aşağıdaki fonksiyonların ekipteki sahipleri tarafından bağlanması gerekir:

1. **Berfin:** JWT imzasını/son kullanma zamanını doğrulayan `require_verified_account`. Geçersiz durumda 401; geçerli durumda `AccountPrincipal(str(current_user.id))` döndürür. Kullanıcı kimliği body/query/header içindeki bir owner alanından alınmaz.
2. **Berfin / Ayşe:** `load_owned_recipe(session, owner_id, recipe_id)`. Aynı SQLAlchemy oturumunda kullanıcıya göre filtrelenmiş, kalıcı, kabul edilmiş tam tarifi `OwnedRecipe(owner_id, RecipeDTO(...))` olarak döndürür. Eşleşme yoksa `None`. Global ZIP tarifi tek başına bu kontrolü sağlamaz.
3. **İrem:** Kullanıcının dolap adlarını salt okunur döndüren fonksiyon. ZIP'teki modeller seçilirse aşağıdaki hazır reader kullanılabilir.

Ana FastAPI uygulamasına eklenen bağlantı kodunun biçimi:

```python
from fridgely_collections import (
    CoreCallbacks, build_collections, zip_inventory_reader,
)

# app, SessionLocal, UserInventory, Ingredient, require_verified_account ve
# load_owned_recipe mevcut host backend'den gelir; bu paket bunları üretmez.
collections = build_collections(
    session_factory=SessionLocal,
    require_account=require_verified_account,
    core=CoreCallbacks(
        recipe_lookup=load_owned_recipe,
        inventory_lookup=zip_inventory_reader(
            inventory_model=UserInventory,
            ingredient_model=Ingredient,
        ),
    ),
)
app.include_router(collections.router)
```

`CoreData` callback'leri **verilen session'ı kullanır, commit/rollback yapmaz, AI çağırmaz ve dolabı değiştirmez**. Doğrulama ayrı bağımlılıktır. Bir isteğin SQLAlchemy oturumu ve transaction'ı bu servis tarafından açılıp kapatılır. Başarı, commit tamamlandıktan sonra döner. SQLite kilit / PostgreSQL serialization-deadlock hatalarında tüm işlem en fazla üç kez yeniden denenir. Snapshot izolasyonu ve bağlantı ayarları host veritabanının sorumluluğudur.

Mevcut bir `GET /recipes/{id}` endpoint'i varsa `include_recipe_details=False` kullanarak çakışmayı önleyin. O endpoint doğrulanmış kullanıcıyla `collections.service.open_recipe(owner_id, recipe_id)` çağırıp dönen tarifi yanıt olarak kullanmalıdır; bu çağrı sahiplik kontrolü ve geçmiş commit'ini birlikte tamamlar. `create_app(...)`, aynı zorunlu bağımlılıklarla bu modül için ayrı bir FastAPI host'u da oluşturabilir.

### Tablolar

`CollectionsBase` yalnızca `shopping_items`, `favorites`, `recipe_views` tablolarını tanımlar. Kullanıcıya göre benzersiz malzeme anahtarı ve kullanıcı/tarif bileşik anahtarları tekrarları engeller. SQLite ve PostgreSQL upsert'leri desteklenir.

Yerel kurulumda `create_schema(engine)` açıkça çağrılabilir; import sırasında çalışmaz. Gerçek ortamda Berfin'in migration'ına bu üç tablo eklenmelidir. Ortak kullanıcı/tarif tablolarının sahiplik alanları ve FK yapısı ZIP'te tamamlanmadığı için paket bunları tahmin ederek oluşturmaz/değiştirmez. Ortak şemaya uygun FK'ler o migration aşamasında eklenmelidir. Bu sırada servis sahipliği read port'u ve `OwnedRecipe` ile kontrol eder; başka kullanıcıya ait bir dönüşü de 404 ile reddeder.

## Kurulum ve test

Repo kökünden, Windows PowerShell:

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-test.lock
backend/.venv/Scripts/python.exe -m pip install --no-deps -e backend
backend/.venv/Scripts/python.exe -m pytest backend/tests
```

Linux/macOS'ta `.venv/Scripts/python.exe` yerine `.venv/bin/python` kullanılır. Paket tek başına kurulacaksa `python -m pip install './backend[test,serve]'` de kullanılabilir. Sabitlenmiş test ortamı `requirements-test.lock`, asgari çalışma bağımlılıkları `pyproject.toml` içindedir. ML paketleri gerekli değildir.

19 Kasım 2026'da Windows/Python 3.12.14 üzerinde **59 test geçti**. HTTP testleri gerçek SQLAlchemy/SQLite dosyası kullanır; JWT sağlayıcısı ve diğer ekip servisleri test double'dır. Senaryolar US-10–US-14 davranışları, sahiplik, doğrulama, eşzamanlı tekrarlar, diskten tekrar açılış, rollback ve commit öncesi başarı verilmemesini kapsar. PostgreSQL için SQL yolu vardır; canlı PostgreSQL veya gerçek JWT/AI entegrasyonu bu doğrulama kapsamında çalıştırılmadı.

23 Kasım 2026 kontrolünde **64 modül testi geçti**. Ayrıca arkadaşların `929776c` ortak uygulamasının ayrı ve geçici kopyasına bu branch'in modülü bağlandı: gerçek JWT, migrations ve kalıcı veri kullanan **126 Python testi ile 27 Node kabul testi geçti**. Yerel PostgreSQL olmadığı için bir PostgreSQL testi atlandı; canlı AI sağlayıcısı denenmedi. Ayrıntı ve tekrar çalıştırma adımları [rehberde](docs/sarp-handoff.md), ölçülen sonuçlar [verification.json](docs/verification.json) içindedir.

Bu branch'in kökündeki Node `src/acceptance-app.mjs` 501 iskeleti ve 27 kabul testi değiştirilmedi. Yukarıdaki 27 başarı, arkadaşların ortak HTTP adaptörü ve gerçek host'u üzerindeki uyumluluk çalışmasına aittir; bu branch tek başına bütün ekip uygulamasını içermez. Diğer branch'lere kod yazılmadı veya merge yapılmadı.

Kaynak sözleşmeler: [charter](../docs/CHARTER.MD), [API](../docs/requirements/api-contract.md), [US-10](../docs/requirements/US-10.md), [US-11](../docs/requirements/US-11.md), [US-12](../docs/requirements/US-12.md), [US-13](../docs/requirements/US-13.md), [US-14](../docs/requirements/US-14.md).

Teknik başvurular: [FastAPI router/dependency yapısı](https://fastapi.tiangolo.com/tutorial/bigger-applications/), [SQLAlchemy transaction'ları](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html), [SQLite upsert](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#insert-on-conflict-upsert).
