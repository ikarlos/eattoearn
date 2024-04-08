from typing import List
from bson import ObjectId
from bson.json_util import dumps

from Plans.PlanModels import PlanModel


async def get_foods_by_ids(foods_collection, food_ids: List[str]):
    result = []
    if len(food_ids) > 0:
        for food_id in food_ids:
            food_item = await foods_collection.find_one({"_id": ObjectId(food_id)})
            if food_item is not None:
                food_item["id"] = str(food_item["_id"])
                food_item["food_price"] = food_item.get("food_types")[0].get(
                    "type_price"
                )
                food_item["food_qty"] = 1
                del food_item["_id"]
                result.append(food_item)

    return result


async def get_plans_with_benifits(foods_collection, plans):
    result = []
    for plan in plans:
        plan["plan_benifits"] = await get_foods_by_ids(
            foods_collection=foods_collection, food_ids=plan.get("plan_benifit_ids")
        )
        plan["plan_benifit_ids"] = []
        result.append(plan)
    return result
