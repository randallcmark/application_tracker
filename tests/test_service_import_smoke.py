def test_ai_and_artefact_services_import() -> None:
    import app.services.ai  # noqa: F401
    import app.services.artefacts  # noqa: F401
    import app.services.competency_evidence  # noqa: F401
