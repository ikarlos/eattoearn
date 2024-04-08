from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field
from Users.UserModel import PyObjectId


class FoodType(BaseModel):
    type_name: str
    type_price: float


class FavouriteFoodModel(BaseModel):
    food_id: Optional[str]
    user_uid: Optional[str]


class FoodModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    food_name: str
    food_description: Optional[str] = None
    food_category: Optional[str] = None
    food_thumb_url: str
    food_qty: Optional[int] = None
    food_type: Optional[str] = None
    food_price: Optional[float] = None
    food_types: Optional[List[FoodType]] = None
    expire_at: Optional[datetime] = None
    user_uid: Optional[str] = None
    offer_tag: Optional[str] = None
    for_plan: Optional[bool] = False
    #
    model_config = ConfigDict(
        json_encoders={ObjectId: str},
        arbitrary_types_allowed=True,
    )


class UpdateFoodModel(BaseModel):
    food_name: Optional[str] = None
    food_description: Optional[str] = None
    food_category: Optional[str] = None
    food_thumb_url: Optional[str] = None
    food_qty: Optional[int] = None
    food_type: Optional[str] = None
    food_types: Optional[List[FoodType]] = None
    expire_at: Optional[datetime] = None
    user_uid: Optional[str] = None
    offer_tag: Optional[str] = None
    for_plan: Optional[bool] = False
    #
    model_config = ConfigDict(
        json_encoders={ObjectId: str},
        arbitrary_types_allowed=True,
    )


class FoodAdmin(BaseModel):
    admin_uid: str
    food: FoodModel


class FoodUpdateAdmin(BaseModel):
    admin_uid: str
    update_food_model: UpdateFoodModel


class FoodDeleteModel(BaseModel):
    admin_uid: str
    id: str
