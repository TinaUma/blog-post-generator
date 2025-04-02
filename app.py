import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import requests

# Инициализация FastAPI приложения
app = FastAPI()

# Получаем API-ключи из переменных окружения
openai.api_key = os.getenv("OPENAI_API_KEY")
currentsapi_key = os.getenv("CURRENTS_API_KEY")

# Проверяем, что API-ключи заданы
if not openai.api_key or not currentsapi_key:
    raise ValueError("Переменные окружения OPENAI_API_KEY и CURRENTS_API_KEY должны быть установлены")


# Класс для валидации входных данных
class Topic(BaseModel):
    topic: str


# Функция для получения последних новостей через Currents API
def get_recent_news(topic: str):
    url = "https://api.currentsapi.services/v1/latest-news"
    params = {
        "language": "en",
        "keywords": topic,
        "apiKey": currentsapi_key
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении данных: {response.text}")

    news_data = response.json().get("news", [])
    if not news_data:
        return "Свежих новостей не найдено."

    return "\n".join([article["title"] for article in news_data[:5]])


# Функция для генерации контента
def generate_content(topic: str):
    # Получаем последние новости
    recent_news = get_recent_news(topic)

    try:
        # Генерация заголовка
        prompt_title = f"Придумайте привлекательный и точный заголовок для статьи на тему '{topic}', с учётом актуальных новостей:\n{recent_news}. Заголовок должен быть интересным и ясно передавать суть темы."
        response_title = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt_title}],
            max_tokens=60,
            temperature=0.5,
            stop=["\n"]
        )
        title = response_title.choices[0].message.content.strip()

        # Генерация мета-описания
        prompt_meta = f"Напишите краткое мета-описание (до 160 символов) для статьи с заголовком: '{title}'. Оно должно быть информативным, содержать ключевые слова и побуждать к чтению."
        response_meta = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt_meta}],
            max_tokens=120,
            temperature=0.5,
            stop=["."]
        )
        meta_description = response_meta.choices[0].message.content.strip()

        # Генерация текста поста
        prompt_post = f"""Напишите подробную статью на тему '{topic}', используя последние новости:\n{recent_news}. 
        Статья должна быть:
        1. Информативной и логичной
        2. Содержать не менее 1500 символов (около 200-300 слов)
        3. Иметь четкую структуру с подзаголовками
        4. Включать анализ текущих трендов
        5. Иметь вступление, основную часть и заключение
        6. Включать релевантные примеры из актуальных новостей
        7. Каждый абзац должен быть не менее 3-4 предложений
        8. Текст должен быть легким для восприятия и содержательным
        9. Добавьте эмодзи для живости
        10. В конце добавьте 3-5 хэштегов (например, #Зодиак #Стиль #Мода)
        11. Завершайте статью призывом к действию (например, 'Делитесь в комментариях!')"""
        response_post = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt_post}],
            max_tokens=2000,  # Увеличили для более длинного текста
            temperature=0.5,
            presence_penalty=0.6,
            frequency_penalty=0.6
        )
        post_content = response_post.choices[0].message.content.strip()

        return {
            "title": title,
            "meta_description": meta_description,
            "post_content": post_content
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации контента: {str(e)}")


# Эндпоинт для генерации поста
@app.post("/generate-post")
async def generate_post_api(topic: Topic):
    return generate_content(topic.topic)


# Корневой эндпоинт для проверки сервиса
@app.get("/")
async def root():
    return {"message": "Service is running"}


# Эндпоинт для проверки состояния
@app.get("/heartbeat")
async def heartbeat_api():
    return {"status": "OK"}


# Запуск приложения через Uvicorn
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)