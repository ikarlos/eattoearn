import base64
import json
import os
import shutil
import threading
from typing import List
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from fastapi import (
    FastAPI,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from motor import motor_asyncio
from Banners.BannerModels import BannerModel, BannerWithAdmin
from Earnings.EarningModels import (
    EarningsModel,
    IncomeModel,
    UpdateEarningsAdmin,
)
from Env.settings import Settings
from Featured.FeaturedModels import (
    FeaturedModel,
    FeaturedWithAdmin,
    UpdateFeaturedWithAdmin,
)
from Foods.FoodModels import (
    FavouriteFoodModel,
    FoodAdmin,
    FoodDeleteModel,
    FoodModel,
    FoodUpdateAdmin,
)
from Models.GenModel import AdminWithId, Availablity, UserWithId
from Models.PhonePeCallbackModel import PhonePeCallback
from Models.PincodeModel import (
    PincodeRowModel,
    UpdatePincodeAdmin,
)
from Models.SettingModels import SettingsModel, StatisticsModel, UpdateSettingsModel
from Orders.OrderModels import FoodOrderModel, FoodOrderModelAdmin
from Payments.PayModels import (
    PAY_FOOD,
    PAY_PLAN,
    PayModel,
    PayResponseModel,
    StatusModel,
)
from PhonePay.phonepe_utils import PhonePeClient
from Plans.PlanModels import PlanBenifitsModel, PlanModel, PlanWithAdmin
from Plans.benifits import insert_plan_benifits
from Users.UserModel import Address, UpdateUserModel, UserModel
from phonepe.sdk.pg.payments.v1.models.response.phonepe_response import PhonePeResponse
from Utils.utils import format_number_to_fixed_length, get_next_sequence
from constants.constants import *
from Earnings.earnings import insert_rewards, insert_rewards_food, update_recents
from Foods.foods import get_plans_with_benifits
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from Email.email_utils import (
    send_plan_success,
    send_plan_admin,
    send_order_success,
    send_food_admin,
    send_redeem_success,
)

app = FastAPI()
settings = Settings()
client = motor_asyncio.AsyncIOMotorClient(settings.db_url)
db = client.get_database(settings.db_name)
phonepeClient = PhonePeClient(settings=settings)

# Collections
ids_collection = db.get_collection("user_ids")
user_collection = db.get_collection("users")
address_collection = db.get_collection("addresses")
bank_collection = db.get_collection("bank")
user_plans_collection = db.get_collection("user_plans")
#
plan_collection = db.get_collection("plans")
#
benifit_collection = db.get_collection("benifits")
benifit_collection.create_index([("expire_at", ASCENDING)], expireAfterSeconds=0)
#
setting_collection = db.get_collection("settings")
#
food_collection = db.get_collection("foods")
#
recent_collection = db.get_collection("recents")
recent_collection.create_index([("expire_at", ASCENDING)], expireAfterSeconds=0)
#
favourite_collection = db.get_collection("favourites")
order_collection = db.get_collection("orders")
#
banner_collection = db.get_collection("banners")
featured_collection = db.get_collection("featured")
earning_collection = db.get_collection("earnings")
#
pincode_collection = db.get_collection("pincodes")
income_collection = db.get_collection("income")
#
transaction_collection = db.get_collection("transaction")
availablity_collection = db.get_collection("availablity")


origins = ["http://localhost:8080", "http://localhost:3000", "http://localhost:3001"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"Hello": "World"}


# UTIL FUNCS
async def is_admin(user_uid: str):
    user_ = await user_collection.find_one({"user_uid": user_uid})
    return user_ is not None and user_.get("user_mode") == "admin"


# Users
@app.post(
    "/api/users/",
    response_description="Add new user",
    status_code=status.HTTP_201_CREATED,
)
async def create_user(user: UserModel):
    # fetching the referrer profile ...
    referrer_ = await user_collection.find_one({"user_ID": user.user_referer_uid})
    if referrer_ is not None:
        referrer_["_id"] = str(referrer_["_id"])
        referrer_modelled: UserModel = UserModel.model_validate(referrer_)
        user.user_referer_uid = referrer_modelled.user_uid

    #
    seq = await get_next_sequence(collection_IDS=ids_collection)
    user.user_ID = format_number_to_fixed_length(seq)
    await user_collection.insert_one(user.model_dump(by_alias=True, exclude=["id"]))
    return {"status": CODE_SUCCESS}


@app.get(
    "/api/users/{id}",
    response_description="Get a single user",
    response_model=UserModel,
    response_model_by_alias=False,
)
async def show_user(id: str):
    if (user := await user_collection.find_one({"user_uid": id})) is not None:
        return user

    raise HTTPException(status_code=404, detail=f"User {id} not found")


@app.get(
    "/api/users/",
    response_description="Get users",
    response_model=List[UserModel],
    response_model_by_alias=False,
)
async def show_users_search(email: str, user_uid: str):
    if await is_admin(user_uid=user_uid) == True:
        users = (
            await user_collection.find(
                {"user_email": {"$regex": email, "$options": "i"}}
            )
            .limit(3)
            .to_list(3)
        )
        return users or []

    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


@app.put(
    "/api/users/{id}",
    response_description="Update a user",
)
async def update_user(id: str, user: UpdateUserModel):
    user = {k: v for k, v in user.model_dump(by_alias=True).items() if v is not None}
    if len(user) >= 1:
        update_result = await user_collection.find_one_and_update(
            {"user_uid": id},
            {"$set": user},
            return_document=ReturnDocument.AFTER,
        )
        if update_result is not None:
            return {"status": CODE_SUCCESS}
        else:
            raise HTTPException(status_code=404, detail=f"User {id} not found")

    return {"status": CODE_ERROR}


# Foods
@app.post(
    "/api/foods/",
    response_description="Add new food",
    status_code=status.HTTP_201_CREATED,
)
async def create_food(food_admin: FoodAdmin):
    if await is_admin(user_uid=food_admin.admin_uid) == True:
        await food_collection.insert_one(
            food_admin.food.model_dump(by_alias=True, exclude=["id"])
        )
        return {"status": CODE_SUCCESS}

    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


@app.get(
    "/api/search/{query}",
    response_description="Search foods",
    response_model=List[FoodModel],
    response_model_by_alias=False,
)
async def search_food(
    query: str = None,
):
    result = (
        await food_collection.find(
            {
                "food_name": {"$regex": query, "$options": "i"},
                "for_plan": {"$ne": True},
            }
        )
        .limit(3)
        .to_list(3)
    )
    return result or []


@app.get(
    "/api/foods",
    response_description="Get foods",
    response_model=List[FoodModel],
    response_model_by_alias=False,
)
async def show_food(
    skip: int,
    limit: int,
    category: str = None,
    tag: str = None,
    offer_tag: str = None,
    id: str = None,
    food_name: str = None,
    admin_uid: str = None,
):
    try:
        if tag is not None:
            result = (
                await food_collection.find(
                    {
                        "food_name": {"$regex": tag, "$options": "i"},
                        "for_plan": {"$ne": True},
                    }
                )
                .sort("_id", DESCENDING)
                .limit(limit=limit)
                .skip(skip=skip)
                .to_list(limit - skip)
            )
            return result
        elif offer_tag is not None:
            result = (
                await food_collection.find(
                    {
                        "offer_tag": {"$regex": offer_tag, "$options": "i"},
                        "for_plan": {"$ne": True},
                    }
                )
                .sort("_id", DESCENDING)
                .skip(skip)
                .limit(limit)
                .to_list(limit - skip)
            )
            return result
        elif id is not None:
            result = await food_collection.find_one(
                {"_id": ObjectId(id), "for_plan": {"$ne": True}}
            )
            return [result]
        elif food_name is not None:
            result = await food_collection.find_one(
                {"food_name": food_name, "for_plan": {"$ne": True}}
            )
            return [result]
        else:
            if (
                category == "any"
                and admin_uid is not None
                and is_admin(user_uid=admin_uid)
            ):
                result = (
                    await food_collection.find()
                    .sort("_id", DESCENDING)
                    .skip(skip)
                    .limit(limit)
                    .to_list(limit - skip)
                )
                return result

            elif category == "any":
                result = (
                    await food_collection.find({"for_plan": {"$ne": True}})
                    .sort("_id", DESCENDING)
                    .skip(skip)
                    .limit(limit)
                    .to_list(limit - skip)
                )
                return result

            #
            if admin_uid is not None and is_admin(user_uid=admin_uid):
                return (
                    await food_collection.find({"food_category": category})
                    .sort("_id", DESCENDING)
                    .skip(skip)
                    .limit(limit)
                    .to_list(limit - skip)
                )
            else:
                return (
                    await food_collection.find(
                        {"food_category": category, "for_plan": {"$ne": True}}
                    )
                    .sort("_id", DESCENDING)
                    .skip(skip)
                    .limit(limit)
                    .to_list(limit - skip)
                )

    except:
        raise HTTPException(status_code=404, detail=f"Server error")


@app.put("/api/foods/{id}", response_description="Update a food")
async def update_food(id: str, food_admin: FoodUpdateAdmin):
    if await is_admin(user_uid=food_admin.admin_uid) == True:
        food_ = {
            k: v
            for k, v in food_admin.update_food_model.model_dump(by_alias=True).items()
            if v is not None
        }

        if len(food_) >= 1:
            update_result = await food_collection.find_one_and_update(
                {"_id": ObjectId(id)},
                {"$set": food_},
                return_document=ReturnDocument.AFTER,
            )
            if update_result is not None:
                return {"status": CODE_SUCCESS}
            else:
                raise HTTPException(status_code=404, detail=f"Food Item {id} not found")

        return {"status": CODE_ERROR}

    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


@app.post("/api/delete_food", response_description="Delete a food")
async def delete_food(req: FoodDeleteModel):
    if await is_admin(user_uid=req.admin_uid) == True:
        delete_result = await food_collection.delete_one({"_id": ObjectId(req.id)})

        if delete_result.deleted_count == 1:
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        raise HTTPException(status_code=404, detail=f"Food {req.id} not found")

    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


# Orders
@app.post(
    "/api/orders/",
    response_description="Add new Order",
    status_code=status.HTTP_201_CREATED,
)
async def create_order(order: FoodOrderModel):
    if order.is_redeem:
        await benifit_collection.delete_one({"user_uid": order.user_uid})

    await order_collection.insert_one(order.model_dump(by_alias=True, exclude=["id"]))
    await send_redeem_success(
        user_uid=order.user_uid,
        user_collection=user_collection,
        is_redeem=order.is_redeem,
    )
    return {"status": CODE_SUCCESS}


@app.get(
    "/api/orders/",
    response_description="Get orders",
    response_model=List[FoodOrderModel],
    response_model_by_alias=False,
)
async def show_orders(user_uid: str, skip: int, limit: int):
    food_orders = (
        await order_collection.find({"user_uid": user_uid})
        .sort("_id", DESCENDING)
        .skip(skip)
        .limit(limit)
        .to_list(limit - skip)
    )

    return food_orders or []


# Orders Admin
@app.get(
    "/api/orders_admin/",
    response_description="Get orders Admin",
    response_model=List[FoodOrderModel],
    response_model_by_alias=False,
)
async def show_orders_admin(admin_uid: str, skip: int, limit: int, delivered: bool):
    if await is_admin(user_uid=admin_uid) == True:
        food_orders = (
            await order_collection.find({"food_delivered": delivered})
            .sort("_id", DESCENDING)
            .skip(skip)
            .limit(limit)
            .to_list(limit - skip)
        )

        return food_orders or []

    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


# Orders Admin By Date
@app.get(
    "/api/orders_admin_date/",
    response_description="Get orders Admin by date",
    response_model=List[FoodOrderModel],
    response_model_by_alias=False,
)
async def show_orders_admin_date(
    admin_uid: str, skip: int, limit: int, from_date: str, to_date: str
):
    if await is_admin(user_uid=admin_uid) == True:
        date_from = datetime.fromisoformat(
            from_date.replace("Z", "+00:00")
        )  # Convert to datetime object
        date_to = datetime.fromisoformat(
            to_date.replace("Z", "+00:00")
        )  # Convert to datetime object

        food_orders = (
            await order_collection.find(
                {"food_ordered_at": {"$gte": date_from, "$lte": date_to}}
            )
            .limit(limit=limit)
            .skip(skip=skip)
            .to_list(limit - skip)
        )

        return food_orders or []

    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


# Orders search
@app.get(
    "/api/orders_search/",
    response_description="Search orders Admin",
    response_model=List[FoodOrderModel],
    response_model_by_alias=False,
)
async def show_orders_admin_search(query: str, admin_uid: str):
    if await is_admin(user_uid=admin_uid) == True:
        orders = await order_collection.find({"_id": ObjectId(query)}).to_list(3)
        return orders or []

    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


@app.put(
    "/api/orders/{id}",
    response_description="Update an order",
)
async def update_order(id: str, admin_order: FoodOrderModelAdmin):
    if await is_admin(user_uid=admin_order.admin_uid):
        order_ = {
            k: v
            for k, v in admin_order.food_order_model.model_dump(by_alias=True).items()
            if v is not None
        }

        if len(order_) >= 1:
            update_result = await order_collection.find_one_and_update(
                {"_id": ObjectId(id)},
                {"$set": order_},
                return_document=ReturnDocument.AFTER,
            )
            if update_result is not None:
                return {"status": CODE_SUCCESS}
            else:
                raise HTTPException(status_code=404, detail=f"Order {id} not found")

    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


@app.post("/api/delete_order/", response_description="Delete an order")
async def delete_order(order_admin: AdminWithId):
    if await is_admin(user_uid=order_admin.admin_uid):
        delete_result = await order_collection.delete_one(
            {"_id": ObjectId(order_admin.id)}
        )
        if delete_result.deleted_count == 1:
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        raise HTTPException(status_code=404, detail=f"Order {order_admin.id} not found")

    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


# Addresses
@app.post(
    "/api/addresses/",
    response_description="Add new Address",
    response_model=Address,
    response_model_by_alias=False,
    status_code=status.HTTP_201_CREATED,
)
async def create_address(address: Address):
    new_address = await address_collection.insert_one(
        address.model_dump(by_alias=True, exclude=["id"])
    )
    created_address = await address_collection.find_one(
        {"_id": new_address.inserted_id}
    )
    return created_address


@app.get(
    "/api/addresses/",
    response_description="Get users address",
    response_model=List[Address],
    response_model_by_alias=False,
)
async def show_address(user_uid: str):
    address = await address_collection.find({"user_uid": user_uid}).to_list(10)
    return address
    # raise HTTPException(status_code=404, detail=f"Address {id} not found")


@app.put(
    "/api/addresses/{id}",
    response_description="Update an address",
    response_model=Address,
    response_model_by_alias=False,
)
async def update_address(id: str, address: Address):
    address_ = {
        k: v for k, v in address.model_dump(by_alias=True).items() if v is not None
    }
    if len(address_) >= 1:
        update_result = await address_collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": address_},
            return_document=ReturnDocument.AFTER,
        )
        if update_result is not None:
            return update_result
        else:
            raise HTTPException(status_code=404, detail=f"Address {id} not found")

    # The update is empty, but we should still return the matching document:
    if (existing_address := await address_collection.find_one({"_id": id})) is not None:
        return existing_address

    raise HTTPException(status_code=404, detail=f"Address {id} not found")


@app.post("/api/delete_address")
async def delete_address(address: UserWithId):
    delete_result = await address_collection.delete_one({"_id": ObjectId(address.id)})

    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail=f"Address {id} not found")


# Plans
@app.post(
    "/api/plans/",
    response_description="Add new Plan",
    status_code=status.HTTP_201_CREATED,
)
async def create_plan(plan_admin: PlanWithAdmin):
    if await is_admin(user_uid=plan_admin.admin_uid):
        new_plan = await plan_collection.insert_one(
            plan_admin.plan.model_dump(exclude=["id"])
        )
        await plan_collection.find_one({"_id": new_plan.inserted_id})
        return {"status": CODE_SUCCESS}

    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


@app.get(
    "/api/plans/{id}",
    response_description="Get a single plan",
    response_model=PlanModel,
    response_model_by_alias=False,
)
async def show_plan(id: str):
    if (plan := await plan_collection.find_one({"_id": ObjectId(id)})) is not None:
        return plan

    raise HTTPException(status_code=404, detail=f"Plan {id} not found")


@app.get(
    "/api/plans/",
    response_description="Get available plans",
    response_model=List[PlanModel],
    response_model_by_alias=False,
)
async def show_plans():
    result_ = await plan_collection.find().limit(10).to_list(10)
    result = await get_plans_with_benifits(
        foods_collection=food_collection, plans=result_
    )
    return result or []


@app.put(
    "/api/plans/{id}",
    response_description="Update a plan",
)
async def update_plan(id: str, plan: PlanWithAdmin):
    if await is_admin(user_uid=plan.admin_uid):
        plan_ = {
            k: v for k, v in plan.model_dump(by_alias=True).items() if v is not None
        }
        if len(plan_) >= 1:
            update_result = await plan_collection.find_one_and_update(
                {"_id": ObjectId(id)},
                {"$set": plan_},
                return_document=ReturnDocument.AFTER,
            )
            if update_result is not None:
                return {"status": CODE_SUCCESS}

        raise HTTPException(status_code=404, detail=f"Plan {id} not found")
    #
    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


@app.post("/api/delete_plan/", response_description="Delete a Plan")
async def delete_plan(plan_admin: AdminWithId):
    if await is_admin(user_uid=plan_admin.admin_uid):
        delete_result = await plan_collection.delete_one(
            {"_id": ObjectId(plan_admin.id)}
        )

        if delete_result.deleted_count == 1:
            return Response(status_code=status.HTTP_200_OK)

        raise HTTPException(status_code=404, detail=f"Address {id} not found")

    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


# Plan Benifits
@app.get(
    "/api/benifits/{user_uid}",
    response_description="Get benifits",
    response_model=PlanBenifitsModel,
    response_model_by_alias=False,
)
async def show_benifits(user_uid: str):
    if (
        benifit := await benifit_collection.find_one({"user_uid": user_uid})
    ) is not None:
        return benifit

    raise HTTPException(status_code=404, detail=f"User Benifits {user_uid} not found")


# User plans
@app.get(
    "/api/active/{user_uid}",
    response_description="Get users active plan",
    response_model=PlanModel,
    response_model_by_alias=False,
)
async def show_active_plan(user_uid: str):
    if (
        plan := await user_plans_collection.find_one(
            {"user_uid": user_uid, "active": True}
        )
    ) is not None:
        return plan

    raise HTTPException(status_code=404, detail=f"Plan {user_uid} not found")


# Payment
@app.post(
    "/api/pay/",
    response_description="Create new payment",
    response_model=PayResponseModel,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(payment: PayModel):
    if payment.pay_type == PAY_PLAN:
        plan = await plan_collection.find_one({"_id": ObjectId(payment.plan_id)})
        if plan is not None:
            response: PhonePeResponse = phonepeClient.init_payment(
                amount=int(plan.get("plan_price") + payment.charges),
                user_uid=payment.user_uid,
            )

            # Put plan ...
            del plan["_id"]
            plan["user_uid"] = payment.user_uid
            plan["merchant_transaction_id"] = response.data.merchant_transaction_id
            plan["active"] = False
            plan["plan_benifits"] = []

            #
            await user_plans_collection.insert_one(plan)

            # Response ...
            return {
                "status": CODE_SUCCESS,
                "success": response.success,
                "code": response.code,
                "message": response.message,
                "merchant_id": response.data.merchant_id,
                "pay_page_url": response.data.instrument_response.redirect_info.url,
                "pay_page_method": response.data.instrument_response.redirect_info.method,
                "merchant_transaction_id": response.data.merchant_transaction_id,
            }
        raise HTTPException(status_code=404, detail=f"Plan {payment.plan_id} not found")

    elif payment.pay_type == PAY_FOOD:
        if payment.food_order is not None:
            response: PhonePeResponse = phonepeClient.init_payment(
                amount=int(payment.food_order.total),
                user_uid=payment.user_uid,
            )
            #
            payment.food_order.merchant_transaction_id = (
                response.data.merchant_transaction_id
            )
            payment.food_order.food_order_successfull = False

            # init the order in db
            order_collection.update_one(
                {"merchant_transaction_id": response.data.merchant_transaction_id},
                {"$set": payment.food_order.model_dump()},
                upsert=True,
            )
            #
            return {
                "status": CODE_SUCCESS,
                "success": response.success,
                "code": response.code,
                "message": response.message,
                "merchant_id": response.data.merchant_id,
                "pay_page_url": response.data.instrument_response.redirect_info.url,
                "pay_page_method": response.data.instrument_response.redirect_info.method,
                "merchant_transaction_id": response.data.merchant_transaction_id,
            }

        raise HTTPException(
            status_code=404, detail=f"Food Item {payment.food_order.id} not found"
        )


# Earnings
@app.get(
    "/api/earnings_admin/",
    response_description="Get a earnings admin",
    response_model=List[EarningsModel],
    response_model_by_alias=True,
)
async def show_earnings_admin(
    admin_uid: str,
    skip: int,
    limit: int,
    paid: bool = False,
):
    if await is_admin(user_uid=admin_uid):
        earnings = (
            await earning_collection.find({"payed": paid})
            .sort("_id", DESCENDING)
            .skip(skip)
            .limit(limit)
            .to_list(limit - skip)
        )

        return earnings or []

    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


@app.get(
    "/api/earnings/",
    response_description="Get user earnings",
    response_model=List[EarningsModel],
    response_model_by_alias=False,
)
async def show_earnings(user_uid: str, skip: int, limit: int):
    try:
        earnings = (
            await earning_collection.find({"user_uid": user_uid})
            .sort("_id", DESCENDING)
            .skip(skip)
            .limit(limit)
            .to_list(limit - skip)
        )

        return earnings or []
    except:
        raise HTTPException(
            status_code=404, detail=f"Earnings for {user_uid} not found"
        )


@app.put("/api/earnings/{id}", response_description="Update an Earning")
async def update_earning(id: str, earning_admin: UpdateEarningsAdmin):
    if await is_admin(user_uid=earning_admin.admin_uid):
        earning_ = {
            k: v
            for k, v in earning_admin.update_earning_model.model_dump(
                by_alias=True
            ).items()
            if v is not None
        }
        if len(earning_) >= 1:
            update_result = await earning_collection.find_one_and_update(
                {"_id": ObjectId(id)},
                {"$set": earning_},
                return_document=ReturnDocument.AFTER,
            )
            #
            if update_result is not None and update_result.get("payed") == True:
                current_user_income = await income_collection.find_one(
                    {"user_uid": update_result.get("user_uid")}
                )
                #
                if (
                    update_result.get("mode") == "active"
                    and current_user_income is not None
                ):
                    updated_income_active = (
                        current_user_income.get("active_income") or 0.0
                    )
                    print("current active: ", updated_income_active)
                    #
                    if updated_income_active > 0.0:
                        updated_income_active = float(
                            updated_income_active - float(update_result.get("amount"))
                        )
                        print("Updating the active income to: ", updated_income_active)
                        await income_collection.update_one(
                            {"user_uid": update_result.get("user_uid")},
                            {"$set": {"active_income": updated_income_active}},
                        )
                    # Done ...
                elif (
                    update_result.get("mode") == "passive"
                    and current_user_income is not None
                ):
                    updated_income_passive = (
                        current_user_income.get("passive_income") or 0.0
                    )
                    #
                    if updated_income_passive > 0.0:
                        updated_income_passive = float(
                            updated_income_passive - float(update_result.get("amount"))
                        )
                        await income_collection.update_one(
                            {"user_uid": update_result.get("user_uid")},
                            {"$set": {"passive_income": updated_income_active}},
                        )
                    # Done ...

                # Done ...
            return {"status": CODE_SUCCESS}

        # BAD
        return {"status": CODE_ERROR}

    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


@app.post("/api/delete_earning", response_description="Delete an Earning")
async def delete_earning(earning_admin: AdminWithId):
    if await is_admin(user_uid=earning_admin.admin_uid) == True:
        delete_result = await earning_collection.delete_one(
            {"_id": ObjectId(earning_admin.id)}
        )

        if delete_result.deleted_count == 1:
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        raise HTTPException(status_code=404, detail=f"Earning {id} not found")

    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


# Favourites
@app.get(
    "/api/favourites/",
    response_description="Get favourite items",
    response_model=List[FoodModel],
    response_model_by_alias=False,
)
async def show_favourites(skip: int, limit: int, user_uid: str = None):
    if not user_uid:
        return []

    favourites = (
        await favourite_collection.find({"user_uid": user_uid})
        .sort("T", DESCENDING)
        .skip(skip)
        .limit(limit)
        .to_list(limit - skip)
    )
    return favourites


@app.post(
    "/api/favourites/",
    response_description="Update a Favourite",
    response_model=FavouriteFoodModel,
    response_model_by_alias=False,
)
async def update_favourites(favourite: FavouriteFoodModel):
    _exists = await favourite_collection.find_one({"_id": ObjectId(favourite.food_id)})
    if _exists is not None:
        # Remove
        await favourite_collection.delete_one({"_id": ObjectId(favourite.food_id)})
        return {"food_id": favourite.food_id, "user_uid": favourite.user_uid}
    else:
        # Insert New
        food_item = await food_collection.find_one({"_id": ObjectId(favourite.food_id)})
        food_item["T"] = ObjectId()
        food_item["user_uid"] = favourite.user_uid
        await favourite_collection.insert_one(food_item)
        return {"food_id": favourite.food_id, "user_uid": favourite.user_uid}


@app.post("/api/upload")
def upload_file(uploaded_file: UploadFile = File(...)):
    try:
        upload_directory = settings.upload_directory
        path = f"{upload_directory}/{uploaded_file.filename}"

        if os.path.exists(path):
            return {
                "file": uploaded_file.filename,
                "content": uploaded_file.content_type,
                "path": f"/static/{uploaded_file.filename}",
            }

        with open(path, "w+b") as file:
            shutil.copyfileobj(uploaded_file.file, file)

        return {
            "file": uploaded_file.filename,
            "content": uploaded_file.content_type,
            "path": f"/static/{uploaded_file.filename}",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# Banners
@app.post(
    "/api/banners/",
    response_description="Add new Banner",
    status_code=status.HTTP_201_CREATED,
)
async def create_banner(banner_admin: BannerWithAdmin):
    if await is_admin(banner_admin.admin_uid) == True:
        await banner_collection.insert_one(
            banner_admin.banner.model_dump(exclude=["id"])
        )
        return {"status": CODE_SUCCESS}

    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


@app.get(
    "/api/banners/",
    response_description="Get banners",
    response_model=List[BannerModel],
    response_model_by_alias=False,
)
async def show_banners():
    result = await banner_collection.find().limit(10).to_list(10)
    return result


@app.post("/api/delete_banner/", response_description="Delete a Banner")
async def delete_banner(banner_admin: AdminWithId):
    if await is_admin(user_uid=banner_admin.admin_uid) == True:
        delete_result = await banner_collection.delete_one(
            {"_id": ObjectId(banner_admin.id)}
        )

        if delete_result.deleted_count == 1:
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        raise HTTPException(status_code=404, detail=f"Banner {id} not found")

    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


# Featured
@app.post(
    "/api/featured/",
    response_description="Add new featured item",
    status_code=status.HTTP_201_CREATED,
)
async def create_featured(featured_admin: FeaturedWithAdmin):
    if await is_admin(user_uid=featured_admin.admin_uid):
        await featured_collection.insert_one(
            featured_admin.featured.model_dump(exclude=["id"])
        )
        return {"status": CODE_SUCCESS}
    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


@app.put(
    "/api/featured/{id}",
    response_description="update a featured item",
    status_code=status.HTTP_202_ACCEPTED,
)
async def update_featured(id: str, featured_admin: UpdateFeaturedWithAdmin):
    if await is_admin(user_uid=featured_admin.admin_uid):
        featured_ = {
            k: v
            for k, v in featured_admin.featured.model_dump(by_alias=True).items()
            if v is not None
        }
        if len(featured_) >= 1:
            update_result = await featured_collection.find_one_and_update(
                {"_id": ObjectId(id)},
                {"$set": featured_},
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
            if update_result is not None:
                return {"status": CODE_SUCCESS}
            else:
                raise HTTPException(
                    status_code=404, detail=f"Featured Item {id} not found"
                )

        return {"status": CODE_ERROR}

    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


@app.get(
    "/api/featured/",
    response_description="Get featured items",
    response_model=List[FeaturedModel],
    response_model_by_alias=False,
)
async def show_featured():
    result = await featured_collection.find().to_list(16)
    return result


@app.post("/api/delete_featured/", response_description="Delete a Featured item")
async def delete_featured(featured_admin: AdminWithId):
    if await is_admin(user_uid=featured_admin.admin_uid):
        delete_result = await featured_collection.delete_one(
            {"_id": ObjectId(featured_admin.id)}
        )

        if delete_result.deleted_count == 1:
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        raise HTTPException(
            status_code=404, detail=f"Featured item {featured_admin.id} not found"
        )

    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


# Pincode
@app.get(
    "/api/pincodes/{pincode}",
    response_description="Get pincode",
    response_model=PincodeRowModel,
    response_model_by_alias=False,
)
async def show_pincode(pincode: str):
    try:
        result = await pincode_collection.find_one({"pincode": pincode})
        if result is None:
            return PincodeRowModel(index=-1, pincode=pincode, charges=-1)
        return result
    except:
        raise HTTPException(status_code=404, detail=f"Pincode {pincode} not found")


@app.get(
    "/api/pincodes/",
    response_description="Get pincodes",
    response_model=List[PincodeRowModel],
    response_model_by_alias=False,
)
async def show_pincodes(admin_uid: str, skip: int, limit: int):
    if await is_admin(user_uid=admin_uid) == True:
        result = (
            await pincode_collection.find()
            .skip(skip)
            .limit(limit)
            .to_list(limit - skip)
        )
        return result or []

    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


@app.put("/api/pincodes/{index}", response_description="Update a pincode")
async def update_pincode(index: int, pincode_admin: UpdatePincodeAdmin):
    if await is_admin(user_uid=pincode_admin.admin_uid):
        pincode_ = {
            k: v
            for k, v in pincode_admin.pincode.model_dump(by_alias=True).items()
            if v is not None
        }
        if len(pincode_) >= 1:
            update_result = await pincode_collection.find_one_and_update(
                {"index": index},
                {"$set": pincode_},
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
            if update_result is not None:
                return {"status": CODE_SUCCESS}
            else:
                raise HTTPException(status_code=404, detail=f"Earning {id} not found")

        return {"status": CODE_ERROR}

    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


@app.post("/api/delete_pincode/", response_description="Delete a Pincode")
async def delete_pincode(pincode_admin: AdminWithId):
    if await is_admin(user_uid=pincode_admin.admin_uid):
        delete_result = await pincode_collection.delete_one({"index": pincode_admin.id})

        if delete_result.deleted_count == 1:
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        raise HTTPException(status_code=404, detail=f"Pincode {id} not found")

    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


# Income
@app.get(
    "/api/income/{user_uid}",
    response_description="Get user income",
    response_model=IncomeModel,
    response_model_by_alias=False,
)
async def show_income(user_uid: str):
    if (income := await income_collection.find_one({"user_uid": user_uid})) is not None:
        return income

    raise HTTPException(status_code=404, detail=f"User Income for {user_uid} not found")


@app.get(
    "/api/pincodes/",
    response_description="Get pincodes",
    response_model=List[PincodeRowModel],
    response_model_by_alias=False,
)
async def show_pincodes(skip: int, limit: int):
    result = (
        await pincode_collection.find().skip(skip).limit(limit).to_list(limit - skip)
    )
    return result or []


# Recents
@app.get(
    "/api/recents/",
    response_model=List[FoodModel],
    response_description="get user recently viewed",
)
async def show_recents(user_uid: str, skip: int, limit: int):
    recents = (
        await recent_collection.find({"user_uid": user_uid})
        .sort("_id", DESCENDING)
        .skip(skip)
        .limit(limit)
        .to_list(limit - skip)
    )
    return recents + []


# Settings
@app.get("/api/settings/", response_model=SettingsModel)
async def show_settings(admin_uid: str):
    if await is_admin(user_uid=admin_uid):
        result_ = await setting_collection.find_one()
        return result_
    #
    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


@app.get(
    "/api/settings/",
    response_model=SettingsModel,
    response_description="Get admin settings",
)
async def show_settings(admin_uid: str):
    if await is_admin(user_uid=admin_uid):
        result_ = await setting_collection.find_one()
        return result_
    #
    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


@app.post("/api/settings/", response_description="update admin settings")
async def update_settings(settings_model: UpdateSettingsModel):
    if await is_admin(settings_model.user_admin):
        settings_ = {
            k: v
            for k, v in settings_model.model_dump(by_alias=True).items()
            if v is not None
        }
        settings_["user_admin"] = "eatoearn_constant"
        if len(settings_) >= 1:
            update_result = await setting_collection.find_one_and_update(
                {"user_admin": "eatoearn_constant"},
                {"$set": settings_},
                return_document=ReturnDocument.AFTER,
            )
            if update_result is not None:
                return {
                    "status": CODE_SUCCESS,
                    "food_l1_pct": settings_model.food_l1_pct,
                    "food_l2_pct": settings_model.food_l2_pct,
                }

        return {"status": CODE_ERROR}
    #
    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


# S2S Callback...
@app.post("/api/callback")
async def s2s_callback(response: PhonePeCallback):
    decoded_data = base64.b64decode(response.response).decode("utf-8")
    decoded_dict = json.loads(decoded_data)

    success_ = decoded_dict.get("success")
    code_ = decoded_dict.get("code")
    code_ = decoded_dict.get("code")
    merchantTransactionId_ = decoded_dict.get("data").get("merchantTransactionId")

    # IF PLAN
    plan_exists = await user_plans_collection.find_one(
        {"merchant_transaction_id": merchantTransactionId_}
    )

    if success_ == True and code_ == "PAYMENT_SUCCESS" and plan_exists is not None:
        # Model Plan
        plan_bought: PlanModel = PlanModel.model_validate(plan_exists)

        # Remove all existing plans...
        await user_plans_collection.delete_many(
            {
                "user_uid": plan_bought.user_uid,
                "merchant_transaction_id": {"$ne": merchantTransactionId_},
            }
        )

        # Mark pay success...
        await user_plans_collection.update_one(
            {"merchant_transaction_id": merchantTransactionId_},
            {"$set": {"active": True}},
        )

        user_ = await user_collection.find_one({"user_uid": plan_bought.user_uid})
        user_name = user_.get("user_name") or user_.get("user_email")
        user_email = user_.get("user_email")
        link = f'https://eatoearn.com/signup/?sponsor={user_.get("user_ID")}'

        t1 = threading.Thread(
            target=send_plan_success,
            args=(
                user_name,
                user_email,
                link,
                f"{plan_bought.plan_name}, {plan_bought.plan_price}",
            ),
        )
        t1.start()

        t2 = threading.Thread(
            target=send_plan_admin,
            args=(
                user_name,
                f"{plan_bought.plan_name}, {plan_bought.plan_price}",
            ),
        )
        t2.start()

        # Insert Benifits ...
        await insert_plan_benifits(
            foods_collection=food_collection,
            benifits_collection=benifit_collection,
            user_uid=plan_bought.user_uid,
            plan=plan_bought,
        )

        # Insert reward...
        await insert_rewards(
            users_collection=user_collection,
            user_plans_collection=user_plans_collection,
            earnings_collection=earning_collection,
            income_collection=income_collection,
            user_uid=plan_bought.user_uid,
            plan_bought=plan_bought,
        )

    # IF FOOD ORDER
    food_order_exists = await order_collection.find_one(
        {"merchant_transaction_id": merchantTransactionId_}
    )
    if (
        success_ == True
        and code_ == "PAYMENT_SUCCESS"
        and food_order_exists is not None
    ):
        # Mark pay success...
        await order_collection.update_one(
            {"merchant_transaction_id": merchantTransactionId_},
            {"$set": {"food_order_successfull": True}},
        )
        # Insert Food Reward
        food_bought: FoodOrderModel = FoodOrderModel.model_validate(food_order_exists)
        #
        user_ = await user_collection.find_one({"user_uid": food_bought.user_uid})
        user_name = user_.get("user_name") or user_.get("user_email")
        user_email = user_.get("user_email")

        t1 = threading.Thread(target=send_order_success, args=(user_name, user_email))
        t1.start()

        t2 = threading.Thread(
            target=send_food_admin,
            args=(
                user_name,
                food_bought.items,
                food_bought.total,
            ),
        )
        t2.start()

        # Inserting FOOD reward...
        await insert_rewards_food(
            users_collection=user_collection,
            user_plans_collection=user_plans_collection,
            earnings_collection=earning_collection,
            settings_collection=setting_collection,
            income_collection=income_collection,
            user_uid=food_bought.user_uid,
            food_bought=food_bought,
        )

        # Update Recents
        await update_recents(
            recent_collection=recent_collection,
            user_uid=food_bought.user_uid,
            food_order=food_bought,
        )

    return {"status": "ok"}


# Status...
@app.post("/api/status")
async def status_check(status: StatusModel):
    if status.pay_type == PAY_PLAN:
        _plan_db = await user_plans_collection.find_one(
            {"merchant_transaction_id": status.merchant_transaction_id}
        )
        if _plan_db.get("active") == True:
            return {"status": CODE_SUCCESS_INIT}
        else:
            # Check status again ...
            if status.success == True and status.code == "PAYMENT_INITIATED":
                response: PhonePeResponse = phonepeClient.check_status(
                    status.merchant_transaction_id
                )
                if (
                    response.data.state == "COMPLETED"
                    and response.data.response_code == "SUCCESS"
                    and response.code == "PAYMENT_SUCCESS"
                    and response.success == True
                ):
                    # Plan bought
                    plan_bought: PlanModel = PlanModel.model_validate(_plan_db)

                    # Remove all existing plans...
                    await user_plans_collection.delete_many(
                        {
                            "user_uid": plan_bought.user_uid,
                            "merchant_transaction_id": {
                                "$ne": status.merchant_transaction_id
                            },
                        }
                    )

                    # FOR PLANS ...
                    await user_plans_collection.update_one(
                        {"merchant_transaction_id": status.merchant_transaction_id},
                        {"$set": {"active": True}},
                    )

                    user_ = await user_collection.find_one(
                        {"user_uid": plan_bought.user_uid}
                    )
                    user_name = user_.get("user_name") or user_.get("user_email")
                    user_email = user_.get("user_email")
                    link = (
                        f'https://eatoearn.com/signup/?sponsor={user_.get("user_ID")}'
                    )

                    t1 = threading.Thread(
                        target=send_plan_success,
                        args=(
                            user_name,
                            user_email,
                            link,
                            f"{plan_bought.plan_name}, {plan_bought.plan_price}",
                        ),
                    )
                    t1.start()

                    t2 = threading.Thread(
                        target=send_plan_admin,
                        args=(
                            user_name,
                            f"{plan_bought.plan_name}, {plan_bought.plan_price}",
                        ),
                    )
                    t2.start()

                    # Insert Benifits ...
                    await insert_plan_benifits(
                        foods_collection=food_collection,
                        benifits_collection=benifit_collection,
                        user_uid=status.user_uid,
                        plan=plan_bought,
                    )

                    # Insert reward...

                    await insert_rewards(
                        users_collection=user_collection,
                        user_plans_collection=user_plans_collection,
                        earnings_collection=earning_collection,
                        income_collection=income_collection,
                        user_uid=status.user_uid,
                        plan_bought=plan_bought,
                    )

                    return {"status": CODE_SUCCESS}
                # ERRORS
                elif (
                    response.data.state == "FAILED"
                    and response.code == "PAYMENT_ERROR"
                    and response.success == False
                ):
                    await user_plans_collection.delete_one(
                        {"merchant_transaction_id": status.merchant_transaction_id}
                    )
                    return {"status": CODE_ERROR}
                #
                elif (
                    response.data.state == "PENDING"
                    and response.code == "PAYMENT_PENDING"
                    and response.success == True
                ):
                    return {"status": CODE_PENDING}
            #
            return {"status": CODE_ERROR}

    elif status.pay_type == PAY_FOOD:
        _food_order_db = await order_collection.find_one(
            {"merchant_transaction_id": status.merchant_transaction_id}
        )
        if _food_order_db.get("food_order_successfull") == True:
            return {"status": CODE_SUCCESS_INIT}
        else:
            # Check status again ...
            if status.success == True and status.code == "PAYMENT_INITIATED":
                response: PhonePeResponse = phonepeClient.check_status(
                    status.merchant_transaction_id
                )
                if (
                    response.data.state == "COMPLETED"
                    and response.data.response_code == "SUCCESS"
                    and response.code == "PAYMENT_SUCCESS"
                    and response.success == True
                ):
                    # FOR FOODS ...
                    await order_collection.update_one(
                        {"merchant_transaction_id": status.merchant_transaction_id},
                        {"$set": {"food_order_successfull": True}},
                    )

                    # Food bought ...
                    food_bought: FoodOrderModel = FoodOrderModel.model_validate(
                        _food_order_db
                    )
                    #
                    user_ = await user_collection.find_one(
                        {"user_uid": status.user_uid}
                    )
                    user_name = user_.get("user_name") or user_.get("user_email")
                    user_email = user_.get("user_email")

                    t1 = threading.Thread(
                        target=send_order_success, args=(user_name, user_email)
                    )
                    t1.start()

                    t2 = threading.Thread(
                        target=send_food_admin,
                        args=(
                            user_name,
                            food_bought.items,
                            food_bought.total,
                        ),
                    )
                    t2.start()

                    # Inserting FOOD reward...
                    await insert_rewards_food(
                        users_collection=user_collection,
                        user_plans_collection=user_plans_collection,
                        earnings_collection=earning_collection,
                        settings_collection=setting_collection,
                        income_collection=income_collection,
                        user_uid=status.user_uid,
                        food_bought=food_bought,
                    )

                    # Update Recents
                    await update_recents(
                        recent_collection=recent_collection,
                        user_uid=status.user_uid,
                        food_order=food_bought,
                    )

                    return {"status": CODE_SUCCESS}
                # ERRORS
                elif (
                    response.data.state == "FAILED"
                    and response.code == "PAYMENT_ERROR"
                    and response.success == False
                ):
                    await order_collection.delete_one(
                        {"merchant_transaction_id": status.merchant_transaction_id}
                    )
                    return {"status": CODE_ERROR}
                #
                elif (
                    response.data.state == "PENDING"
                    and response.code == "PAYMENT_PENDING"
                    and response.success == True
                ):
                    return {"status": CODE_PENDING}
            else:
                return {"status": CODE_ERROR}


# Statistics
@app.get(
    "/api/statistics/{id}",
    response_model=StatisticsModel,
    response_description="get admin statistics",
)
async def get_statistics(id: str):
    if await is_admin(id):
        total_orders = await order_collection.count_documents({})
        total_delivered = await order_collection.count_documents(
            {"food_delivered": True}
        )
        total_earnings = await earning_collection.count_documents({})
        earnings_payed = await earning_collection.count_documents({"payed": True})

        return {
            "total_orders": total_orders,
            "total_delivered": total_delivered,
            "total_earnings": total_earnings,
            "earnings_payed": earnings_payed,
        }

    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


@app.post("/api/availablity/")
async def availablity(setting: Availablity):
    if await is_admin(setting.admin_uid) == True:
        await availablity_collection.update_one(
            {"ref": setting.ref}, {"$set": setting.model_dump()}, upsert=True
        )
        return Response(status_code=status.HTTP_201_CREATED)

    raise HTTPException(status_code=404, detail=f"ERROR_NO_ADMIN")


@app.get("/api/availablity/", response_model=Availablity)
async def availablity():
    availablity = await availablity_collection.find_one()
    return availablity


# END
