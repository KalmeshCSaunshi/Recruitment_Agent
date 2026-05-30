from sqlalchemy import create_engine

DATABASE_URL = "postgresql://recruitment_user:Recruit%40123@localhost:5432/recruitment_agent"
engine = create_engine(DATABASE_URL)

def test_connection():
    try:
        with engine.connect() as conn:
            print("✅ PostgreSQL Connected Successfully")
    except Exception as e:
        print("❌ Connection Failed")
        print(e)

if __name__ == "__main__":
    test_connection()