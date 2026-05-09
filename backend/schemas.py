from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=100)


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OptionCreate(BaseModel):
    text: str = Field(min_length=1, max_length=200)


class PollCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    options: list[OptionCreate] = Field(min_length=2)
    expires_at: str  # ISO 8601 UTC


class PollUpdate(BaseModel):
    title: str | None = None
    options: list[OptionCreate] | None = None
    expires_at: str | None = None


class OptionOut(BaseModel):
    id: int
    text: str

    class Config:
        from_attributes = True


class PollOut(BaseModel):
    id: int
    title: str
    creator_id: int
    expires_at: str
    created_at: str
    updated_at: str
    options: list[OptionOut] = []

    class Config:
        from_attributes = True


class VoteRequest(BaseModel):
    option_id: int


class OptionResult(BaseModel):
    id: int
    text: str
    count: int


class PollResult(BaseModel):
    poll_id: int
    title: str
    total_votes: int
    options: list[OptionResult]
    expired: bool
