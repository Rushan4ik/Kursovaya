from db.models import User, News
from services.game import submit_answer
from db.repository import get_user_stats, reset_seen_news, mark_seen


def setup_data(session):
    session.add(User(user_id=1, username="tester"))
    news = News(text="Достаточно длинный учебный текст новости для проверки.", is_fake=True,
                explanation="Демонстрационное пояснение.")
    session.add(news)
    session.commit()
    return news


def test_correct_answer_updates_stats_and_streak(session):
    news = setup_data(session)
    result, created = submit_answer(session, 1, news.id, True, "token-1")
    assert created is True
    assert result[1] is True
    stats = get_user_stats(session, 1)
    assert stats["total"] == 1
    assert stats["correct"] == 1
    assert stats["streak"] == 1


def test_wrong_answer_resets_streak(session):
    news = setup_data(session)
    submit_answer(session, 1, news.id, False, "token-2")
    assert get_user_stats(session, 1)["streak"] == 0


def test_duplicate_callback_is_ignored(session):
    news = setup_data(session)
    first, created_first = submit_answer(session, 1, news.id, True, "same-token")
    second, created_second = submit_answer(session, 1, news.id, True, "same-token")
    assert created_first is True
    assert created_second is False
    assert second is None
    assert get_user_stats(session, 1)["total"] == 1


def test_reset_seen_does_not_delete_answers(session):
    news = setup_data(session)
    mark_seen(session, 1, news.id)
    submit_answer(session, 1, news.id, True, "token-3")
    reset_seen_news(session, 1)
    assert get_user_stats(session, 1)["total"] == 1
