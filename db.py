from sqlalchemy import create_engine

DATABASE_URL = "postgresql+psycopg2://neondb_owner:npg_deE7FBOQ3Cuc@ep-lingering-voice-a1cvl42u-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def get_engine():
    return create_engine(DATABASE_URL)



