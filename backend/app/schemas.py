"""Request models (Pydantic). These are schemas only; there is no behaviour here."""

from typing import Literal

from pydantic import BaseModel, Field

Lang = Literal["en", "hi", "mr"]
Short = Field(default="", max_length=200)
Items = Field(default_factory=list, max_length=10)


class TextIn(BaseModel):
    text: str = Field(max_length=20000)
    lang: Lang = "en"


class FieldsIn(BaseModel):
    amount: str = Short
    bank: str = Short
    account: str = Short
    when: str = Short
    mobile: str = Short
    name: str = Short
    location: str = Short
    description: str = Field(default="", max_length=1500)
    utrs: list[str] = Items
    scamPhones: list[str] = Items
    scamUpi: list[str] = Items
    scamLinks: list[str] = Items


class ValidateIn(BaseModel):
    fields: FieldsIn


class PackIn(BaseModel):
    fields: FieldsIn
    mode: Literal["A", "B"] = "A"
    lang: Lang = "en"
    elapsed: Literal["lt15", "m30", "h1to2", "sameDay", "earlier"] = "m30"


class AskIn(BaseModel):
    question: str = Field(max_length=300)
    lang: Lang = "en"


class ReportIn(BaseModel):
    page: str = Field(default="", max_length=100)
    note: str = Field(min_length=1, max_length=500)
