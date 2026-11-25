from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from db.models import User, News, Answer, SeenNews


def get_or_create_user(session, user_id: int, username: str | None) -> User:
    user = session.get(User, user_id)
    if user is None:
        user = User(user_id=user_id, username=username)
        session.add(user)
    else:
        user.username = username
    session.commit()
    return user


def get_random_unseen_news(session, user_id: int, category: str | None = None):
    stmt = select(News).where(~News.id.in_(
        select(SeenNews.news_id).where(SeenNews.user_id == user_id)
    ))
    if category:
        stmt = stmt.where(News.category == category)
    return session.scalars(stmt.order_by(func.random()).limit(1)).first()


def mark_seen(session, user_id: int, news_id: int) -> None:
    if session.get(SeenNews, (user_id, news_id)) is None:
        session.add(SeenNews(user_id=user_id, news_id=news_id))
        session.commit()


def add_answer(session, user_id: int, news_id: int, choice: bool, token: str):
    existing = session.scalar(select(Answer).where(Answer.round_token == token))
    if existing:
        return None, False
    news = session.get(News, news_id)
    user = session.get(User, user_id)
    if news is None or user is None:
        return None, False
    correct = choice == news.is_fake
    answer = Answer(
        user_id=user_id, news_id=news_id, user_choice=choice,
        is_correct=correct, round_token=token
    )
    session.add(answer)
    if correct:
        user.streak += 1
        user.max_streak = max(user.max_streak, user.streak)
    else:
        user.streak = 0
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return None, False
    return (news, correct), True


def get_user_stats(session, user_id: int):
    total = session.scalar(select(func.count(Answer.id)).where(Answer.user_id == user_id)) or 0
    correct = session.scalar(select(func.count(Answer.id)).where(
        Answer.user_id == user_id, Answer.is_correct.is_(True)
    )) or 0
    user = session.get(User, user_id)
    return {
        "total": total,
        "correct": correct,
        "percent": round(correct / total * 100, 1) if total else 0,
        "streak": user.streak if user else 0,
        "max_streak": user.max_streak if user else 0,
    }


def reset_seen_news(session, user_id: int) -> None:
    session.query(SeenNews).filter_by(user_id=user_id).delete()
    session.commit()


def get_news_stats(session):
    total = session.scalar(select(func.count(News.id))) or 0
    fake = session.scalar(select(func.count(News.id)).where(News.is_fake.is_(True))) or 0
    real = total - fake
    # Сложность: доля неправильных ответов по каждой новости.
    rows = session.execute(
        select(News.id, News.text, func.count(Answer.id).label("answers"),
               func.sum(Answer.is_correct == False).label("wrong"))
        .join(Answer, Answer.news_id == News.id, isouter=True)
        .group_by(News.id)
        .having(func.count(Answer.id) > 0)
    ).all()
    hardest = sorted(
        [{"id": r.id, "text": r.text, "answers": r.answers,
          "error_rate": round((r.wrong or 0) / r.answers * 100, 1)} for r in rows],
        key=lambda item: item["error_rate"], reverse=True
    )[:5]
    return {"total": total, "fake": fake, "real": real, "hardest": hardest}


def add_news(session, text: str, is_fake: bool, explanation: str,
             source_url: str | None = None, category: str | None = None):
    if not 20 <= len(text) <= 1000:
        raise ValueError("Текст новости должен содержать 20–1000 символов.")
    if not 10 <= len(explanation) <= 500:
        raise ValueError("Пояснение должно содержать 10–500 символов.")
    news = News(text=text, is_fake=is_fake, explanation=explanation,
                source_url=source_url or None, category=category or None)
    session.add(news)
    session.commit()
    return news


def get_categories(session):
    return list(session.scalars(select(News.category).where(News.category.is_not(None)).distinct()))
