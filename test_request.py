import requests

url = "http://localhost:8000/generate-post"
data = {"topic": "Что говорит ваш знак зодиака о вашем стиле?"}
response = requests.post(url, json=data)
print(response.json())
