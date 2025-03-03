from typing import Literal

from pydantic import BaseModel, Field


class RichTextElement(BaseModel):
    type: str
    user_id: str | None = None
    text: str | None = None


class RichTextSection(BaseModel):
    type: Literal["rich_text_section"]
    elements: list[RichTextElement]


class Block(BaseModel):
    type: Literal["rich_text"]
    block_id: str
    elements: list[RichTextSection]


class SlackEvent(BaseModel):
    user: str
    type: str
    ts: str
    client_msg_id: str | None = None
    text: str
    team: str | None = None
    blocks: list[Block] | None = None
    channel: str
    event_ts: str


class SlackWebhookPayload(BaseModel):
    token: str | None = Field(None)
    team_id: str | None = Field(None)
    api_app_id: str | None = Field(None)
    event: SlackEvent | None = Field(None)
    type: str | None = Field(None)
    event_id: str | None = Field(None)
    event_time: int | None = Field(None)
    challenge: str | None = Field(None)
    subtype: str | None = Field(None)


class SlackMessageReaction(BaseModel):
    """Model for a reaction on a Slack message."""

    name: str
    users: list[str]
    count: int


class SlackMessage(BaseModel):
    """Model for a message in a Slack conversation."""

    user: str
    type: str
    ts: str
    client_msg_id: str | None = None
    text: str
    team: str | None = None
    blocks: list[Block] | None = None
    language: dict | None = None
    reactions: list[SlackMessageReaction] | None = None
    thread_ts: str | None = None
    reply_count: int | None = None
    reply_users_count: int | None = None
    latest_reply: str | None = None
    reply_users: list[str] | None = None
    is_locked: bool | None = None
    subscribed: bool | None = None
    parent_user_id: str | None = None
