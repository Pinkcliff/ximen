import pandas as pd
import openpyxl
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 读取Excel文件
df = pd.read_excel(PROJECT_ROOT / 'data' / '点位表.xlsx')

print("=" * 60)
print("点位表内容:")
print("=" * 60)
print(f"总行数: {len(df)}")
print(f"列名: {df.columns.tolist()}")
print("\n前15行数据:")
print("-" * 60)

for idx, row in df.head(15).iterrows():
    name = str(row.iloc[0]) if pd.notna(row.iloc[0]) else "NaN"
    addr = str(row.iloc[1]) if pd.notna(row.iloc[1]) else "NaN"
    dtype = str(row.iloc[2]) if pd.notna(row.iloc[2]) else "NaN"
    print(f"{idx:2d}. 名称: {name:30s} 地址: {addr:15s} 类型: {dtype}")

print("\n" + "=" * 60)
print("完整点位表:")
print("=" * 60)
print(df.to_string())
