
import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+psycopg2://neondb_owner:npg_deE7FBOQ3Cuc@ep-lingering-voice-a1cvl42u-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
)

def run_etl():
    df = pd.read_csv("movies.csv")
    df.dropna(inplace=True)

    with engine.connect() as conn:
        for _, row in df.iterrows():
            conn.execute(
                text("INSERT INTO movies (title, genre, rating) VALUES (:t,:g,:r)"),
                {"t": row["title"], "g": row["genre"], "r": row["rating"]}
            )
        conn.commit()

if __name__ == "__main__":
    run_etl()
