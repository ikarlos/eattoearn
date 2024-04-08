from pydantic import BaseModel


class AdminWithId(BaseModel):
    admin_uid: str
    id: str


class UserWithId(BaseModel):
    user_uid: str
    id: str


class Availablity(BaseModel):
    ref: str = "eatoearn"
    admin_uid: str
    foods: bool = True
    plans: bool = True
    free_plan_delivery: bool = False
