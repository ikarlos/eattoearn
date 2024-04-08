from typing import Optional
from pydantic import BaseModel, Field

from Users.UserModel import PyObjectId


class FeaturedModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    featured_img_url: str
    title: str


class UpdateFeaturedModel(BaseModel):
    featured_img_url: Optional[str]
    title: Optional[str]


class FeaturedWithAdmin(BaseModel):
    admin_uid: str
    featured: FeaturedModel


class UpdateFeaturedWithAdmin(BaseModel):
    admin_uid: str
    featured: UpdateFeaturedModel
