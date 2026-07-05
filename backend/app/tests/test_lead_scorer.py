from app.services.lead_scorer import LeadScorer


def test_lead_scorer_returns_bounded_scores() -> None:
    scorer = LeadScorer()
    result = scorer.score(
        website_exists=True,
        ssl_enabled=True,
        social_presence_count=2,
        contact_count=3,
        seo_signals=2,
        performance_score=80,
        review_count=10,
        rating=4.2,
    )
    assert 0 <= result.digital_presence_score <= 100
    assert 0 <= result.lead_opportunity_score <= 100
