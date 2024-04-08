from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

from Users.UserModel import PyObjectId


class IncomeModel(BaseModel):
    user_uid: str
    active_income: float = 0.0
    passive_income: float = 0.0


class EarningsModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_uid: str
    l2_referrer_idf: Optional[str] = Field(default=None)
    referrer_idf: str
    buyer_idf: str
    amount: float
    earned_date: datetime
    mode: Optional[str]
    bought_price: Optional[float]
    payed: bool | None = False

    model_config = ConfigDict(
        json_encoders={ObjectId: str},
        arbitrary_types_allowed=True,
    )


class UpdateEarningsModel(BaseModel):
    user_uid: Optional[str] = None
    referrer_idf: Optional[str] = None
    buyer_idf: Optional[str] = None
    amount: Optional[float] = None
    earned_date: Optional[datetime] = None
    mode: Optional[str] = None
    bought_price: Optional[float] = None
    payed: Optional[bool] = None

    class Config:
        json_encoders = {ObjectId: str}
        arbitrary_types_allowed = True


class UpdateEarningsAdmin(BaseModel):
    admin_uid: str
    update_earning_model: UpdateEarningsModel


# END
