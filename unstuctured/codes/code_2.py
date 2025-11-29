# Convert CSV -> XLSX (preserves emojis)
import pandas as pd
from google.colab import files
import os
CSV_PATH = "/content/qsr_social_feedback_A_60k_with_emojis.csv" 
XLSX_PATH = "/content/qsr_social_feedback_A_60k_with_emojis.xlsx"
encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252"]
for enc in encodings:
    try:
        df = pd.read_csv(CSV_PATH, encoding=enc, low_memory=False)
        print("Loaded with encoding:", enc, "shape:", df.shape)
        break
    except Exception as e:
        last_err = e
else:
    raise RuntimeError(f"Cannot read CSV. Last error: {last_err}")
df.to_excel(XLSX_PATH, index=False)
print("Saved XLSX to:", XLSX_PATH)

files.download(XLSX_PATH)