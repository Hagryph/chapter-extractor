from __future__ import annotations

import pytest

from chapter_extractor.domain.shortcuts import (
    ShortcutCatalog,
    ShortcutCategory,
)


class TestShortcutCatalog:
    def test_all_returns_at_least_one(self) -> None:
        assert len(ShortcutCatalog.all()) >= 1

    def test_ids_are_unique(self) -> None:
        ids = [s.id for s in ShortcutCatalog.all()]
        assert len(ids) == len(set(ids))

    def test_key_sequences_are_unique(self) -> None:
        # Different actions must not bind the same key.
        keys = [s.key_sequence for s in ShortcutCatalog.all()]
        assert len(keys) == len(set(keys))

    def test_by_id_returns_correct_spec(self) -> None:
        spec = ShortcutCatalog.by_id("view.cycle_focus")
        assert spec.label == "Toggle Focus Mode"
        assert spec.key_sequence == "F11"

    def test_by_id_unknown_raises(self) -> None:
        with pytest.raises(KeyError):
            ShortcutCatalog.by_id("nope.does.not.exist")

    def test_categories_in_order_no_dupes(self) -> None:
        cats = ShortcutCatalog.categories_in_order()
        assert len(cats) == len(set(cats))

    def test_by_category_returns_only_that_category(self) -> None:
        view_only = ShortcutCatalog.by_category(ShortcutCategory.VIEW)
        assert all(s.category == ShortcutCategory.VIEW for s in view_only)
        assert len(view_only) > 0

    def test_every_spec_has_status_tip(self) -> None:
        # Status tips drive the status bar + the cheat-sheet dialog tooltips,
        # so every spec must have one.
        for spec in ShortcutCatalog.all():
            assert spec.status_tip.strip(), f"{spec.id} has empty status_tip"
