"""Юнит-тесты парсинга и чистки фида (без БД и сети)."""
import textwrap

from app.scraper.feed_source import (
    clean_text, parse_price, norm_currency, YmlFeedSource,
)


def test_clean_text():
    assert clean_text("<b>Набор</b>&nbsp;воблеров &amp; блёсен") == "Набор воблеров & блёсен"
    assert clean_text(None) is None
    assert clean_text("   ") is None


def test_parse_price():
    assert parse_price("2 490,00") == 2490.0
    assert parse_price("8990") == 8990.0
    assert parse_price("—") is None
    assert parse_price(None) is None


def test_norm_currency():
    assert norm_currency("RUR") == "RUB"
    assert norm_currency(None) == "RUB"
    assert norm_currency("usd") == "USD"


YML = textwrap.dedent('''\
<?xml version="1.0" encoding="UTF-8"?>
<yml_catalog date="2026-01-01"><shop>
<categories>
<category id="1">Подарки</category>
<category id="10" parentId="1">Рыбалка</category>
</categories>
<offers>
<offer id="1" available="true"><name>Товар A</name><price>1 000,00</price>
<currencyId>RUR</currencyId><categoryId>10</categoryId><url>https://x/1</url></offer>
<offer id="2" available="false"><name>Товар B</name><price>500</price><url>https://x/2</url></offer>
<offer id="3"><name></name><url>https://x/3</url></offer>
</offers>
</shop></yml_catalog>''')


def test_yml_parsing(tmp_path):
    f = tmp_path / "feed.xml"
    f.write_text(YML, encoding="utf-8")
    src = YmlFeedSource(str(f), source_name="test")

    cats = list(src.categories())
    assert {c.name for c in cats} == {"Подарки", "Рыбалка"}

    offers = list(src.offers())
    assert len(offers) == 2  # оффер без имени (id=3) пропущен
    o1 = next(o for o in offers if o.external_id == "1")
    assert o1.price == 1000.0          # '1 000,00' -> 1000.0
    assert o1.currency == "RUB"        # RUR -> RUB
    assert any(not o.available for o in offers)  # id=2 available=false
