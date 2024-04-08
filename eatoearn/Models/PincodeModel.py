from argparse import OPTIONAL
from typing import Optional
from pydantic import BaseModel, Field

from Users.UserModel import PyObjectId


class PincodeRowModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    index: int
    pincode: str
    charges: float


class UpdatePincodeRowModel(BaseModel):
    index: Optional[int] = None
    pincode: Optional[str] = None
    charges: Optional[float] = None


class UpdatePincodeAdmin(BaseModel):
    admin_uid: str
    pincode: UpdatePincodeRowModel
