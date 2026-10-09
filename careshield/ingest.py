
from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    model_validator,
)


class StrictInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class PasteInput(StrictInput):
    """Validate a single pasted healthcare message."""

    text: str = Field(min_length=1, max_length=10000)
    channel: Literal["email", "sms"] | None = None
    sender: str | None = None
    subject: str | None = None
    headers: str | None = None


class UploadRow(PasteInput):
    """Validate one CSV or JSON upload row."""

    id: str = Field(min_length=1)
    received_at: datetime | None = None


class BatchInput(RootModel[list[UploadRow]]):
    """Validate a batch of uploaded messages."""

    @model_validator(mode="after")
    def validate_batch(self):
        if not 1 <= len(self.root) <= 500:
            raise ValueError(
                "Upload must contain between 1 and 500 rows."
            )

        ids = [row.id for row in self.root]

        if len(ids) != len(set(ids)):
            raise ValueError("Upload IDs must be unique.")

        return self


class QuestionnaireInput(StrictInput):
    """Validate answers to the 10 scam questionnaire questions."""

    contact_channel: Literal[
        "phone_call", "text", "email", "letter", "social_media"
    ]

    claimed_identity: Literal[
        "medicare",
        "medicaid_or_state_office",
        "insurance_company_or_agent",
        "hospital_or_doctors_office",
        "debt_collector",
        "pharmacy",
        "other",
    ]

    contacted_them_first: bool

    requested_information: Literal[
        "medicare_or_medicaid_number",
        "social_security_number",
        "bank_or_card_details",
        "password_or_code",
        "date_of_birth",
        "nothing",
    ]

    urgent_action: Literal["yes", "no", "not_sure"]

    payment_method: Literal[
        "gift_card", "wire", "payment_app",
        "crypto", "card", "none"
    ]

    threatened_consequence: Literal[
        "arrest_or_legal_action",
        "loss_of_coverage",
        "loss_of_benefits",
        "none",
    ]

    free_offer: Literal[
        "free_equipment_or_test",
        "zero_dollar_plan",
        "discount_medication",
        "none",
    ]

    refused_verification: Literal[
        "yes", "no", "did_not_ask"
    ]

    already_shared_or_paid: Literal[
        "information", "payment", "no"
    ]
