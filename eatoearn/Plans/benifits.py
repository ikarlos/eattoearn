#
from Foods.foods import get_foods_by_ids
from Plans.PlanModels import PlanBenifitsModel, PlanModel


async def insert_plan_benifits(
    foods_collection, benifits_collection, user_uid, plan: PlanModel
):
    foods_ = await get_foods_by_ids(
        foods_collection=foods_collection, food_ids=plan.plan_benifit_ids
    )
    benifits = PlanBenifitsModel(
        user_uid=user_uid, plan_benifits=foods_, plan_benifits_redeemed=False
    )
    await benifits_collection.update_one(
        {"user_uid": user_uid},
        {
            "$set": benifits.model_dump(),
        },
        upsert=True,
    )


# END
