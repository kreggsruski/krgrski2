import os
import requests
from urllib.parse import quote

def generate_russian_kids_topics(num_topics=100):
    """Generate Russian children's story topics about animals."""
    
    import os
    from dotenv import load_dotenv

    load_dotenv()
    POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

    if not POLLINATIONS_API_KEY:
        raise ValueError("❌ POLLINATIONS_API_KEY is missing! You MUST set this in your .env file or GitHub Secrets to use the paid API.")

    base_url = "https://gen.pollinations.ai/text/"
    
    system = (
        "Ты креативный автор сказок для детей. "
        "Генерируй короткие названия русских сказок для детей (3-8 лет) о животных. "
        "Каждая сказка должна иметь животного героя и простой моральный урок. "
        "Используй простой, детский язык. "
        "Генерируй ТОЛЬКО названия, каждое в новой строке, без нумерации."
    )
    
    # Different categories for variety
    categories = [
        "Лесные животные (медведи, лисы, зайцы, олени, белки, ежи, волки)",
        "Домашние животные (коровы, куры, свиньи, лошади, овцы, козы, кролики)",
        "Океанские животные (дельфины, черепахи, рыбы, киты, акулы, осьминоги)",
        "Животные джунглей (обезьяны, слоны, попугаи, тигры, львы, панды)",
        "Птицы (совы, орлы, воробьи, ласточки, аисты, лебеди, фламинго)",
        "Насекомые и мелкие существа (бабочки, пчелы, муравьи, божьи коровки)",
    ]
    
    moral_lessons = "дружба, честность, доброта, храбрость, щедрость, терпение, трудолюбие, скромность"
    
    # Rotate through categories for variety
    category_index = num_topics % len(categories)
    category = categories[category_index]
    
    prompt = (
        f"Сгенерируй {num_topics} уникальных названий русских сказок для детей. "
        f"Фокус на: {category}. "
        f"Моральные уроки: {moral_lessons}. "
        "Каждое название в новой строке, без номеров."
    )
    
    url = base_url + quote(prompt)
    params = {
        "model": "openai",
        "temperature": 1.2,
        "system": system
    }
    
    print(f"[topics] Генерация {num_topics} русских тем сказок для детей...")
    print(f"[topics] Категория: {category}")
    
    headers = {"Authorization": f"Bearer {POLLINATIONS_API_KEY}"}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=120)
        r.raise_for_status()
        text = r.text.strip()
        
        # Split into lines and clean
        topics = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Remove numbering if present
        cleaned_topics = []
        for topic in topics:
            # Remove common numbering patterns
            topic = topic.lstrip('0123456789.-) ')
            if len(topic) > 10 and not topic.startswith('['):
                cleaned_topics.append(topic)
        
        return cleaned_topics
        
    except Exception as e:
        print(f"[topics] Ошибка генерации: {e}")
        return []

def generate_topics_in_batches(total=600, batch_size=100):
    """Generate topics in batches to ensure variety and avoid repetition."""
    all_topics = []
    seen = set()
    
    print(f"[topics] Генерация {total} тем в пакетах по {batch_size}...")
    
    batches_needed = (total + batch_size - 1) // batch_size
    
    for batch_num in range(batches_needed):
        print(f"\n[topics] Пакет {batch_num + 1}/{batches_needed}")
        
        # Generate batch
        batch_topics = generate_russian_kids_topics(batch_size)
        
        # Add unique topics
        for topic in batch_topics:
            topic_lower = topic.lower()
            if topic_lower not in seen:
                all_topics.append(topic)
                seen.add(topic_lower)
        
        print(f"[topics] Уникальных тем после пакета: {len(all_topics)}")
        
        # Stop if we have enough
        if len(all_topics) >= total:
            break
    
    # If still not enough, add fallback topics
    if len(all_topics) < total:
        print(f"[topics] Добавление резервных тем...")
        fallback = get_fallback_topics()
        for topic in fallback:
            if len(all_topics) >= total:
                break
            topic_lower = topic.lower()
            if topic_lower not in seen:
                all_topics.append(topic)
                seen.add(topic_lower)
    
    return all_topics[:total]

def get_fallback_topics():
    """Fallback Russian kids story topics if API fails."""
    return [
        "Маленький медвежонок ищет мёд в лесу",
        "Дружелюбная лиса помогает потерявшемуся зайчику",
        "Дельфин спасает маленькую черепаху",
        "Смелая белочка делится орехами",
        "Мудрая сова учит лесных зверей",
        "Весёлые утята учатся плавать",
        "Котёнок находит новый дом",
        "Щенок учится делиться игрушками",
        "Маленькая мышка помогает большому льву",
        "Заяц и черепаха учатся дружбе",
        "Слон забывает и учится извиняться",
        "Попугай учится говорить правду",
        "Маленький пингвин учится храбрости",
        "Кузнечик поёт для друзей",
        "Божья коровка помогает в саду",
        "Бабочка учится терпению",
        "Ёжик делится яблоками",
        "Корова даёт молоко для всех",
        "Цыплёнок учится быть смелым",
        "Овечка делится шерстью",
        "Лошадь помогает на ферме",
        "Свинка учится чистоте",
        "Кролик сажает морковку",
        "Коза взбирается на гору",
        "Утка учится летать",
        "Гусь ведёт друзей домой",
        "Индюк учится скромности",
        "Ослик помогает нести тяжести",
        "Крыса учится доброте",
        "Хомяк собирает запасы на зиму",
        "Бобёр строит дом для семьи",
        "Выдра играет в воде",
        "Лось защищает лес",
        "Волк учится дружбе",
        "Рысь помогает маленьким зверям",
        "Кабан ищет еду в лесу",
        "Косуля учится быстроте",
        "Заяц учится храбрости",
        "Лиса учится честности",
        "Медведь просыпается от зимнего сна",
        "Панда ест бамбук и делится",
        "Коала спит на дереве",
        "Кенгуру носит детёныша в сумке",
        "Жираф тянется к высоким листьям",
        "Зебра учится о полосках",
        "Лев учится быть нежным",
        "Тигр учится делиться",
        "Обезьяна играет с друзьями",
        "Горилла защищает семью",
        "Шимпанзе учится новому",
        "Орангутан помогает в джунглях",
        "Бегемот плавает в реке",
        "Носорог защищает свою территорию",
        "Крокодил учится быть нежным",
        "Змея учится дружбе",
        "Черепаха медленно выигрывает гонку",
        "Ящерица греется на солнце",
        "Хамелеон меняет цвета",
        "Игуана учится лазать",
        "Саламандра учится плавать",
        "Лягушка прыгает в пруд",
        "Жаба учится петь",
        "Тритон находит новый дом",
        "Дельфин учится прыжкам",
        "Кит поёт песни",
        "Акула учится быть дружелюбной",
        "Осьминог помогает друзьям",
        "Кальмар учится прятаться",
        "Медуза плавает в океане",
        "Морская звезда помогает на дне моря",
        "Краб учится ходить прямо",
        "Омар делится едой",
        "Креветка учится плавать",
        "Морской конёк танцует в воде",
        "Рыбка учится в стае",
        "Лосось возвращается домой",
        "Форель прыгает в ручье",
        "Щука учится терпению",
        "Орёл летит высоко в небе",
        "Сокол учится охотиться",
        "Ястреб защищает гнездо",
        "Сова учит мудрости",
        "Филин помогает ночью",
        "Ворона учится делиться",
        "Сорока собирает блестящие вещи",
        "Галка учится в группе",
        "Голубь несёт сообщения",
        "Воробей поёт утром",
        "Синица делится едой",
        "Малиновка учится петь",
        "Соловей поёт красивее всех",
        "Ласточка строит гнездо",
        "Аист приносит счастье",
        "Цапля ловит рыбу",
        "Лебедь плавает по озеру",
        "Пеликан делится рыбой",
        "Фламинго стоит на одной ноге",
        "Попугай учится говорить",
        "Тукан имеет цветной клюв",
        "Колибри пьёт нектар",
        "Дятел стучит по дереву",
        "Кукушка поёт в лесу"
    ]

def save_topics_to_file(topics, filename="topics.txt"):
    """Save topics to file."""
    with open(filename, "w", encoding="utf-8") as f:
        for topic in topics:
            f.write(f"{topic}\n")
    print(f"[topics] Сохранено {len(topics)} тем в {filename}")

def load_used_topics():
    """Load previously used topics from used_topics.txt into a set (lowercase)."""
    used = set()
    if os.path.exists("used_topics.txt"):
        with open("used_topics.txt", "r", encoding="utf-8") as f:
            used = {line.strip().lower() for line in f if line.strip()}
    return used

def main():
    """Generate and save Russian kids story topics."""
    print("=" * 60)
    print("=== Генератор Русских Сказок для Детей ===")
    print("=" * 60)
    
    used_topics = load_used_topics()
    
    # Check if topics.txt exists and has content
    try:
        with open("topics.txt", "r", encoding="utf-8") as f:
            existing_topics = [line.strip() for line in f if line.strip()]
        
        # Remove any topics that have already been used
        clean_existing = [t for t in existing_topics if t.lower() not in used_topics]
        if len(clean_existing) != len(existing_topics):
            print(f"[topics] Удалено {len(existing_topics) - len(clean_existing)} уже использованных тем")
            existing_topics = clean_existing
        
        if len(existing_topics) >= 30:
            print(f"[topics] Найдено {len(existing_topics)} тем. Не нужно генерировать новые.")
            # Still save the cleaned list
            save_topics_to_file(existing_topics)
            return
        else:
            print(f"[topics] Найдено только {len(existing_topics)} тем. Генерация новых...")
    except FileNotFoundError:
        print("[topics] Файл topics.txt не существует. Генерация новых тем...")
        existing_topics = []
    
    # Generate 150 new topics in batches (API-based)
    num_to_generate = 150
    print(f"\n[topics] Генерация {num_to_generate} тем через API...")
    new_topics = generate_topics_in_batches(total=num_to_generate, batch_size=50)
    
    # Combine with existing (if any) and remove duplicates
    all_topics = existing_topics + new_topics
    unique_topics = []
    seen = set()
    for topic in all_topics:
        tl = topic.lower()
        if tl not in seen and tl not in used_topics:
            unique_topics.append(topic)
            seen.add(tl)
    
    # Save to file
    save_topics_to_file(unique_topics)
    
    print("=" * 60)
    print(f"✅ Сгенерировано {len(unique_topics)} уникальных тем!")
    print("=" * 60)

if __name__ == "__main__":
    main()
