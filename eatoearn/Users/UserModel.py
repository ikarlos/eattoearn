from typing import Annotated, Optional
from bson import ObjectId
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

PyObjectId = Annotated[str, BeforeValidator(str)]


class UserBankModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    bank_acc: str = Field()
    bank_ifsc: str = Field()


class Address(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_uid: Optional[str] = Field(default=None)
    address_type: Optional[str] = Field(default=None)
    address_detected: Optional[str] = Field(default=None)
    address_complete: Optional[str] = Field(default=None)
    address_pincode: Optional[str] = Field(default=None)
    address_floor: Optional[str] = Field(default=None)
    address_landmark: Optional[str] = Field(default=None)


class UserModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_uid: str
    user_mode: str = "customer"
    user_name: str = Field()
    user_phone: str = Field()
    user_email: str = Field()
    user_ID: Optional[str] = Field(default=None)
    user_active_plan_id: Optional[str] = Field(default=None)
    user_referer_uid: Optional[str] = Field(default=None)
    user_referal_completed: bool = Field(default=False)
    user_bank: Optional[UserBankModel] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class UpdateUserModel(BaseModel):
    user_mode: Optional[str] = None
    user_name: Optional[str] = None
    user_phone: Optional[str] = None
    user_email: Optional[str] = None
    user_referer_uid: Optional[str] = None
    user_referal_completed: Optional[bool] = None
    user_bank: Optional[UserBankModel] = None

    model_config = ConfigDict(
        json_encoders={ObjectId: str},
        arbitrary_types_allowed=True,
    )


#
