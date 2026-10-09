
import pytest
from pydantic import ValidationError

from careshield.ingest import (
    BatchInput,
    PasteInput,
    QuestionnaireInput,
    UploadRow,
)


def test_valid_paste():
    message = PasteInput(
        text="Verify your Medicare number immediately!",
        channel="sms",
    )
    assert message.channel == "sms"


def test_message_too_long():
    with pytest.raises(ValidationError):
        PasteInput(text="A" * 10001)


def test_empty_message():
    with pytest.raises(ValidationError):
        PasteInput(text="")


def test_unknown_upload_column():
    with pytest.raises(ValidationError):
        UploadRow(
            id="m001",
            text="Test message",
            unknown_field="invalid",
        )


def test_valid_batch():
    batch = BatchInput.model_validate([
        {"id": "m001", "text": "Test message 1"},
        {"id": "m002", "text": "Test message 2"},
    ])
    assert len(batch.root) == 2


def test_duplicate_upload_ids():
    with pytest.raises(ValidationError):
        BatchInput.model_validate([
            {"id": "m001", "text": "Message 1"},
            {"id": "m001", "text": "Message 2"},
        ])


def test_valid_questionnaire():
    answers = QuestionnaireInput(
        contact_channel="text",
        claimed_identity="medicare",
        contacted_them_first=False,
        requested_information="medicare_or_medicaid_number",
        urgent_action="yes",
        payment_method="none",
        threatened_consequence="none",
        free_offer="none",
        refused_verification="did_not_ask",
        already_shared_or_paid="no",
    )

    assert answers.claimed_identity == "medicare"
