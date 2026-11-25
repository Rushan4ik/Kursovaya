from uuid import uuid4
from db import repository


def start_round(session, user_id: int, category: str | None = None):
    news = repository.get_random_unseen_news(session, user_id, category)
    if news is None:
        return None
    repository.mark_seen(session, user_id, news.id)
    return news, uuid4().hex


def submit_answer(session, user_id: int, news_id: int, choice: bool, token: str):
    return repository.add_answer(session, user_id, news_id, choice, token)
