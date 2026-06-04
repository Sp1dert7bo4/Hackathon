from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class Intent(BaseModel):
    intent: str = "food_recommendation"
    cuisine: str | None = None
    location: str | None = None
    budget: int | None = None
    time: str | None = None
    people: int | None = None
    diet: str | None = None
    confidence: float = 0.0
    low_confidence: bool = False
    missing_fields: list[str] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)


class IntentRequest(BaseModel):
    text: str


class SearchRequest(BaseModel):
    intent: str = "food_recommendation"
    cuisine: str | None = None
    location: str | None = None
    budget: int | None = None
    time: str | None = None
    people: int | None = None
    diet: str | None = None
    user_latitude: float | None = None
    user_longitude: float | None = None
    simulate_failure: bool = False


class Restaurant(BaseModel):
    id: str
    name: str
    address: str
    district: str
    distance_km: float
    rating: float
    price_min: int
    price_max: int
    cuisine_tags: list[str]
    status: str = "open"
    review_count: int
    image_url: str
    source: str = "dataset"
    last_updated: date
    phone: str | None = None
    hours: str | dict[str, Any] | None = None
    about_options: dict[str, Any] | list[Any] | None = None
    review_keywords: list[str] = Field(default_factory=list)
    latitude: float | None = None
    longitude: float | None = None

    @property
    def price_range(self) -> str:
        return f"{self.price_min:,}-{self.price_max:,} VND".replace(",", ".")


class RankedRestaurant(BaseModel):
    restaurant: Restaurant
    rank: int
    score: float
    components: dict[str, float]
    reasons: list[str]


class SearchResponse(BaseModel):
    restaurants: list[Restaurant]
    source: str
    stale_data: bool = False
    warning: str | None = None


class RankRequest(BaseModel):
    restaurants: list[Restaurant]
    user_profile: dict[str, Any] = Field(default_factory=dict)


class RankResponse(BaseModel):
    ranked_restaurants: list[RankedRestaurant]
    explanation: str
    warning: str | None = None


class ConversationState(BaseModel):
    food_type: str | None = None
    location: str | None = None
    budget: int | None = None
    occasion: str | None = None
    user_latitude: float | None = None
    user_longitude: float | None = None


class ChatRequest(BaseModel):
    text: str
    user_id: str = "demo-user"
    conversation_state: ConversationState | None = None
    preferences: dict[str, Any] = Field(default_factory=dict)
    user_latitude: float | None = None
    user_longitude: float | None = None
    simulate_failure: bool = False


class ChatResponse(BaseModel):
    status: str
    intent: Intent
    conversation_state: ConversationState = Field(default_factory=ConversationState)
    ranked_restaurants: list[RankedRestaurant] = Field(default_factory=list)
    explanation: str | None = None
    questions: list[str] = Field(default_factory=list)
    warning: str | None = None
    ai_provider: str = "rules"
    can_use_distance: bool = False


class FeedbackRequest(BaseModel):
    user_id: str = "demo-user"
    feedback: str
    reason: str | None = None
    last_intent: Intent
    shown_restaurant_ids: list[str] = Field(default_factory=list)


class FeedbackResponse(BaseModel):
    updated_preferences: dict[str, Any]
    next_action: str
    ranked_restaurants: list[RankedRestaurant]
    explanation: str


class DirectionsRequest(BaseModel):
    restaurant_id: str
    user_latitude: float
    user_longitude: float


class DirectionsResponse(BaseModel):
    restaurant_name: str
    restaurant_address: str
    restaurant_phone: str | None = None
    restaurant_hours: str | dict[str, Any] | None = None
    distance_km: float | None = None
    google_maps_link: str | None = None
    error: str | None = None
