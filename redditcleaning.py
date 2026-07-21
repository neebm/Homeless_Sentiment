import pandas as pd
import re
import csv


INPUT_FILE = "/home/bhux/mikayla/ProjectLLM-hlth/Homeless_sentiment/canadian_reddit_posts_04-05-2026.csv"

df = pd.read_csv(INPUT_FILE, encoding="utf-8")

# Dataset statistics

print("RAW DATASET")
print(f"Total posts: {len(df):,}")

city_counts = (
    df.groupby("city")
      .size()
      .reset_index(name="posts")
      .sort_values("posts", ascending=False)
)

print(city_counts)

# -------------------------------Remove media / external links
filtered = df.copy()

# Image extensions
image_pattern = (
    r"\.jpg|\.jpeg|\.png|\.gif|\.webp|"
    r"i\.redd\.it|preview\.redd\.it"
)

# Videos
video_pattern = (
    r"\.mp4|\.mov|\.avi|"
    r"v\.redd\.it|youtube\.com|youtu\.be"
)

# External websites
reddit_pattern = r"reddit\.com|redd\.it"

# Remove image posts
filtered = filtered[
    ~filtered["url"].str.contains(image_pattern,
                                  case=False,
                                  na=False)
]

# Remove videos
filtered = filtered[
    ~filtered["url"].str.contains(video_pattern,
                                  case=False,
                                  na=False)
]

# Keep only Reddit-hosted posts
filtered = filtered[
    filtered["url"].str.contains(reddit_pattern,
                                 case=False,
                                 na=False)
]

# Statistics after filtering

print("\n")
print("AFTER MEDIA FILTERING")
print(f"Remaining posts: {len(filtered):,}")

city_counts = (
    filtered.groupby("city")
            .size()
            .reset_index(name="posts")
            .sort_values("posts", ascending=False)
)

print(city_counts)

# -----------------------------------------Flag potentially unrelated posts

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

pattern = "|".join(re.escape(k) for k in keywords)

combined_text = (
    filtered["title"].fillna("") +
    " " +
    filtered["selftext"].fillna("")
)

filtered["contains_keyword"] = combined_text.str.contains(
    pattern,
    case=False,
    regex=True
)

print("\n")
print("TOPIC RELEVANCE")
print("Posts containing keywords:",
      filtered["contains_keyword"].sum())

print("Posts missing keywords:",
      (~filtered["contains_keyword"]).sum())

# Export file for review, manually review and mark
review = filtered[
    filtered["contains_keyword"] == False
]

# review.to_csv(
#     "manual_review_posts.csv",
#     index=False,
#     quoting=csv.QUOTE_ALL
# )

print(f"\nPosts needing review: {len(review)}")


reviewed = pd.read_csv("/home/bhux/mikayla/ProjectLLM-hlth/Homeless_sentiment/manual_review_posts_reviewed.csv")

manual_keep = reviewed[
    reviewed["Relevant"]
    .fillna("")
    .str.upper()
    .eq("Y")
]

automatic_keep = filtered[
    filtered["contains_keyword"]
].copy()

final_posts = pd.concat(
    [automatic_keep, manual_keep],
    ignore_index=True
)

# Remove duplicates if any
final_posts = final_posts.drop_duplicates(subset="post_id")

print("FINAL DATASET")
print(f"Total posts: {len(final_posts)}")

city_counts = (
    final_posts.groupby("city")
    .size()
    .reset_index(name="posts")
    .sort_values("posts", ascending=False)
)
print(city_counts)

# finally clean text

def clean_text(text):

    if pd.isna(text):
        return ""

    text = text.lower()
    text = re.sub(r"http\S+|www\S+", "", text)
    text = re.sub(r"[^a-z0-9\s.,!?']", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


final_clean = filtered.copy()

final_clean["clean_title"] = final_clean["title"].apply(clean_text)
final_clean["clean_text"] = final_clean["selftext"].apply(clean_text)

filtered.to_csv(
    "filtered_posts.csv",
    index=False
)

final_clean.to_csv(
    "clean_posts.csv",
    index=False
)

