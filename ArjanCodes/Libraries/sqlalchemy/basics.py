from typing import Any

import sqlalchemy as sa
from sqlalchemy import Row
from sqlalchemy.orm import sessionmaker, declarative_base, Mapped, mapped_column

engine = sa.create_engine("sqlite:///:memory:", echo=True)
connection = engine.connect()

metadata = sa.MetaData()

user_table = sa.Table(
    "user",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("username", sa.String),
    sa.Column("email", sa.String),
)


def insert_user(username: str, email: str) -> None:
    query = user_table.insert().values(username=username, email=email)
    connection.execute(query)


def select_user(username: str) -> Row[Any] | None:
    query = user_table.select().where(user_table.c.username == username)
    result = connection.execute(query)
    return result.fetchone()


def main() -> None:
    metadata.create_all(engine)
    insert_user("Arjan", "Arjan@arjancodes.com")
    print(select_user("Arjan"))
    connection.close()

db = sa.create_engine("sqlite:///:memory:", echo=True)
Session = sessionmaker(bind=db)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    email: Mapped[str]

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


def main2() -> None:
    Base.metadata.create_all(db)
    user = User(username="Arjan", email="Arjan@arjancodes.com")

    with Session() as session:
        session.add(user)
        session.commit()
        print(session.query(User).all())



if __name__ == "__main__":
    main()
    print('\n\n\n---------------------------------------------------\n\n\n')
    main2()