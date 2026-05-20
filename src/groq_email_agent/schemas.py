from pydantic import BaseModel

class EmailState(BaseModel):
    sender: str
    subject: str
    body: str
    triage: str | None = None
    draft: str | None = None
    approved: bool | None = None