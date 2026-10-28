from pydantic import BaseModel, ConfigDict, Field


class LeadIn(BaseModel):
    """Incoming lead payload from the webhook."""

    # Trim spaces so "   " is treated as empty and fails min_length.
    model_config = ConfigDict(str_strip_whitespace=True)

    external_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=5000)
    source: str = Field(min_length=1, max_length=50)
