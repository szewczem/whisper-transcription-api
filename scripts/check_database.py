from sqlalchemy import text

from app.database.session import engine


def main() -> None:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

        print(f"Database check returned: {result.scalar_one()}")


if __name__ == "__main__":
    main()
