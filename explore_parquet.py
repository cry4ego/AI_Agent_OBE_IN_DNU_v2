import pandas as pd

file_path = "data/vietnamese_legal_dataset/content.parquet"
print(f"Đang đọc {file_path}...")
df = pd.read_parquet(file_path)
print(f"Kích thước dataset: {len(df)} dòng")
print(f"Các cột: {list(df.columns)}")

print("\n=== 3 mẫu đầu tiên ===")
for i in range(min(3, len(df))):
    row = df.iloc[i]
    print(f"\n--- Mẫu {i+1} ---")
    for col in df.columns:
        val = row[col]
        if isinstance(val, str):
            display = val[:200] + "..." if len(val) > 200 else val
        elif isinstance(val, list):
            display = str(val[:2])
        else:
            display = val
        print(f"  {col}: {display}")
