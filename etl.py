import pandas as pd
from sqlalchemy import text

def run_etl(uploaded_file, engine):
    # Đọc file CSV người dùng upload
    df = pd.read_csv(uploaded_file)

    # Chuẩn hoá cột
    df.columns = df.columns.str.strip().str.lower()

    # Loại trùng
    df = df.drop_duplicates()

    # Chỉ append vào bảng có sẵn
    df.to_sql(
        "ratings",      # bảng của bạn đã tạo sẵn
        engine,
        if_exists="append",
        index=False
    )

    return df
