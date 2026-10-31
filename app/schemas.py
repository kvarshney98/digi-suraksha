from typing import Literal
from pydantic import BaseModel, Field, model_validator
Language = Literal["en", "hi"]
class AnalysisRequest(BaseModel):
    content: str = Field(min_length=1, max_length=30000)
    input_type: Literal["auto", "text", "url", "email"] = "auto"
    language: Language = "en"
    remote_consent: bool = False
class AIExplanation(BaseModel):
    summary: str = Field(max_length=2000)
    evidence_ids: list[str] = Field(max_length=30)
class Incident(BaseModel):
    description: str = Field(min_length=5, max_length=10000)
    outcome: Literal["attempt", "money", "credentials"] = "attempt"
    date: str = Field(default="", max_length=40)
    time: str = Field(default="", max_length=5)
    date_unknown: bool = False
    time_unknown: bool = False
    time_approximate: bool = False
    pincode: str = Field(default="", max_length=6)
    state: str = Field(default="", max_length=80)
    city: str = Field(default="", max_length=100)
    locality: str = Field(default="", max_length=150)
    sender_phone: str = Field(default="", max_length=30)
    sender_email: str = Field(default="", max_length=254)
    record_id: str | None = None
    amount: str = Field(default="", max_length=40)
    reference: str = Field(default="", max_length=150)
    evidence: str = Field(default="", max_length=2000)
    acknowledgement: str = Field(default="", max_length=150)
    language: Language = "en"
    save: bool = False

    @model_validator(mode="after")
    def validate_incident(self):
        import re
        from datetime import date, time
        from uuid import UUID
        if bool(self.date) == self.date_unknown:
            raise ValueError("Enter incident date or mark date unknown / दिनांक लिखें या अज्ञात चुनें")
        if bool(self.time) == self.time_unknown:
            raise ValueError("Enter incident time or mark time unknown / समय लिखें या अज्ञात चुनें")
        if self.date:
            try: date.fromisoformat(self.date)
            except ValueError: raise ValueError("Invalid incident date / अमान्य दिनांक")
        if self.time:
            if not re.fullmatch(r"[0-2][0-9]:[0-5][0-9]", self.time):
                raise ValueError("Invalid incident time / अमान्य समय")
            time.fromisoformat(self.time)
        if self.time_unknown and self.time_approximate:
            raise ValueError("Unknown time cannot also be approximate / अज्ञात समय अनुमानित नहीं हो सकता")
        if self.pincode and not re.fullmatch(r"[1-9][0-9]{5}", self.pincode):
            raise ValueError("Enter a six-digit Indian PIN code / छह अंकों का पिन कोड लिखें")
        if self.sender_phone and not re.fullmatch(r"\+?[0-9][0-9 ()-]{5,28}",self.sender_phone):
            raise ValueError("Invalid sender phone / अमान्य फोन नंबर")
        if self.sender_email and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",self.sender_email):
            raise ValueError("Invalid sender email / अमान्य ईमेल")
        if self.record_id:
            UUID(self.record_id)
        return self
