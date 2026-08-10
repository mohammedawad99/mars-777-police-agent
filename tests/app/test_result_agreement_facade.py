"""The façade publishes ResultAgreement and none of its support values."""

from mars777_police.app import peer_final_messages, peer_messages, result_values


def test_facade_exports_the_defining_class_object() -> None:
    assert peer_messages.ResultAgreement is peer_final_messages.ResultAgreement


def test_result_agreement_is_listed_once_in_all() -> None:
    assert peer_messages.__all__.count("ResultAgreement") == 1


def test_facade_all_stays_sorted_and_unique() -> None:
    assert peer_messages.__all__ == sorted(peer_messages.__all__)
    assert len(set(peer_messages.__all__)) == len(peer_messages.__all__)


def test_facade_hides_every_result_support_value() -> None:
    support = {
        "ParticipantGitCommits",
        "ParticipantTokenUsage",
        "ResultContributionEntry",
        "ResultContribution",
        "InvalidResultValueError",
    }
    assert not support & set(peer_messages.__all__)
    for name in support:
        assert not hasattr(peer_messages, name)
        assert hasattr(result_values, name)


def test_facade_defines_no_class_of_its_own() -> None:
    for name in peer_messages.__all__:
        assert getattr(peer_messages, name).__module__ != peer_messages.__name__


def test_no_digest_response_class_was_introduced() -> None:
    for absent in ("ResultAck", "ResultAgreementAck", "ResultResponse", "ResultAccepted"):
        assert not hasattr(peer_messages, absent)
        assert not hasattr(peer_final_messages, absent)
        assert not hasattr(result_values, absent)
