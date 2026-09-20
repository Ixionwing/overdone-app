from overdone.config import Settings


def test_enrichment_rules_path_uses_override(tmp_path) -> None:
    rules = tmp_path / "custom.json"
    rules.write_text("{}")
    settings = Settings(
        enrichment_rules_path=str(rules),
        ollama_base_url=None,
    )
    assert settings.resolved_enrichment_rules_path() == rules


def test_catalog_path_uses_data_dir(tmp_path) -> None:
    catalog = tmp_path / "exercises.json"
    catalog.write_text("[]")
    settings = Settings(data_dir=str(tmp_path), ollama_base_url=None)
    assert settings.resolved_catalog_path() == catalog


def test_catalog_prefers_free_exercise_db(tmp_path) -> None:
    (tmp_path / "exercises.json").write_text("[]")
    nested = tmp_path / "free-exercise-db"
    nested.mkdir()
    full = nested / "exercises.json"
    full.write_text("[{}]")
    settings = Settings(data_dir=str(tmp_path), ollama_base_url=None)
    assert settings.resolved_catalog_path() == full
