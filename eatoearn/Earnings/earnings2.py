from datetime import datetime, timedelta
import threading

from pytz import utc
from Earnings.EarningModels import EarningsModel
from Orders.OrderModels import FoodOrderModel
from Plans.PlanModels import PlanModel
from Email.email_utils import send_referral_success


async def calculate_reward(
    plan: PlanModel, referrer_plan: PlanModel, level: int
) -> float:
    min_price = min(plan.plan_price, referrer_plan.plan_price)
    if level == 1:
        return min_price * (referrer_plan.plan_l1_pct)

    elif level == 2:
        return min_price * (referrer_plan.plan_l2_pct)

    else:
        raise ValueError("Invalid referrer level")


async def calculate_reward_food(
    settings_collection, food: FoodOrderModel, referrer_plan: PlanModel, level: int
) -> float:
    food_settings = await settings_collection.find_one()
    food_l1_pct = float(food_settings.get("food_l1_pct")) or 0.10
    food_l2_pct = float(food_settings.get("food_l2_pct")) or 0.05
    food_total = float(food.total - food.delivery_charges - 3.0)
    #
    if level == 1:
        if referrer_plan.plan_price >= 1300:
            return food_total * float(food_l1_pct)
        else:
            min_price = min(food_total, referrer_plan.plan_price)
            return min_price * food_l1_pct
    elif level == 2:
        if referrer_plan.plan_price >= 1300:
            return food_total * float(food_l2_pct)
        else:
            min_price = min(food_total, referrer_plan.plan_price)
            return min_price * food_l2_pct
    else:
        raise ValueError("Invalid referrer level")


# async def calculate_reward_food(
#     settings_collection, food: FoodOrderModel, referrer_plan: PlanModel, level: int
# ) -> float:
#     min_price = min(referrer_plan.plan_price, food.total)
#     #
#     if level == 1:
#         amount_ = min_price * referrer_plan.plan_l1_pct
#         if referrer_plan.plan_price >= 1399:
#             amount_ = food.total * referrer_plan.plan_l1_pct
#         return amount_

#     elif level == 2:
#         amount_ = min_price * referrer_plan.plan_l2_pct
#         if referrer_plan.plan_price >= 1399:
#             amount_ = food.total * referrer_plan.plan_l2_pct
#         return amount_
#     else:
#         raise ValueError("Invalid referrer level")


async def create_notification(
    earnings_collection,
    #
    winner_user_uid: int,
    reward_amount: float,
    bought_price: float,
    buyer_name: str,
    referrer_name: str,
    l2_referrer_name: str,
    mode: str,
) -> EarningsModel:
    notification = EarningsModel(
        user_uid=winner_user_uid,
        amount=reward_amount,
        bought_price=bought_price,
        buyer_idf=buyer_name,
        referrer_idf=referrer_name,
        l2_referrer_idf=l2_referrer_name,
        earned_date=datetime.now() + timedelta(seconds=19801, microseconds=368263),
        mode=mode,
    )
    await earnings_collection.insert_one(notification.model_dump())


async def get_referrer(user_collection, user_uid: str):
    _user = user_collection.find_one({"user_uid": user_uid})
    if _user is not None:
        return _user.get("user_referer_uid") or None
    return None


async def get_user_plan(plans_collection, user_uid) -> PlanModel:
    plan = await plans_collection.find_one({"user_uid": user_uid})
    return PlanModel(**plan)


async def update_active_income(income_collection, referer_uid, new_earned: float):
    user_income = await income_collection.find_one({"user_uid": referer_uid})
    if user_income:
        new_earnings = user_income.get("active_income", 0) + new_earned
        await income_collection.update_one(
            {"user_uid": referer_uid}, {"$set": {"active_income": new_earnings}}
        )
    else:
        # If the employee does not exist, insert a new document with the given earnings
        await income_collection.insert_one(
            {"user_uid": referer_uid, "active_income": new_earned}
        )


async def update_passive_income(income_collection, referer_uid, new_earned: float):
    user_income = await income_collection.find_one({"user_uid": referer_uid})
    if user_income is not None:
        new_earnings = float(user_income.get("passive_income") or 0.0) + new_earned
        await income_collection.update_one(
            {"user_uid": referer_uid}, {"$set": {"passive_income": new_earnings}}
        )
    else:
        # If the employee does not exist, insert a new document with the given earnings
        await income_collection.insert_one(
            {"user_uid": referer_uid, "passive_income": new_earned}
        )


async def insert_rewards(
    users_collection,
    user_plans_collection,
    earnings_collection,
    income_collection,
    user_uid: str,
    plan_bought: PlanModel,
):
    user_ = await users_collection.find_one({"user_uid": user_uid})
    user_referrer_uid = user_.get("user_referer_uid") or None
    if user_referrer_uid is None:
        return
    if user_.get("user_referal_completed") == True:
        return

    referrer_plan = await user_plans_collection.find_one(
        {"user_uid": user_referrer_uid}
    )
    if referrer_plan is None:
        return
    referrer_plan = PlanModel.model_validate(referrer_plan)

    referrer_ = await users_collection.find_one({"user_uid": user_referrer_uid})
    referrer_idf = referrer_.get("user_name") or referrer_.get("user_email")
    user_idf = user_.get("user_name") or user_.get("user_email")

    reward_amount_l1 = await calculate_reward(
        plan=plan_bought, referrer_plan=referrer_plan, level=1
    )

    # update income ...
    await update_active_income(
        income_collection=income_collection,
        referer_uid=user_referrer_uid,
        new_earned=reward_amount_l1,
    )

    # create notification ...
    await create_notification(
        earnings_collection=earnings_collection,
        winner_user_uid=user_referrer_uid,
        reward_amount=reward_amount_l1,
        bought_price=plan_bought.plan_price,
        buyer_name=user_idf,
        referrer_name=referrer_idf,
        l2_referrer_name=None,
        mode="active",
    )

    t1 = threading.Thread(
        target=send_referral_success,
        args=(
            referrer_idf,
            user_idf,
            f"{plan_bought.plan_name}, {plan_bought.plan_price}",
            referrer_.get("user_email"),
            "Level 1",
        ),
    )
    t1.start()

    # # L2 Earnings ...
    user_l2_referrer_uid = referrer_.get("user_referer_uid") or None
    if user_l2_referrer_uid is None:
        # Mark referral done
        await users_collection.update_one(
            {"user_uid": user_uid}, {"$set": {"user_referal_completed": True}}
        )
        return

    l2_referrer_plan = await user_plans_collection.find_one(
        {"user_uid": user_l2_referrer_uid}
    )
    l2_referrer_plan = PlanModel.model_validate(l2_referrer_plan)
    if l2_referrer_plan is None:
        return

    l2_referrer = await users_collection.find_one({"user_uid": user_l2_referrer_uid})
    l2_referrer_idf = l2_referrer.get("user_name") or l2_referrer.get("user_email")

    reward_amount_l2 = await calculate_reward(
        plan=plan_bought, referrer_plan=l2_referrer_plan, level=2
    )

    # update income ...
    await update_active_income(
        income_collection=income_collection,
        referer_uid=user_l2_referrer_uid,
        new_earned=reward_amount_l2,
    )

    # create notification ...
    await create_notification(
        earnings_collection=earnings_collection,
        winner_user_uid=user_l2_referrer_uid,
        reward_amount=reward_amount_l2,
        bought_price=plan_bought.plan_price,
        buyer_name=user_idf,
        referrer_name=referrer_idf,
        mode="active",
        l2_referrer_name=l2_referrer_idf,
    )

    # send success L2
    t2 = threading.Thread(
        target=send_referral_success,
        args=(
            l2_referrer_idf,
            referrer_idf,
            f"{plan_bought.plan_name}, {plan_bought.plan_price}",
            l2_referrer.get("user_email"),
            "Level 2",
        ),
    )
    t2.start()

    # Mark referral done
    await users_collection.update_one(
        {"user_uid": user_uid}, {"$set": {"user_referal_completed": True}}
    )


async def insert_rewards_food(
    users_collection,
    user_plans_collection,
    earnings_collection,
    settings_collection,
    income_collection,
    user_uid: str,
    food_bought: FoodOrderModel,
):
    user_ = await users_collection.find_one({"user_uid": user_uid})
    user_referrer_uid = user_.get("user_referer_uid") or None
    if user_referrer_uid is None:
        return

    referrer_plan = await user_plans_collection.find_one(
        {"user_uid": user_referrer_uid}
    )
    if referrer_plan is None:
        return
    referrer_plan = PlanModel.model_validate(referrer_plan)

    referrer_ = await users_collection.find_one({"user_uid": user_referrer_uid})
    referrer_idf = referrer_.get("user_name") or referrer_.get("user_email")
    user_idf = user_.get("user_name") or user_.get("user_email")

    reward_amount_l1 = await calculate_reward_food(
        settings_collection=settings_collection,
        food=food_bought,
        referrer_plan=referrer_plan,
        level=1,
    )

    # update income ...
    await update_passive_income(
        income_collection=income_collection,
        referer_uid=user_referrer_uid,
        new_earned=reward_amount_l1,
    )

    # create the notification ...
    await create_notification(
        earnings_collection=earnings_collection,
        winner_user_uid=user_referrer_uid,
        reward_amount=reward_amount_l1,
        bought_price=food_bought.total,
        buyer_name=user_idf,
        referrer_name=referrer_idf,
        mode="passive",
    )

    # L2 Earnings ...
    user_l2_referrer_uid = referrer_.get("user_referer_uid") or None
    if user_l2_referrer_uid is None:
        return

    l2_referrer_plan = await user_plans_collection.find_one(
        {"user_uid": user_l2_referrer_uid}
    )
    l2_referrer_plan = PlanModel.model_validate(l2_referrer_plan)
    if l2_referrer_plan is None:
        return

    l2_referrer = await users_collection.find_one({"user_uid": user_l2_referrer_uid})
    l2_referrer_idf = l2_referrer.get("user_name") or l2_referrer.get("user_email")

    reward_amount_l2 = await calculate_reward_food(
        settings_collection=settings_collection,
        food=food_bought,
        referrer_plan=l2_referrer_plan,
        level=2,
    )

    # update income ...
    await update_passive_income(
        income_collection=income_collection,
        referer_uid=user_l2_referrer_uid,
        new_earned=reward_amount_l2,
    )

    # create notification ...
    await create_notification(
        earnings_collection=earnings_collection,
        winner_user_uid=user_l2_referrer_uid,
        reward_amount=reward_amount_l2,
        bought_price=food_bought.total,
        buyer_name=user_idf,
        referrer_name=referrer_idf,
        mode="passive",
        l2_referrer_name=l2_referrer_idf,
    )


async def update_recents(recent_collection, user_uid, food_order: FoodOrderModel):
    for food_item in food_order.items:
        food_item.user_uid = user_uid
        food_item.expire_at = datetime.now(utc) + timedelta(days=7)
        recent_collection.update_one(
            {"user_uid": user_uid, "food_name": food_item.food_name},
            {"$set": food_item.model_dump(exclude_none=True)},
            upsert=True,
        )


# END
