async def get_next_sequence(collection_IDS, start_value=100):
    counter_doc = await collection_IDS.find_one_and_update(
        {"_id": "users"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    return start_value + counter_doc["seq"]


def format_number_to_fixed_length(number, length=6):
    number_string = str(number)

    if len(number_string) < length:
        leading_zeros = length - len(number_string)
        number_string = "0" * leading_zeros + number_string

    elif len(number_string) > length:
        number_string = number_string[:length]

    return "EE" + number_string
