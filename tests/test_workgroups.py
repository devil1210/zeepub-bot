from unittest.mock import AsyncMock, patch
import pytest

from models.library import GroupContactLink, TranslatorsGroup
from services.workgroup_service import WorkgroupService
from utils.template_engine import apply_publication_template


def test_translators_group_preferred_link_priority():
    group = TranslatorsGroup(name="Novelas Ligera Fansub")
    group.contact_links = [
        GroupContactLink(platform="discord", url="https://discord.gg/test"),
        GroupContactLink(platform="facebook", url="https://facebook.com/testfansub"),
        GroupContactLink(platform="website", url="https://testfansub.com"),
    ]

    # Prioridad 1: Website
    assert group.get_preferred_link() == "https://testfansub.com"

    # Si se elimina Website, prioridad 2: Facebook
    group.contact_links = [
        GroupContactLink(platform="discord", url="https://discord.gg/test"),
        GroupContactLink(platform="facebook", url="https://facebook.com/testfansub"),
    ]
    assert group.get_preferred_link() == "https://facebook.com/testfansub"

    # Si se elimina Facebook, prioridad 3: Discord
    group.contact_links = [
        GroupContactLink(platform="discord", url="https://discord.gg/test"),
    ]
    assert group.get_preferred_link() == "https://discord.gg/test"


def test_translators_group_links_dict():
    group = TranslatorsGroup(name="Kitsune Scan")
    group.contact_links = [
        GroupContactLink(platform="Web Oficial", url="https://kitsune.com"),
        GroupContactLink(platform="Facebook", url="https://fb.com/kitsune"),
        GroupContactLink(platform="Discord", url="https://discord.gg/kitsune"),
        GroupContactLink(platform="Patreon", url="https://patreon.com/kitsune"),
    ]

    links = group.get_links_dict()
    assert links["web"] == "https://kitsune.com"
    assert links["fb"] == "https://fb.com/kitsune"
    assert links["discord"] == "https://discord.gg/kitsune"
    assert links["patreon"] == "https://patreon.com/kitsune"


@pytest.mark.asyncio
async def test_resolve_translator_metadata():
    mock_group = TranslatorsGroup(name="Escanor Translations")
    mock_group.contact_links = [
        GroupContactLink(platform="web", url="https://escanor.net"),
        GroupContactLink(platform="facebook", url="https://facebook.com/escanor"),
        GroupContactLink(platform="discord", url="https://discord.gg/escanor"),
    ]

    with patch.object(WorkgroupService, "get_by_name", new_callable=AsyncMock, return_value=mock_group):
        meta = await WorkgroupService.resolve_translator_metadata(translator_name="Escanor Translations")
        assert meta["traductor"] == "Escanor Translations"
        assert meta["traductor_link"] == "https://escanor.net"
        assert meta["traductor_web"] == "https://escanor.net"
        assert meta["traductor_fb"] == "https://facebook.com/escanor"
        assert meta["traductor_discord"] == "https://discord.gg/escanor"
        assert "🌐 Web: https://escanor.net" in meta["traductor_links"]
        assert "📘 Facebook: https://facebook.com/escanor" in meta["traductor_links"]


def test_template_engine_with_translator_tags():
    template = (
        "📖 <b>{titulo}</b>\n"
        "[?traductor]👥 Traductor: <a href=\"{traductor_link}\">{traductor}</a>\n[/?]"
        "[?traductor_discord]💬 Discord: {traductor_discord}\n[/?]"
        "[?traductor_fb]📘 FB: {traductor_fb}\n[/?]"
    )

    data = {
        "title": "Solo Leveling Vol 1",
        "traductor": "Hunter Scans",
        "traductor_link": "https://hunterscans.com",
        "traductor_discord": "https://discord.gg/hunter",
        "traductor_fb": "",
    }

    rendered = apply_publication_template(template, data)
    assert "👥 Traductor: <a href=\"https://hunterscans.com\">Hunter Scans</a>" in rendered
    assert "💬 Discord: https://discord.gg/hunter" in rendered
    assert "📘 FB:" not in rendered  # Condicional se ocultó porque estaba vacío


@pytest.mark.asyncio
async def test_resolve_book_workgroup_credits_all_roles():
    group_t = TranslatorsGroup(name="Translator Group")
    group_t.contact_links = [GroupContactLink(platform="web", url="https://trans.com")]

    group_e = TranslatorsGroup(name="Editor Pro")
    group_e.contact_links = [GroupContactLink(platform="facebook", url="https://fb.com/editor")]

    group_m = TranslatorsGroup(name="Layout Master")
    group_m.contact_links = [GroupContactLink(platform="discord", url="https://discord.gg/layout")]

    def fake_get_by_name(name):
        if name == "Translator Group":
            return group_t
        if name == "Editor Pro":
            return group_e
        if name == "Layout Master":
            return group_m
        return None

    with patch.object(WorkgroupService, "get_by_name", side_effect=fake_get_by_name), \
         patch.object(WorkgroupService, "get_by_id", return_value=None):
        raw = {
            "traductor": "Translator Group",
            "editor": "Editor Pro",
            "maquetador": "Layout Master",
        }
        res = await WorkgroupService.resolve_book_workgroup_credits(
            book_id="book_uuid_12345",
            raw_meta=raw,
        )
        assert res["traductor"] == "Translator Group"
        assert res["traductor_link"] == "https://trans.com"
        assert res["editor"] == "Editor Pro"
        assert res["editor_link"] == "https://fb.com/editor"
        assert res["maquetador"] == "Layout Master"
        assert res["maquetador_link"] == "https://discord.gg/layout"


@pytest.mark.asyncio
async def test_distinct_individual_translator_and_group_template():
    group_fansub = TranslatorsGroup(name="Novelas Ligera Fansub")
    group_fansub.contact_links = [
        GroupContactLink(platform="website", url="https://novelasligera.com"),
        GroupContactLink(platform="discord", url="https://discord.gg/novelas"),
        GroupContactLink(platform="facebook", url="https://fb.com/novelasligera"),
    ]

    with patch.object(WorkgroupService, "get_by_name", return_value=group_fansub), \
         patch.object(WorkgroupService, "get_by_id", return_value=None):
        raw = {
            "traductor": "Kiri (Traductor Individual)",
            "grupo": "Novelas Ligera Fansub",
        }
        res = await WorkgroupService.resolve_book_workgroup_credits(
            book_id="book_uuid_999",
            raw_meta=raw,
        )

        template = (
            "📖 <b>{titulo}</b>\n"
            "👤 Traductor: {traductor}\n"
            "👥 Fansub: <a href=\"{grupo_link}\">{grupo}</a>\n"
            "🌐 Web Grupo: {grupo_web}\n"
            "💬 Discord Grupo: {grupo_discord}"
        )
        data = {"titulo": "Re:Zero Vol 1"}
        data.update(res)

        rendered = apply_publication_template(template, data)
        assert "👤 Traductor: Kiri (Traductor Individual)" in rendered
        assert "👥 Fansub: <a href=\"https://novelasligera.com\">Novelas Ligera Fansub</a>" in rendered
        assert "🌐 Web Grupo: https://novelasligera.com" in rendered
        assert "💬 Discord Grupo: https://discord.gg/novelas" in rendered


