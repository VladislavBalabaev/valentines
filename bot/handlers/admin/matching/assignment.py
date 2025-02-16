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


def min_distance(preference1, preference2):
    """
    Compute Euclidean distance between two lists of numbers.
    """
    sq_sum = sum((a - b) ** 2 for a, b in zip(preference1, preference2))
    return sq_sum ** (1 / 2)


def extract_questions(survey):
    """
    Extracts survey answers from a survey dictionary.
    Only keys that start with 'question' are considered,
    and they are sorted numerically.
    """
    questions = []
    for key, value in survey.items():
        if key.startswith("question"):
            try:
                num = int(key.replace("question", ""))
                questions.append((num, int(value)))
            except ValueError:
                continue
    questions.sort(key=lambda x: x[0])
    return [val for _, val in questions]


def score_based_matching(users):
    """
    For each user, computes a preference list of candidates (by username)
    based on the Euclidean distance between the user's ideal partner answers
    (from partner_survey) and each candidate's actual survey answers.

    A candidate is considered only if:
      - It is not the user themself.
      - It is not in the user's blacklist.
      - The candidate's reported sex matches the user's desired partner sex.

    Then, a greedy iterative procedure assigns to each user up to 2 candidates
    (while also ensuring each candidate is not assigned more than twice overall).

    Returns a dictionary: {username: [username1, username2]}.
    """
    # Build a preference list for each user.
    # For each user, sort candidates by increasing score (i.e. lower is better).
    preferences = {}
    for user in users:
        uname = user["info"]["username"]
        partner_pref = extract_questions(user["partner_survey"])
        desired = user["info"]["partner_sex"].lower()
        candidate_list = []
        for candidate in users:
            cand_name = candidate["info"]["username"]
            # Skip self or blacklisted candidates.
            if cand_name == uname or cand_name in user["blacklist"]:
                continue
            # Only consider candidates whose reported sex matches the desired type.
            if candidate["info"]["sex"].lower() != desired:
                continue
            candidate_survey = extract_questions(candidate["survey"])
            score = min_distance(partner_pref, candidate_survey)
            candidate_list.append((cand_name, score))
        # Sort by score ascending (lower score = more attractive).
        candidate_list.sort(key=lambda x: x[1])
        # Save only the candidate usernames in order.
        preferences[uname] = [cand for cand, s in candidate_list]

    # Set the maximum number of assignments per candidate.
    max_assignments = 2
    assignment_counts = defaultdict(int)  # counts how many times a candidate has been assigned.

    # This will hold the final matches for each user.
    matched = {user["info"]["username"]: [] for user in users}

    # Order the users randomly to avoid bias.
    user_order = list(matched.keys())
    random.shuffle(user_order)

    # Iterate repeatedly until no more assignments can be made.
    changed = True
    while changed:
        changed = False
        for user in user_order:
            # If the user already has 2 matches, skip.
            if len(matched[user]) >= 2:
                continue
            # Go through the user’s preference list.
            for candidate in preferences.get(user, []):
                # If this candidate is still available (i.e. has less than 2 assignments)
                # and is not already assigned to this user, assign candidate.
                if candidate not in matched[user] and assignment_counts[candidate] < max_assignments:
                    matched[user].append(candidate)
                    assignment_counts[candidate] += 1
                    changed = True
                    # Stop once the user has 2 matches.
                    if len(matched[user]) == 2:
                        break

    for user in matched:
        if len(matched[user]) < 2:
            needed = 2 - len(matched[user])
            # Filter out candidates already matched.
            available = [cand for cand in preferences.get(user, []) if cand not in matched[user]]
            if available:
                # Randomly choose as many as needed (without worrying about candidate assignment limits here)
                chosen = random.sample(available, min(needed, len(available)))
                matched[user].extend(chosen)

    return matched


async def match():
    """
    Retrieves users from the database, filters out users with matching restrictions, 
    and performs the matching process while respecting blacklists. Attaches random emojis to each match.
    """
    users = await find_all_users(["_id", "info", "survey", "partner_survey", "blacklist", "blocked_bot", "blocked_matching", "finished_profile"])
    # print(users)
    users = [user for user in users if user["blocked_bot"] == "no" and user["blocked_matching"] == "no" and user["finished_profile"] == "yes"]
    # print(users[0])
    matched = score_based_matching(users)

    matched = pd.DataFrame(matched.items(), columns=["username", "assignments"])

    emojis = distinct_emoji_list()
    matched["emoji"] = [secrets.choice(emojis) for _ in range(matched.shape[0])]

    username_to_id = {user["info"]["username"]: user["_id"] for user in users}
    username_to_info = {user["info"]["username"]: user["info"] for user in users}
    matched["_id"] = matched["username"].apply(lambda x: username_to_id[x])
    matched["info"] = matched["username"].apply(lambda x: username_to_info[x])

    matched = matched.set_index("_id").loc[:, ["username", "emoji", "assignments", "info"]]
    return matched
