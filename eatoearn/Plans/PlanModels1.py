from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, timedelta
from pytz import utc

from Foods.FoodModels import FoodModel
from Users.UserModel import PyObjectId


class PlanBenifitsModel(BaseModel):
    user_uid: str
    plan_benifits: Optional[List[FoodModel]] = None
    plan_benifits_redeemed: Optional[bool] = None
    expire_at: datetime = datetime.now(utc) + timedelta(hours=48)


class PlanModel(BaseModel):
    # USER Ref
    user_uid: Optional[str] = None
    # PLAN
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    plan_name: str
    plan_price: int
    plan_bg: Optional[str] = "#3366CC"
    active: Optional[bool] = Field(default=False)
    plan_benifit_ids: Optional[List[str]] = None
    plan_benifits: Optional[List[FoodModel]] = None
    #
    plan_l1_pct: Optional[float] = None
    plan_l2_pct: Optional[float] = None
    #
    model_config = ConfigDict(
        json_encoders={ObjectId: str},
        arbitrary_types_allowed=True,
    )


class PlanWithAdmin(BaseModel):
    admin_uid: str
    plan: PlanModel
