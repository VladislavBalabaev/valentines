import random
import secrets
import pandas as pd
from collections import defaultdict

from .emojis import distinct_emoji_list
from db.operations.users import find_all_users


def uniform_blacklist_matching(blacklists):
    """
    Matches users while respecting their blacklists. Each user is matched with up to 2 candidates 
    who are not in their blacklist and have not exceeded the maximum number of assignments.
    """
    max_assignments = 2
    # max_assignments = (2 * len(users)) // len(users) + 1
    users = list(blacklists.keys())
    matched = {user: [] for user in users}
    assignment_counts = defaultdict(int)                # a dictionary that provides a default value for a non-existent key


    for user in users:
        possible_candidates = [u for u in users if u != user and u not in blacklists[user]]
        random.shuffle(possible_candidates)

        candidates_sorted = sorted(possible_candidates, key=lambda u: assignment_counts[u])

        for candidate in candidates_sorted:
            if len(matched[user]) < 2 and assignment_counts[candidate] < max_assignments:
                matched[user].append(candidate)
                assignment_counts[candidate] += 1

                if len(matched[user]) == 2:
                    break

    return matched


async def match():
    """
    Retrieves users from the database, filters out users with matching restrictions, 
    and performs the matching process while respecting blacklists. Attaches random emojis to each match.
    """
    users = await find_all_users(["_id", "info", "blacklist", "blocked_bot", "active_matching", "blocked_matching"])
    users = [user for user in users if user["blocked_bot"] == "no" and user["active_matching"] == "yes" and user["blocked_matching"] == "no"]

    blacklists = {user["info"]["username"]: user["blacklist"] for user in users}
    matched = uniform_blacklist_matching(blacklists)
    matched = pd.DataFrame(matched.items(), columns=["username", "assignments"])

    emojis = distinct_emoji_list()
    matched["emoji"] = [secrets.choice(emojis) for _ in range(matched.shape[0])]

    username_to_id = {user["info"]["username"]: user["_id"] for user in users}
    username_to_info = {user["info"]["username"]: user["info"] for user in users}
    matched["_id"] = matched["username"].apply(lambda x: username_to_id[x])
    matched["info"] = matched["username"].apply(lambda x: username_to_info[x])

    matched = matched.set_index("_id").loc[:, ["username", "emoji", "assignments", "info"]]

    return matched
