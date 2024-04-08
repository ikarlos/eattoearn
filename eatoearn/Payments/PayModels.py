from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

from Orders.OrderModels import FoodOrderModel
from Plans.PlanModels import PlanModel

PAY_PLAN = 1
PAY_FOOD = 2


class PayModel(BaseModel):
    pay_type: int
    user_uid: str
    charges: Optional[float] = Field(default=0.0)
    plan_id: Optional[str] = Field(default=None)
    food_order: Optional[FoodOrderModel] = Field(default=None)


class PayResponseModel(BaseModel):
    status: int
    success: bool
    code: str
    message: str
    merchant_id: str
    pay_page_url: str
    pay_page_method: "str"
    merchant_transaction_id: str


class StatusModel(BaseModel):
    merchant_transaction_id: str
    pay_type: int
    user_uid: str
    #
    code: Optional[str]
    success: Optional[bool]


# END
