import praw
import pandas as pd
from datetime import datetime
import time


reddit = praw.Reddit(
    client_id="tGQSKu1Lejc5ChP-xMZnaw",
    client_secret="TV4zHWh1lZ1jDbjJDfrdMokA6iajaA",
    user_agent="Homeless-sentiment-analysis by u/Crispygyozadumpling"
)

city_subreddits = {
    "Toronto": "toronto",
    "Vancouver": "vancouver",
    "Montreal" : "montreal",
    "Quebec City" : "quebeccity",
    "Calgary": "Calgary",
    "Ottawa": "ottawa",
    "Edmonton": "Edmonton",
    "Winnipeg": "Winnipeg",
    "Hamilton": "Hamilton",
    "Halifax": "halifax",
    "London": "londonontario",
    "Victoria": "VictoriaBC"
}

# --- Keywords to filter homelessness-related posts ---
# are there any additional keywords that we could use here? 
french_keywords = [
    "sans-abri",          # most common
    "itinérance",         # Quebec term for homelessness
    "itinérant",          # person experiencing homelessness
    "campement",          # encampment
    "campements",         
    "tente",              # tent
    "tentes",
    "abri",               # shelter (generic)
    "refuge",             # shelter (services)
    "dormir dehors",      # sleeping outside
    "vivre dans la rue",  # living on the street
    "crise du logement",  # housing crisis
    "logement",           # housing (broad but useful)
]

keywords = ["homeless", "tent", "shelter", "sleeping rough", "unhoused", "encampment"]
keywords += french_keywords



# --- Fetch comments (TOP 200) ---
def fetch_comments(submission, limit=200):
    comments_data = []

    try:
        submission.comment_sort = "top"
        submission.comments.replace_more(limit=3)  # load SOME extra comments safely

        all_comments = submission.comments.list()

        for comment in all_comments[:limit]:
            if not comment.body or comment.body in ["[deleted]", "[removed]"]:
                continue

            comments_data.append({
                "comment_id": comment.id,
                "post_id": submission.id,
                "comment": comment.body,
                "score": comment.score,
                "created_utc": datetime.utcfromtimestamp(comment.created_utc),
                "parent_id": comment.parent_id,
            })

    except Exception as e:
        print(f"    Error fetching comments for post {submission.id}: {e}")

    return comments_data


# --- Fetch posts + comments ---
def fetch_posts(subreddit_name, keywords, limit_per_keyword=500):
    subreddit = reddit.subreddit(subreddit_name)

    posts = []
    all_comments = []
    seen_ids = set()

    for keyword in keywords:
        print(f"  Searching '{keyword}' in r/{subreddit_name}...")

        try:
            for submission in subreddit.search(keyword, sort="relevant", limit=limit_per_keyword, time_filter="all"):

                # --- Deduplicate ---
                if submission.id in seen_ids:
                    continue
                seen_ids.add(submission.id)

                # --- Filter bad posts ---
                if (
                    submission.id is None or
                    submission.title is None or
                    submission.title.strip() == ""
                ):
                    continue

                # Clean 
                selftext = submission.selftext if submission.selftext not in ["[deleted]", "[removed]"] else ""
                full_text = submission.title + " " + (selftext or "")

                posts.append({
                    "post_id": submission.id,
                    "text": full_text,
                    "title": submission.title,
                    "selftext": selftext,
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                    "created_utc": datetime.utcfromtimestamp(submission.created_utc),
                    "subreddit": subreddit_name,
                    "keyword": keyword,
                    "url": submission.url
                })

                # --- Only fetch comments if post has some ---
                if submission.num_comments > 0:
                    comments = fetch_comments(submission)
                    all_comments.extend(comments)

            time.sleep(5)  # reduce rate limiting

        except Exception as e:
            print(f"    Error with keyword '{keyword}': {e}")

    return posts, all_comments


# =========================
# ===== TEST RUN =====
# =========================

# # --- Select first 6 subreddits ---
# test_subreddits = dict(list(city_subreddits.items())[:6])

# all_posts = []
# all_comments = []

# print(f"\n=== TEST RUN: First 6 subreddits ===\n")

# for city, sub in test_subreddits.items():
#     print(f"\n--- Scraping {city} (r/{sub}) ---")

#     posts, comments = fetch_posts(sub, keywords)

#     # Add city label
#     for p in posts:
#         p["city"] = city

#     for c in comments:
#         c["city"] = city

#     all_posts.extend(posts)
#     all_comments.extend(comments)


# df_posts = pd.DataFrame(all_posts)
# df_comments = pd.DataFrame(all_comments)

# df_posts.to_csv("TEST_reddit_posts.csv", index=False)
# df_comments.to_csv("TEST_reddit_comments.csv", index=False)

# print("\n=== DONE ===")
# print(f"Posts scraped: {len(df_posts)}")
# print(f"Comments scraped: {len(df_comments)}")

all_posts = []
all_comments = []

print(f"\n=== FULL RUN: All subreddits ===\n")

for city, sub in city_subreddits.items():
    print(f"\n--- Scraping {city} (r/{sub}) ---")

    posts, comments = fetch_posts(sub, keywords)

    for p in posts:
        p["city"] = city

    for c in comments:
        c["city"] = city

    all_posts.extend(posts)
    all_comments.extend(comments)

    print(f"Collected so far: {len(all_posts)} posts, {len(all_comments)} comments")

    pd.DataFrame(posts).to_csv(
    "canadian_reddit_posts_partial.csv",
    mode='a',
    header=not pd.io.common.file_exists("canadian_reddit_posts_partial.csv"),
    index=False)

    pd.DataFrame(comments).to_csv(
    "canadian_reddit_comments_partial.csv",
    mode='a',
    header=not pd.io.common.file_exists("canadian_reddit_comments_partial.csv"),
    index=False)


    print(f"Saved progress after {city}")

# Save at the end
df_posts = pd.DataFrame(all_posts)
df_comments = pd.DataFrame(all_comments)

df_posts.to_csv("canadian_reddit_posts.csv", index=False)
df_comments.to_csv("canadian_reddit_comments.csv", index=False)

print("\n=== DONE ===")
