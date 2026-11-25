from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    streak: Mapped[int] = mapped_column(Integer, default=0)
    max_streak: Mapped[int] = mapped_column(Integer, default=0)

    answers: Mapped[list["Answer"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class News(Base):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_fake: Mapped[bool] = mapped_column(Boolean, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Answer(Base):
    __tablename__ = "answers"
    __table_args__ = (UniqueConstraint("round_token", name="uq_answers_round_token"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    news_id: Mapped[int] = mapped_column(ForeignKey("news.id"), nullable=False)
    user_choice: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    round_token: Mapped[str] = mapped_column(String(40), nullable=False)

    user: Mapped[User] = relationship(back_populates="answers")
    news: Mapped[News] = relationship()


class SeenNews(Base):
    __tablename__ = "seen_news"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), primary_key=True)
    news_id: Mapped[int] = mapped_column(ForeignKey("news.id"), primary_key=True)
