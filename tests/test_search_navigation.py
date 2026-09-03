import pytest
from core.state_manager import StateManager
from services.library_ui.catalog_builders import build_search_results_rich_blocks


def test_search_results_callback_data():
    """Verifies that series buttons in search results use the 24-char hash prefix to remain within Telegram's 64-byte limit."""
    series_results = [
        {
            "title": "Mushoku Tensei",
            "name": "Mushoku Tensei: Isekai Ittara Honki Dasu",
            "series_hash": "ad19c76f422d53773c2541909febd69595eceed777ce4711630f4aa46a8ca9e0",
            "book_count": 19,
        }
    ]
    books_results = [
        {
            "key": "book1234",
            "title": "Standalone Book",
        }
    ]

    blocks = build_search_results_rich_blocks("tensei", series_results, books_results)

    btn_blocks = [b for b in blocks if b.get("type") == "buttons"]
    series_btn = btn_blocks[0]["buttons"][0]

    # Callback must be col|<24-char-hash>
    expected_cb = "col|ad19c76f422d53773c254190"
    assert series_btn["callback_data"] == expected_cb
    assert len(series_btn["callback_data"].encode("utf-8")) <= 64


def test_state_manager_key_lookups():
    """Verifies StateManager handles both string and integer keys seamlessly."""
    sm = StateManager()
    uid = 12345
    st = sm.get_user_state(uid)

    st["series_map"] = {0: "hash_0", "1": "hash_1"}
    st["colecciones"] = {2: {"href": "local_series|hash_2"}}

    # Int lookup with str key
    assert sm.get_series_by_key("0", uid) == "hash_0"
    assert sm.get_series_by_key(0, uid) == "hash_0"

    # Str lookup with int key
    assert sm.get_series_by_key(1, uid) == "hash_1"
    assert sm.get_series_by_key("1", uid) == "hash_1"

    # Colecciones href lookup
    assert sm.get_series_by_key("2", uid) == "hash_2"
    assert sm.get_series_by_key(2, uid) == "hash_2"
