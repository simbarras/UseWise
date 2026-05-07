import pytest
from usewise.llm.risk import (
    ANSWER_KEYS,
    WEIGHTS,
    calculate_risk,
    flag_risk,
    parse_months,
    retention_risk,
)


class TestParseMonths:
    def test_parse_months_less_than_1_month(self) -> None:
        assert parse_months("< 1 month") == 0.5

    def test_parse_months_1_6_months(self) -> None:
        assert parse_months("1-6 months") == 3.5

    def test_parse_months_6_12_months(self) -> None:
        assert parse_months("6-12 months") == 9.0

    def test_parse_months_1_3_years(self) -> None:
        assert parse_months("1-3 years") == 18.0

    def test_parse_months_3_plus_years(self) -> None:
        assert parse_months("3+ years") == 48.0

    def test_parse_months_indefinitely(self) -> None:
        assert parse_months("Indefinitely") is None

    def test_parse_months_when_account_deleted(self) -> None:
        assert parse_months("When account deleted") is None

    def test_parse_months_none(self) -> None:
        assert parse_months(None) is None

    def test_parse_months_empty_string(self) -> None:
        assert parse_months("") is None

    def test_parse_months_regex_years(self) -> None:
        assert parse_months("2 years") == 24.0

    def test_parse_months_regex_months(self) -> None:
        assert parse_months("3 months") == 3.0

    def test_parse_months_regex_days(self) -> None:
        assert parse_months("30 days") == pytest.approx(1.0, abs=0.01)

    def test_parse_months_case_insensitive(self) -> None:
        assert parse_months("INDEFINITELY") is None
        assert parse_months("When Account Deleted") is None


class TestFlagRisk:
    def test_flag_risk_true(self) -> None:
        risk, is_unclear = flag_risk(answer=True)
        assert risk == 0.0
        assert is_unclear is False

    def test_flag_risk_false(self) -> None:
        risk, is_unclear = flag_risk(answer=False)
        assert risk == 1.0
        assert is_unclear is False

    def test_flag_risk_none(self) -> None:
        risk, is_unclear = flag_risk(answer=None)
        assert risk == 0.5
        assert is_unclear is True


class TestRetentionRisk:
    def test_retention_risk_none(self) -> None:
        risk, is_unclear = retention_risk(None)
        assert risk == 0.6
        assert is_unclear is True

    def test_retention_risk_less_than_1_month(self) -> None:
        risk, is_unclear = retention_risk("< 1 month")
        assert risk == 0.0
        assert is_unclear is False

    def test_retention_risk_1_6_months(self) -> None:
        risk, is_unclear = retention_risk("1-6 months")
        assert risk == 0.25
        assert is_unclear is False

    def test_retention_risk_6_12_months(self) -> None:
        risk, is_unclear = retention_risk("6-12 months")
        assert risk == 0.5
        assert is_unclear is False

    def test_retention_risk_1_3_years(self) -> None:
        risk, is_unclear = retention_risk("1-3 years")
        assert risk == 0.75
        assert is_unclear is False

    def test_retention_risk_3_plus_years(self) -> None:
        risk, is_unclear = retention_risk("3+ years")
        assert risk == 1.0
        assert is_unclear is False

    def test_retention_risk_indefinitely(self) -> None:
        risk, is_unclear = retention_risk("Indefinitely")
        assert risk == 0.6
        assert is_unclear is True


class TestCalculateRisk:
    def test_calculate_risk_all_safe(self) -> None:
        answers = {
            "sharing": True,
            "tracking": True,
            "retention": "< 1 month",
            "deletion": True,
            "policy_changes": True,
        }
        score = calculate_risk(answers)
        assert score == 1

    def test_calculate_risk_all_risky(self) -> None:
        answers = {
            "sharing": False,
            "tracking": False,
            "retention": "3+ years",
            "deletion": False,
            "policy_changes": False,
        }
        score = calculate_risk(answers)
        assert score == 5

    def test_calculate_risk_mixed(self) -> None:
        answers = {
            "sharing": True,
            "tracking": False,
            "retention": "6-12 months",
            "deletion": True,
            "policy_changes": False,
        }
        score = calculate_risk(answers)
        assert 1 <= score <= 5

    def test_calculate_risk_with_unclear(self) -> None:
        answers = {
            "sharing": None,
            "tracking": None,
            "retention": "Indefinitely",
            "deletion": None,
            "policy_changes": None,
        }
        score = calculate_risk(answers)
        assert 1 <= score <= 5

    def test_calculate_risk_respects_weights(self) -> None:
        assert WEIGHTS["sharing"] == 0.30
        assert WEIGHTS["tracking"] == 0.20
        assert WEIGHTS["retention"] == 0.25
        assert WEIGHTS["deletion"] == 0.15
        assert WEIGHTS["policy_changes"] == 0.10
        assert sum(WEIGHTS.values()) == 1.0

    def test_calculate_risk_returns_int(self) -> None:
        answers = {
            "sharing": True,
            "tracking": True,
            "retention": "< 1 month",
            "deletion": True,
            "policy_changes": True,
        }
        score = calculate_risk(answers)
        assert isinstance(score, int)

    def test_calculate_risk_in_valid_range(self) -> None:
        test_cases = [
            {
                "sharing": True,
                "tracking": True,
                "retention": "< 1 month",
                "deletion": True,
                "policy_changes": True,
            },
            {
                "sharing": False,
                "tracking": False,
                "retention": "3+ years",
                "deletion": False,
                "policy_changes": False,
            },
            {
                "sharing": None,
                "tracking": None,
                "retention": "Indefinitely",
                "deletion": None,
                "policy_changes": None,
            },
        ]
        for answers in test_cases:
            score = calculate_risk(answers)
            assert 1 <= score <= 5


class TestAnswerKeys:
    def test_answer_keys_count(self) -> None:
        assert len(ANSWER_KEYS) == 5

    def test_answer_keys_content(self) -> None:
        expected = ["sharing", "tracking", "retention", "deletion", "policy_changes"]
        assert expected == ANSWER_KEYS
