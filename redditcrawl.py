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

# --- Collect posts ---
def fetch_posts(subreddit_name, keywords, limit_per_keyword=1000):
    subreddit = reddit.subreddit(subreddit_name)
    posts = []
    seen_ids = set()
    
    for keyword in keywords:
        print(f"  Searching '{keyword}' in r/{subreddit_name}...")

        try:
            for submission in subreddit.search(keyword, sort="relevant", limit=limit_per_keyword, time_filter="all"):
                
                # created_time = datetime.utcfromtimestamp(submission.created_utc)

                # if not (start_date <= created_time <= end_date):
                    #continue

                if submission.id not in seen_ids:
                    seen_ids.add(submission.id)

                    posts.append({
                        "id": submission.id,
                        "title": submission.title,
                        "selftext": submission.selftext,
                        "score": submission.score,
                        "num_comments": submission.num_comments,
                        "created_utc": datetime.utcfromtimestamp(submission.created_utc),
                        "subreddit": subreddit_name,
                        "keyword": keyword,
                        "url": submission.url
                    })

            time.sleep(3)  # avoid rate limiting

        except Exception as e:
            print(f"    Error with keyword '{keyword}': {e}")

    return posts

all_posts = []
for city, sub in city_subreddits.items():
    print(f"Fetching posts from r/{sub}...")
    city_posts = fetch_posts(sub, keywords)

    for p in city_posts:
        p["city"] = city
    all_posts.extend(city_posts)

# --- Save to CSV ---
df = pd.DataFrame(all_posts)
df.to_csv("canadian_homelessness_reddit_posts_raw.csv", index=False)
print(f"Saved {len(df)} posts to canadian_homelessness_reddit_posts.csv")