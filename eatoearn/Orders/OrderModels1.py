from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from Foods.FoodModels import FoodModel
from Users.UserModel import Address, PyObjectId


class FoodOrderModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    # User Ref
    user_uid: str
    billed_to: str
    total: float
    delivery_charges: float
    platform_fee: float
    food_ordered_at: Optional[datetime] = datetime.now()
    food_order_successfull: Optional[bool] = Field(default=False)
    food_delivered: Optional[bool] = Field(default=False)
    merchant_transaction_id: Optional[str] = Field(default=None)
    address: Address
    suggestion: Optional[str] = ""
    #
    is_redeem: Optional[bool] = False
    #
    items: List[FoodModel]


class FoodOrderUpdateModel(BaseModel):
    # User Ref
    user_uid: Optional[str] = None
    billed_to: Optional[str] = None
    total: Optional[float] = None
    delivery_charges: Optional[float] = None
    platform_fee: Optional[float] = None
    food_ordered_at: Optional[datetime] = None
    food_order_successfull: Optional[bool] = None
    food_delivered: Optional[bool] = None
    merchant_transaction_id: Optional[str] = None
    address: Optional[Address] = None
    suggestion: Optional[str] = None
    #
    is_redeem: Optional[bool] = None
    #
    items: Optional[List[FoodModel]] = None


class FoodOrderModelAdmin(BaseModel):
    admin_uid: str
    food_order_model: FoodOrderUpdateModel
