# Complete script: load CSV, smart-detect text & sentiment columns, append emojis, save CSV and XLSX (Colab)
import pandas as pd
import re, random, sys, os
from google.colab import files
INPUT_CSV = "/content/qsr_social_feedback_A_60k.csv"
OUTPUT_CSV = "/content/qsr_social_feedback_A_60k_with_emojis.csv"
OUTPUT_XLSX = "/content/qsr_social_feedback_A_60k_with_emojis.xlsx"
def detect_text_col(df):
    possible_text_cols = [c for c in df.columns 
                          if any(k in c.lower() 
                                 for k in ("review","text","comment","message","content","body","post_text","post"))]

    blacklist = ["id", "number", "num", "code"]

    filtered = []
    for c in possible_text_cols:
        if not any(b in c.lower() for b in blacklist):
            filtered.append(c)

    if "post_text" in [col.lower() for col in df.columns]:
        for col in df.columns:
            if col.lower() == "post_text":
                return col


    for prefer in ("post_text","text","review","message","comment","content","body","post"):
        for col in df.columns:
            if col.lower() == prefer or col.lower().endswith("" + prefer) or col.lower().startswith(prefer + ""):
                if not any(b in col.lower() for b in blacklist):
                    return col
    return filtered[0] if filtered else None

def detect_sentiment_col(df):
    label_candidates = [c for c in df.columns if any(k in c.lower() for k in ("sentiment_label","sentimentlabel","label","sentiment"))]
    for exact in ("sentiment_label","sentimentlabel","sentimentLabel","sentimentlabel"):
        for c in df.columns:
            if c.lower() == exact.lower():
                return c
  
    for c in label_candidates:
        if "score" not in c.lower() and "value" not in c.lower():
            return c
    score_candidates = [c for c in df.columns if any(k in c.lower() for k in ("sentiment_score","sentimentscore","score","sentimentvalue"))]
    if score_candidates:
        return score_candidates[0]
    for c in df.columns:
        if "sentiment" in c.lower():
            return c
    return None

print("Loading CSV:", INPUT_CSV)
df = pd.read_csv(INPUT_CSV, low_memory=False)
print("Columns found:", df.columns.tolist())

text_col = detect_text_col(df)
sent_col = detect_sentiment_col(df)
print("Detected text column:", text_col)
print("Detected sentiment column:", sent_col)

if text_col is None:
    raise RuntimeError("No text column detected. Rename your review/post column or set text_col manually.")
if sent_col is None:
    raise RuntimeError("No sentiment column detected. Rename your sentiment column or set sent_col manually.")

# --- find numeric sentiment column if it exists (for stronger emoji weighting) ---
num_sent_col = None
for c in df.columns:
    if c.lower() in ("sentiment_score","sentimentscore","score","sentiment_value","sentimentvalue"):
        num_sent_col = c
        break
if num_sent_col is None:
    for c in df.columns:
        if ("score" in c.lower() or "sentiment" in c.lower()) and pd.api.types.is_numeric_dtype(df[c]):
            num_sent_col = c
            break
print("Numeric sentiment column (if any):", num_sent_col)

positive_emojis = ["😍","🔥","😋","🥰","👍","😊","✨","🤩","❤"]
neutral_emojis  = ["😐","🤔","🙂","👌"]
negative_emojis = ["😡","😤","😞","👎","😭","💢"]

def pick_emojis_by_label_and_score(label, score=None):
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
    return " ".join(random.sample(pool, count)) if count>0 else ""
def get_label(val):
    if pd.isna(val): return "neutral"
    v = str(val).strip().lower()
    try:
        fv = float(v)
        if fv >= 0.05: return "positive"
        if fv <= -0.05: return "negative"
        return "neutral"
    except Exception:
        if any(x in v for x in ("pos","positive","+","good","happy","love","great","excellent")): return "positive"
        if any(x in v for x in ("neg","negative","bad","sad","angry","hate","terrible","poor")): return "negative"
        return "neutral"

def append_emojis(row):
    text = "" if pd.isna(row[text_col]) else str(row[text_col])
    raw_label = row[sent_col] if sent_col in row else None
    label = get_label(raw_label)
    score = None
    if num_sent_col and not pd.isna(row.get(num_sent_col)):
        try:
            score = float(row.get(num_sent_col))
        except Exception:
            score = None
    emo = pick_emojis_by_label_and_score(label, score)
    return f"{text} {emo}".strip()

df["review_text_with_emojis"] = df.apply(append_emojis, axis=1)
df.to_csv(OUTPUT_CSV, index=False)
print("Saved CSV with emojis to:", OUTPUT_CSV)

encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252"]
loaded = False
for enc in encodings:
    try:
        tmp = pd.read_csv(OUTPUT_CSV, encoding=enc, low_memory=False)
        print("Successfully reloaded CSV with encoding:", enc, "shape:", tmp.shape)
        loaded = True
        break
    except Exception as e:
        last_err = e
if not loaded:
    raise RuntimeError(f"Cannot read output CSV for XLSX conversion. Last error: {last_err}")

# write xlsx
df.to_excel(OUTPUT_XLSX, index=False)
print("Saved XLSX to:", OUTPUT_XLSX)

# trigger download in Colab
try:
    files.download(OUTPUT_XLSX)
except Exception as e:
    print("Download failed in this environment; file is at:", OUTPUT_XLSX)
