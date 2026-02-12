import pandas as pd
import os
import uuid
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, bindparam
from sqlalchemy.exc import SQLAlchemyError

# =====================================================
# 1️⃣ Environment Setup
# =====================================================
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOSTNAME")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
    raise ValueError("❌ Missing DB environment variables.")

engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    pool_pre_ping=True
)

print("✅ Database connected.")

# =====================================================
# 2️⃣ Load Post IDs
# =====================================================
try:
    df_posts = pd.read_csv("post_table.csv")

    if "id" not in df_posts.columns:
        raise ValueError("'id' column not found in CSV")

    post_ids = df_posts["id"].dropna().unique().tolist()
    post_ids = [uuid.UUID(pid) for pid in post_ids]

    print(f"📦 Loaded {len(post_ids)} post IDs")

except Exception as e:
    print(f"❌ CSV Error: {e}")
    exit()

# =====================================================
# 3️⃣ Utility: Batched Query Executor
# =====================================================
BATCH_SIZE = 1000

def fetch_in_batches(query, ids, param_name):
    all_data = []

    for i in range(0, len(ids), BATCH_SIZE):
        batch_ids = ids[i:i+BATCH_SIZE]

        df_batch = pd.read_sql(
            query,
            engine,
            params={param_name: batch_ids}
        )

        all_data.append(df_batch)

        print(f"🔄 Processed batch {i // BATCH_SIZE + 1}")

    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()


# =====================================================
# 4️⃣ Query: Comments by post_id
# =====================================================
comment_query = text("""
    SELECT *
    FROM "Comment"
    WHERE post_id IN :post_ids
""").bindparams(
    bindparam("post_ids", expanding=True)
)

print("🚀 Fetching Comments...")
df_comments = fetch_in_batches(comment_query, post_ids, "post_ids")

print(f"✅ Retrieved {len(df_comments)} comments")

# Extract comment IDs for next step
comment_ids = []
if not df_comments.empty:
    comment_ids = [uuid.UUID(str(cid)) for cid in df_comments["id"].tolist()]

# =====================================================
# 5️⃣ Query: Post Likes (Like table)
# =====================================================
like_query = text("""
    SELECT *
    FROM "Like"
    WHERE post_id IN :post_ids
""").bindparams(
    bindparam("post_ids", expanding=True)
)

print("🚀 Fetching Post Likes...")
df_likes = fetch_in_batches(like_query, post_ids, "post_ids")

print(f"✅ Retrieved {len(df_likes)} post likes")

# =====================================================
# 6️⃣ Query: Comment Likes
# =====================================================
comment_like_query = text("""
    SELECT *
    FROM "CommentLike"
    WHERE comment_id IN :comment_ids
""").bindparams(
    bindparam("comment_ids", expanding=True)
)

print("🚀 Fetching Comment Likes...")
df_comment_likes = fetch_in_batches(comment_like_query, comment_ids, "comment_ids")

print(f"✅ Retrieved {len(df_comment_likes)} comment likes")

video_view_query = text("""
    SELECT *
    FROM "VideoViewStat"
    WHERE video_id IN :video_ids
""").bindparams(
    bindparam("video_ids", expanding=True)
)
print("🚀 Fetching Video View Stats...")

df_video_views = fetch_in_batches(
    video_view_query,
    post_ids,          # same post_ids used as video_ids
    "video_ids"
)

print(f"✅ Retrieved {len(df_video_views)} video view stat records")


# =====================================================
# 7️⃣ Export Everything
# =====================================================
try:
    df_comments.to_csv("comments.csv", index=False)
    df_likes.to_csv("post_likes.csv", index=False)
    df_comment_likes.to_csv("comment_likes.csv", index=False)
    df_video_views.to_csv("video_view_stats.csv", index=False)


    print("📁 All data exported successfully.")

except Exception as e:
    print(f"❌ Export error: {e}")

print("🎉 Script completed successfully.")
