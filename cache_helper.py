from cachetools import TTLCache

# Create a cache that holds a maximum of 500 users.
# Each user's data expires after 72 hours (72 * 60 * 60 seconds).
user_cache = TTLCache(maxsize=500, ttl=72 * 60 * 60)

# We will cache a dictionary like this:
# key = username
# value = {
#     "user_data": { ... from get_user_data ... },
#     "contribution_analysis": { ... from analyze_contribution_quality ... }
# }