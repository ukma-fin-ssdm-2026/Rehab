from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator, model_validator

MessageStyle = Literal["formal", "humorous", "zen", "strict"]


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    name: str
    nickname: str
    email: str
    has_avatar: bool
    avatar_version: int | None = Field(ge=1)
    email_reminders_enabled: bool
    message_style: MessageStyle


class ProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=100)
    nickname: str | None = Field(default=None, min_length=1, max_length=50)

    @field_validator("name", "nickname", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> object:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Поле не може бути порожнім")
        return value.strip()

    @model_validator(mode="after")
    def require_one_field(self):
        if not self.model_fields_set:
            raise ValueError("Потрібне хоча б одне поле")
        return self


class ProfilePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def require_new_password(self):
        if self.current_password == self.new_password:
            raise ValueError("Новий пароль має відрізнятися від поточного")
        return self


class ProfilePreferencesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email_reminders_enabled: StrictBool | None = None
    message_style: MessageStyle | None = None

    @field_validator("email_reminders_enabled", "message_style", mode="before")
    @classmethod
    def reject_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("Поле не може бути null")
        return value

    @model_validator(mode="after")
    def require_one_field(self):
        if not self.model_fields_set:
            raise ValueError("Потрібне хоча б одне поле")
        return self


class AvatarUploadOut(BaseModel):
    has_avatar: Literal[True]
    avatar_version: int = Field(ge=1)


class AvatarDataOut(BaseModel):
    data_url: str
    avatar_version: int = Field(ge=1)
