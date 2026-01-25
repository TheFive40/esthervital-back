from sqlalchemy import create_engine, text
from shared.database import DATABASE_URL

# Create engine
engine = create_engine(DATABASE_URL)

def list_users():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id_usuario, email, nombre FROM usuarios"))
        users = result.fetchall()
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"ID: {user.id_usuario}, Email: {user.email}, Name: {user.nombre}")

if __name__ == "__main__":
    list_users()
