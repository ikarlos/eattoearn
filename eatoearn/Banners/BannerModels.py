from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field

from Users.UserModel import PyObjectId


class BannerModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    banner_img_url: str
    line_title: str
    headline: str
    line_action: Optional[str] = "Order now to avail benifits"
    offer_tag: Optional[str] = None


class BannerWithAdmin(BaseModel):
    admin_uid: str
    banner: BannerModel
