from app.services.contact_extractor import ContactExtractor


def test_extract_contacts() -> None:
    extractor = ContactExtractor()
    result = extractor.extract("Email hello@example.com, call +91 98765 43210, Instagram https://instagram.com/example")
    assert "hello@example.com" in result.emails
    assert result.phones
    assert result.social_links["instagram"]
