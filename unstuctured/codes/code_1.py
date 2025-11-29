import pandas as pd
import re, random, sys, os
import emoji
INPUT = "/content/qsr_social_feedback_A_60k.csv"
OUTPUT = "/content/qsr_social_feedback_A_60k_with_emojis.csv"
df = pd.read_csv(INPUT, low_memory=False)
print("Loaded file. Columns:\n", df.columns.tolist())
def detect_text_col(df):
    candidates = [c for c in df.columns if any(k in c.lower() for k in ("review","text","comment","message","post"))]
    return candidates[0] if candidates else None

def detect_sentiment_col(df):
    candidates = [c for c in df.columns if any(k in c.lower() for k in ("sentiment","sentimental","sentiment_label","sentimentscore","sentiment_score","label"))]
    return candidates[0] if candidates else None
text_col = detect_text_col(df)
sent_col = detect_sentiment_col(df)
print("Auto-detected text column:", text_col)
print("Auto-detected sentiment column:", sent_col)
if text_col is None:
    raise RuntimeError("No text column detected. Rename your review column or set text_col manually.")
if sent_col is None:
    raise RuntimeError("No sentiment column detected. Rename your sentiment column or set sent_col manually.")
positive_emojis = ["😍","🔥","😋","🥰","👍","😊","✨","🤩","❤"]
neutral_emojis  = ["😐","🤔","🙂","👌"]
negative_emojis = ["😡","😤","😞","👎","😭","💢"]
num_sent_col = None
for c in df.columns:
    if c.lower() in ("sentiment_score","sentimentscore","score"):
        num_sent_col = c
        break
def pick_emojis_by_label_and_score(label, score=None):
    # stronger score -> more emojis
    if label == "positive":
        pool = positive_emojis
        count = 1 if score is None else (2 if score>0.6 else 1)
    elif label == "negative":
        pool = negative_emojis
        count = 1 if score is None else (2 if score<-0.6 else 1)
    else:
        pool = neutral_emojis
        count = 1
    count = min(count, len(pool))
    return " ".join(random.sample(pool, count))
def get_label(val):
    if pd.isna(val): return "neutral"
    v = str(val).strip().lower()
    try:
        fv = float(v)
        if fv >= 0.05: return "positive"
        if fv <= -0.05: return "negative"
        return "neutral"
    except Exception:
        if any(x in v for x in ("pos","positive","+","good","happy","love")): return "positive"
        if any(x in v for x in ("neg","negative","bad","sad","angry","hate")): return "negative"
        return "neutral"
def append_emojis(row):
    text = "" if pd.isna(row[text_col]) else str(row[text_col])
    raw_label = row[sent_col] if sent_col in row else None
    label = get_label(raw_label)
    score = None
    if num_sent_col and not pd.isna(row.get(num_sent_col)):
        try:
            score = float(row[num_sent_col])
        except Exception:
            score = None
    emo = pick_emojis_by_label_and_score(label, score)
    return f"{text} {emo}".strip()
df["review_text_with_emojis"] = df.apply(append_emojis, axis=1)
df.to_csv(OUTPUT, index=False)
print("Saved:", OUTPUT)
print(df[[text_col, sent_col, "review_text_with_emojis"]].head(8).to_string(index=False))