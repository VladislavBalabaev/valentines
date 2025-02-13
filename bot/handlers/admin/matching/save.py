import pandas as pd

from db.connect import get_mongo_matches


async def save_matching(matched_df: pd.DataFrame, time_started: str):
    """
    Saves the matching results to the MongoDB 'matches' collection. 
    The results are stored as a dictionary, with the match timestamp as the document ID.
    """
    mongo_matches = get_mongo_matches()

    matched_df = matched_df.copy()
    matched_df.index = matched_df.index.astype(str)
    matched_dict = matched_df.T.to_dict('dict')

    await mongo_matches.insert_one({"_id": time_started, "matching": matched_dict})

    return
