import argparse
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker

fake_vi = Faker("vi_VN")
fake_en = Faker("en_US")

# 1. SYSTEM PROMPT — giống prompt dùng trong app Android
SYSTEM_PROMPT = (
    "You are Mobi-Assistant. Analyze the user command and return ONLY "
    "a valid JSON object. No markdown, no extra text, no explanation."
)

# 2. DỮ LIỆU THAM CHIẾU — app, chủ đề tin tức, từ khóa thời gian
APPS = {
    "TikTok": "com.zhiliaoapp.musically",
    "Instagram": "com.instagram.android",
    "Facebook": "com.facebook.katana",
    "YouTube": "com.google.android.youtube",
    "Zalo": "com.zing.zalo",
    "Messenger": "com.facebook.orca",
    "Twitter": "com.twitter.android",
    "Shopee": "com.shopee.vn",
    "Lazada": "com.lazada.android",
    "Snapchat": "com.snapchat.android",
    "Telegram": "org.telegram.messenger",
    "Discord": "com.discord",
    "Spotify": "com.spotify.music",
    "Netflix": "com.netflix.mediaclient",
    "Gmail": "com.google.android.gm",
    "Viber": "com.viber.voip",
    "Line": "jp.naver.line.android",
    "WhatsApp": "com.whatsapp",
    "Tinder": "com.tinder",
    "Grab": "com.grabtaxi.passenger",
    "Be": "com.be.driver",
    "Tiki": "com.tiki.android",
    "Sendo": "com.sendo.android",
    "Momo": "com.momo.android",
    "ZingMP3": "com.zing.mp3",
    "VieON": "com.vieon.android",
}

NEWS_TOPICS_VI = [
    "AI", "công nghệ", "thể thao", "bóng đá Việt Nam", "kinh tế", "chứng khoán",
    "crypto", "bất động sản", "thời tiết", "giáo dục", "y tế", "du lịch",
    "ô tô điện", "trí tuệ nhân tạo", "game", "phim ảnh", "âm nhạc",
    "chính trị", "covid", "biến đổi khí hậu", "khởi nghiệp", "startup",
    "bóng đá quốc tế", "cổ phiếu", "thị trường chứng khoán", "ngân hàng",
    "lạm phát", "giá vàng", "dầu khí", "năng lượng tái tạo", "xe máy điện",
    "smartphone", "5G", "metaverse", "blockchain", "NFT", "âm nhạc Kpop",
    "phim Việt Nam", "series Netflix", "bóng chuyền", "Olympic",
    "bầu cử", "quốc hội", "ngoại giao", "môi trường", "ô nhiễm",
]

NEWS_TOPICS_EN = [
    "artificial intelligence", "technology", "sports", "stock market",
    "climate change", "space exploration", "cryptocurrency", "politics",
    "health", "travel", "electric vehicles", "gaming", "movies", "music",
    "soccer", "international relations", "inflation", "gold prices",
    "renewable energy", "smartphones", "5G technology", "blockchain",
    "metaverse", "NFT", "Kpop", "Hollywood", "cybersecurity", "AI ethics",
    "remote work", "mental health", "sustainable living", "fintech",
]

# Các cách diễn đạt thời gian tương đối trong tiếng Việt -> ngày offset
RELATIVE_DAYS_VI = {
    "hôm nay": 0,
    "ngày hôm nay": 0,
    "ngày mai": 1,
    "mai": 1,
    "sáng mai": 1,
    "ngày kia": 2,
    "ngày mốt": 2,
    "3 ngày nữa": 3,
    "tuần sau": 7,
    "tuần tới": 7,
    "cuối tuần này": 5,
    "thứ 2 tới": 7,
    "tuần này": 0,
    "ngày mai lúc": 1,
    "4 ngày nữa": 4,
    "5 ngày nữa": 5,
}

# Buổi trong ngày -> khung giờ ngẫu nhiên hợp lý
TIME_OF_DAY_VI = {
    "sáng": (5, 11),
    "trưa": (11, 13),
    "chiều": (13, 18),
    "tối": (18, 22),
    "đêm": (22, 23),
    "khuya": (23, 23),
    "sớm": (6, 9),
    "buổi sáng sớm": (5, 8),
}


def random_time_str():
    """Sinh giờ ngẫu nhiên dạng HH:MM."""
    h = random.randint(0, 23)
    m = random.choice([0, 5, 10, 15, 20, 30, 45])
    return f"{h:02d}:{m:02d}"


def time_from_period(period: str):
    """Sinh giờ hợp lý dựa theo buổi (sáng/trưa/chiều/tối)."""
    lo, hi = TIME_OF_DAY_VI[period]
    h = random.randint(lo, hi)
    m = random.choice([0, 15, 30, 45])
    return f"{h:02d}:{m:02d}"


def make_example(instruction, user_input, output_dict):
    return {
        "instruction": instruction,
        "input": user_input,
        "output": json.dumps(output_dict, ensure_ascii=False),
    }


# 3. GENERATOR: SET_ALARM — đặt báo thức với nhiều ngữ cảnh thời gian
def gen_set_alarm(n):
    examples = []

    templates_simple = [
        "đặt báo thức {time}",
        "đặt báo thức lúc {time}",
        "báo thức {time} {day}",
        "nhắc tôi lúc {time} {day}",
        "đặt giờ báo thức {time}",
        "đặt cho tôi báo thức {time} {day}",
        "làm ơn đặt báo thức {time}",
        "hãy đặt báo thức lúc {time} {day} giúp tôi",
        "tôi cần báo thức lúc {time}",
        "set alarm at {time}",
        "wake me up at {time}",
        "set an alarm for {time} {day_en}",
        "please set an alarm at {time}",
        "can you set an alarm for {time}",
        "I need an alarm at {time} {day_en}",
        "báo thức cho tôi vào {time} {day}",
        "đặt nhắc nhở lúc {time}",
        "tạo báo thức {time} sáng mai",
        "wake me tomorrow at {time}",
        "set alarm tomorrow {time}",
        "đánh thức tôi lúc {time}",
    ]

    templates_period = [
        "đặt báo thức {h}h {period}",
        "đặt báo thức {h} giờ {period} {day}",
        "báo thức {h}h{m} {period}",
        "nhắc tôi dậy lúc {h}h {period} {day}",
        "đặt báo thức {h}h{m} {period} {day} giúp tôi",
        "tôi muốn báo thức lúc {h} giờ {period}",
        "set an alarm for {h} {period_en} {day_en}",
        "báo thức {period} {h} giờ {day}",
        "đặt báo thức vào buổi {period} lúc {h}h",
        "wake me up in the {period_en} at {h}",
    ]

    templates_recurring = [
        "đặt báo thức {time} hàng ngày",
        "đặt báo thức {time} mỗi ngày",
        "báo thức {time} các ngày trong tuần",
        "nhắc tôi lúc {time} mỗi sáng",
        "đặt báo thức lặp lại lúc {time}",
        "mỗi ngày báo thức cho tôi lúc {time}",
        "set a daily alarm at {time}",
        "remind me every day at {time}",
        "set a recurring alarm for {time}",
        "báo thức {time} mỗi sáng chủ nhật",
        "đặt báo thức hàng tuần vào {time}",
        "daily reminder at {time}",
        "set alarm every weekday at {time}",
    ]

    days_vi = list(RELATIVE_DAYS_VI.keys())
    period_en_map = {"sáng": "AM", "trưa": "noon", "chiều": "PM", "tối": "PM", "đêm": "PM", "khuya": "PM"}

    for _ in range(n):
        kind = random.choice(["simple", "period", "recurring"])

        if kind == "simple":
            tmpl = random.choice(templates_simple)
            time_str = random_time_str()
            day_key = random.choice(days_vi)
            day_offset = RELATIVE_DAYS_VI[day_key]
            date_value = "tomorrow" if day_offset == 1 else (
                "today" if day_offset == 0 else f"+{day_offset}d"
            )
            label = random.choice([
                "Báo thức", "Alarm", "Dậy thôi", "Nhắc việc",
                "Thức dậy", "Wake up", "Đi làm", "Họp", "Tập gym", "Ăn sáng"
            ])

            user_input = tmpl.format(
                time=time_str, day=day_key,
                day_en="tomorrow" if day_offset == 1 else "today"
            )
            output = {
                "action": "SET_ALARM",
                "confidence": round(random.uniform(0.92, 0.99), 2),
                "language": "en" if "set" in tmpl or "wake" in tmpl or "alarm at" in tmpl
                            or "I need" in tmpl or "can you" in tmpl else "vi",
                "entities": {"time": time_str, "date": date_value, "label": label},
                "response_text": f"Đã đặt báo thức lúc {time_str}.",
                "clarification": "",
            }
            examples.append(make_example(SYSTEM_PROMPT, user_input, output))

        elif kind == "period":
            tmpl = random.choice(templates_period)
            period = random.choice(list(TIME_OF_DAY_VI.keys()))
            time_str = time_from_period(period)
            h, m = time_str.split(":")
            day_key = random.choice(days_vi)
            day_offset = RELATIVE_DAYS_VI[day_key]
            date_value = "tomorrow" if day_offset == 1 else (
                "today" if day_offset == 0 else f"+{day_offset}d"
            )

            is_en = "set an alarm for" in tmpl
            user_input = tmpl.format(
                h=h.lstrip("0") or "0", m=m, period=period, day=day_key,
                period_en=period_en_map.get(period, "AM"),
                day_en="tomorrow" if day_offset == 1 else "today",
            )
            output = {
                "action": "SET_ALARM",
                "confidence": round(random.uniform(0.9, 0.99), 2),
                "language": "en" if is_en else "vi",
                "entities": {"time": time_str, "date": date_value, "label": "Báo thức"},
                "response_text": f"Đã đặt báo thức lúc {time_str}.",
                "clarification": "",
            }
            examples.append(make_example(SYSTEM_PROMPT, user_input, output))

        else:  # recurring
            tmpl = random.choice(templates_recurring)
            time_str = random_time_str()
            user_input = tmpl.format(time=time_str)
            is_en = any(w in tmpl for w in ["daily alarm", "remind me every", "recurring alarm"])
            output = {
                "action": "SET_ALARM",
                "confidence": round(random.uniform(0.88, 0.97), 2),
                "language": "en" if is_en else "vi",
                "entities": {
                    "time": time_str,
                    "date": "recurring_daily",
                    "label": "Báo thức hàng ngày",
                },
                "response_text": f"Đã đặt báo thức lặp lại hàng ngày lúc {time_str}.",
                "clarification": "",
            }
            examples.append(make_example(SYSTEM_PROMPT, user_input, output))

    return examples


# 4. GENERATOR: CANCEL_ALARM
def gen_cancel_alarm(n):
    templates = [
        "hủy báo thức lúc {time}",
        "xóa báo thức {time}",
        "tắt báo thức {time} đi",
        "cancel the alarm at {time}",
        "remove my {time} alarm",
        "hủy hết báo thức {time}",
        "xóa báo thức sáng mai",
        "turn off alarm for {time}",
        "delete the {time} alarm",
        "bỏ báo thức lúc {time} giúp tôi",
    ]
    examples = []
    for _ in range(n):
        tmpl = random.choice(templates)
        time_str = random_time_str()
        user_input = tmpl.format(time=time_str)
        output = {
            "action": "CANCEL_ALARM",
            "confidence": round(random.uniform(0.9, 0.98), 2),
            "language": "en" if "cancel" in tmpl or "remove" in tmpl or "delete" in tmpl or "turn off" in tmpl else "vi",
            "entities": {"time": time_str},
            "response_text": f"Đã hủy báo thức lúc {time_str}.",
            "clarification": "",
        }
        examples.append(make_example(SYSTEM_PROMPT, user_input, output))
    return examples


# 5. GENERATOR: FETCH_NEWS — tìm tin tức theo chủ đề tùy ý người dùng
def gen_fetch_news(n):
    templates_vi_oneshot = [
        "tìm tin tức về {topic}",
        "tìm tin tức mới nhất về {topic}",
        "có tin gì mới về {topic} không",
        "cho tôi xem tin tức {topic}",
        "tóm tắt tin tức {topic} hôm nay",
        "cập nhật tin {topic} mới nhất",
        "tin nóng về {topic}",
        "bản tin {topic} hôm nay",
        "đọc tin {topic} cho tôi",
        "update me on {topic}",
    ]
    templates_vi_scheduled = [
        "tìm tin tức về {topic} và tổng hợp lại mỗi {time} sáng",
        "kiếm thông tin mới về {topic} cho tôi, tổng hợp lúc {time} hàng ngày",
        "mỗi ngày lúc {time} hãy tổng hợp tin tức {topic} cho tôi",
        "tự động cập nhật tin {topic} vào {time} mỗi sáng",
        "tổng hợp tin {topic} lúc {time} mỗi ngày giúp tôi",
        "lên lịch tin tức {topic} lúc {time} sáng hàng ngày",
        "mỗi sáng {time} báo tin {topic} cho tôi",
    ]
    templates_en = [
        "find news about {topic}",
        "what's the latest on {topic}",
        "summarize {topic} news every day at {time}",
        "give me daily updates about {topic} at {time}",
        "latest news on {topic} please",
        "daily briefing on {topic} at {time}",
    ]

    examples = []
    for _ in range(n):
        kind = random.choice(["vi_oneshot", "vi_scheduled", "en"])

        if kind == "vi_oneshot":
            topic = random.choice(NEWS_TOPICS_VI)
            tmpl = random.choice(templates_vi_oneshot)
            user_input = tmpl.format(topic=topic)
            output = {
                "action": "FETCH_NEWS",
                "confidence": round(random.uniform(0.9, 0.98), 2),
                "language": "vi",
                "entities": {"topic": topic, "schedule_time": "", "language": "vi"},
                "response_text": f"Đang tìm tin tức về {topic}...",
                "clarification": "",
            }
        elif kind == "vi_scheduled":
            topic = random.choice(NEWS_TOPICS_VI)
            time_str = time_from_period("sáng")
            tmpl = random.choice(templates_vi_scheduled)
            user_input = tmpl.format(topic=topic, time=time_str.split(":")[0])
            output = {
                "action": "FETCH_NEWS",
                "confidence": round(random.uniform(0.92, 0.99), 2),
                "language": "vi",
                "entities": {"topic": topic, "schedule_time": time_str, "language": "vi"},
                "response_text": f"Đã lên lịch tổng hợp tin tức về {topic} lúc {time_str} mỗi ngày.",
                "clarification": "",
            }
        else:
            topic = random.choice(NEWS_TOPICS_EN)
            time_str = random_time_str()
            tmpl = random.choice(templates_en)
            user_input = tmpl.format(topic=topic, time=time_str)
            output = {
                "action": "FETCH_NEWS",
                "confidence": round(random.uniform(0.9, 0.98), 2),
                "language": "en",
                "entities": {
                    "topic": topic,
                    "schedule_time": time_str if "{time}" in tmpl else "",
                    "language": "en",
                },
                "response_text": f"Fetching news about {topic}...",
                "clarification": "",
            }

        examples.append(make_example(SYSTEM_PROMPT, user_input, output))
    return examples


# 6. GENERATOR: SUMMARIZE_EMAIL — tóm tắt N email mới nhất theo lịch
def gen_summarize_email(n):
    templates_count_time = [
        "tóm tắt {count} email mới nhất vào {time} sáng",
        "tóm tắt {count} mail gần nhất lúc {time} mỗi ngày",
        "mỗi sáng {time} hãy tóm tắt {count} email mới cho tôi",
        "đọc tóm tắt {count} email mới nhất lúc {time}",
        "tổng hợp {count} mail mới vào {time} mỗi sáng giúp tôi",
        "tóm tắt inbox {count} email lúc {time}",
        "daily email summary of {count} at {time}",
    ]
    templates_count_only = [
        "tóm tắt {count} email mới nhất",
        "cho tôi xem tóm tắt {count} mail gần đây",
        "tóm tắt giúp tôi {count} email chưa đọc",
        "tóm tắt {count} email gần đây nhất",
        "brief me on my last {count} emails",
    ]
    templates_en = [
        "summarize my last {count} emails at {time}",
        "give me a summary of {count} recent emails every morning at {time}",
        "summarize {count} unread emails",
        "email digest for {count} messages",
    ]

    examples = []
    for _ in range(n):
        count = random.choice([3, 5, 10, 15, 20, 25, 30])
        kind = random.choice(["count_time", "count_only", "en"])

        if kind == "count_time":
            time_str = time_from_period("sáng")
            tmpl = random.choice(templates_count_time)
            user_input = tmpl.format(count=count, time=time_str.split(":")[0])
            output = {
                "action": "SUMMARIZE_EMAIL",
                "confidence": round(random.uniform(0.92, 0.99), 2),
                "language": "vi",
                "entities": {
                    "email_count": count,
                    "schedule_time": time_str,
                    "language": "vi",
                },
                "response_text": f"Đã lên lịch tóm tắt {count} email mới nhất lúc {time_str} mỗi ngày.",
                "clarification": "",
            }
        elif kind == "count_only":
            tmpl = random.choice(templates_count_only)
            user_input = tmpl.format(count=count)
            output = {
                "action": "SUMMARIZE_EMAIL",
                "confidence": round(random.uniform(0.88, 0.97), 2),
                "language": "vi",
                "entities": {"email_count": count, "schedule_time": "", "language": "vi"},
                "response_text": f"Đang tóm tắt {count} email mới nhất...",
                "clarification": "",
            }
        else:
            time_str = random_time_str()
            tmpl = random.choice(templates_en)
            user_input = tmpl.format(count=count, time=time_str)
            output = {
                "action": "SUMMARIZE_EMAIL",
                "confidence": round(random.uniform(0.9, 0.98), 2),
                "language": "en",
                "entities": {
                    "email_count": count,
                    "schedule_time": time_str if "{time}" in tmpl else "",
                    "language": "en",
                },
                "response_text": f"Summarizing your last {count} emails...",
                "clarification": "",
            }

        examples.append(make_example(SYSTEM_PROMPT, user_input, output))
    return examples


# 7. GENERATOR: SET_APP_LIMIT — giới hạn thời gian sử dụng app
def gen_set_app_limit(n):
    templates_vi = [
        "giới hạn {app} {minutes} phút mỗi ngày",
        "giới hạn {app} {minutes} phút 1 ngày",
        "giới hạn thời gian sử dụng {app} còn {minutes} phút",
        "hạn chế {app} chỉ {minutes} phút/ngày",
        "cho tôi dùng {app} tối đa {minutes} phút mỗi ngày",
        "đặt giới hạn {minutes} phút cho {app}",
        "mỗi ngày chỉ cho dùng {app} {minutes} phút thôi",
        "khóa {app} sau khi dùng {minutes} phút",
        "{app} chỉ được dùng {minutes} phút một ngày",
        "đặt hạn mức {minutes} phút mỗi ngày cho {app}",
        "tôi muốn giới hạn {app} trong {minutes} phút",
        "set daily limit {minutes} phút cho {app}",
        "giới hạn {app} còn lại {minutes} phút hôm nay",
    ]
    templates_vi_hours = [
        "giới hạn {app} {hours} giờ mỗi ngày",
        "giới hạn {app} {hours} tiếng 1 ngày",
        "hạn chế {app} chỉ {hours} giờ/ngày",
        "cho tôi dùng {app} tối đa {hours} giờ mỗi ngày",
        "{app} chỉ được dùng {hours} tiếng một ngày",
        "giới hạn {app} tối đa {hours} tiếng/ngày",
    ]
    templates_en = [
        "limit {app} to {minutes} minutes per day",
        "limit {app} to {hours} hour a day",
        "set a {minutes} minute daily limit for {app}",
        "restrict {app} usage to {minutes} minutes daily",
        "only allow {minutes} minutes of {app} per day",
        "cap {app} at {hours} hours a day",
        "set screen time limit for {app} to {minutes} minutes",
    ]

    examples = []
    for _ in range(n):
        app_name = random.choice(list(APPS.keys()))
        package = APPS[app_name]
        kind = random.choice(["vi_min", "vi_hour", "en"])

        if kind == "vi_min":
            minutes = random.choice([10, 15, 20, 25, 30, 40, 45, 50, 60, 75, 90, 100, 120, 150, 180, 240])
            tmpl = random.choice(templates_vi)
            user_input = tmpl.format(app=app_name, minutes=minutes)
            output = {
                "action": "SET_APP_LIMIT",
                "confidence": round(random.uniform(0.93, 0.99), 2),
                "language": "vi",
                "entities": {
                    "app_name": app_name,
                    "package_name": package,
                    "limit_minutes": minutes,
                },
                "response_text": f"Đã giới hạn {app_name} {minutes} phút/ngày.",
                "clarification": "",
            }
        elif kind == "vi_hour":
            hours = random.choice([1, 2, 3, 4, 5, 6])
            tmpl = random.choice(templates_vi_hours)
            user_input = tmpl.format(app=app_name, hours=hours)
            output = {
                "action": "SET_APP_LIMIT",
                "confidence": round(random.uniform(0.9, 0.98), 2),
                "language": "vi",
                "entities": {
                    "app_name": app_name,
                    "package_name": package,
                    "limit_minutes": hours * 60,
                },
                "response_text": f"Đã giới hạn {app_name} {hours} giờ/ngày.",
                "clarification": "",
            }
        else:
            tmpl = random.choice(templates_en)
            if "{minutes}" in tmpl:
                minutes = random.choice([10, 15, 20, 30, 45, 60, 90, 120, 180])
                user_input = tmpl.format(app=app_name, minutes=minutes)
            else:
                hours = random.choice([1, 2, 3, 4])
                minutes = hours * 60
                user_input = tmpl.format(app=app_name, hours=hours)
            output = {
                "action": "SET_APP_LIMIT",
                "confidence": round(random.uniform(0.92, 0.99), 2),
                "language": "en",
                "entities": {
                    "app_name": app_name,
                    "package_name": package,
                    "limit_minutes": minutes,
                },
                "response_text": f"{app_name} limited to {minutes} minutes per day.",
                "clarification": "",
            }

        examples.append(make_example(SYSTEM_PROMPT, user_input, output))
    return examples


# 8. GENERATOR: BLOCK_APP / UNBLOCK_APP
def gen_block_unblock_app(n):
    block_templates = [
        "khóa {app}", "khóa ứng dụng {app} lại", "chặn {app} ngay",
        "block {app}", "lock {app} now",
        "tắt {app} tạm thời",
        "không cho dùng {app} nữa",
        "block access to {app}",
    ]
    unblock_templates = [
        "mở khóa {app}", "bỏ chặn {app}", "cho tôi dùng {app} lại",
        "unblock {app}", "unlock {app}",
        "bật lại {app}",
        "restore access to {app}",
    ]

    examples = []
    for _ in range(n):
        app_name = random.choice(list(APPS.keys()))
        package = APPS[app_name]
        is_block = random.random() < 0.5

        if is_block:
            tmpl = random.choice(block_templates)
            user_input = tmpl.format(app=app_name)
            output = {
                "action": "BLOCK_APP",
                "confidence": round(random.uniform(0.92, 0.99), 2),
                "language": "en" if "block" in tmpl or "lock" in tmpl else "vi",
                "entities": {"app_name": app_name, "package_name": package},
                "response_text": f"Đã khóa {app_name}.",
                "clarification": "",
            }
        else:
            tmpl = random.choice(unblock_templates)
            user_input = tmpl.format(app=app_name)
            output = {
                "action": "UNBLOCK_APP",
                "confidence": round(random.uniform(0.92, 0.99), 2),
                "language": "en" if "unblock" in tmpl or "unlock" in tmpl else "vi",
                "entities": {"app_name": app_name, "package_name": package},
                "response_text": f"Đã mở khóa {app_name}.",
                "clarification": "",
            }

        examples.append(make_example(SYSTEM_PROMPT, user_input, output))
    return examples


# 9. GENERATOR: QUERY_USAGE — hỏi thống kê sử dụng
def gen_query_usage(n):
    templates = [
        "tôi đã dùng {app} bao nhiêu phút hôm nay",
        "hôm nay tôi dùng {app} bao lâu rồi",
        "thống kê thời gian dùng {app} tuần này",
        "xem báo cáo sử dụng {app} tháng này",
        "how much time did I spend on {app} today",
        "show my {app} usage this week",
        "thời gian dùng {app} hôm nay là bao nhiêu",
        "báo cáo sử dụng {app} tuần qua",
        "screen time for {app} this month",
        "how long have I used {app} today",
    ]
    periods = {
        "hôm nay": "today", "today": "today",
        "tuần này": "week", "this week": "week",
        "tháng này": "month",
        "tuần qua": "week",
    }

    examples = []
    for _ in range(n):
        app_name = random.choice(list(APPS.keys()))
        tmpl = random.choice(templates)
        user_input = tmpl.format(app=app_name)

        period = "today"
        for k, v in periods.items():
            if k in user_input:
                period = v
                break

        output = {
            "action": "QUERY_USAGE",
            "confidence": round(random.uniform(0.9, 0.98), 2),
            "language": "en" if "how" in tmpl or "show" in tmpl else "vi",
            "entities": {"app_name": app_name, "period": period},
            "response_text": f"Đang kiểm tra thống kê sử dụng {app_name}...",
            "clarification": "",
        }
        examples.append(make_example(SYSTEM_PROMPT, user_input, output))
    return examples


# 10. GENERATOR: WIFI / DND SCHEDULE — mở rộng thêm cho agent
def gen_wifi_dnd(n):
    templates_wifi = [
        "tắt wifi lúc {time}", "bật wifi lúc {time}",
        "tự động tắt wifi vào {time} mỗi tối",
        "turn off wifi at {time}",
        "bật WiFi lúc {time} sáng mai",
        "schedule wifi off at {time}",
        "tắt mạng wifi từ {time}",
    ]
    templates_dnd = [
        "bật chế độ không làm phiền từ {time1} đến {time2}",
        "kích hoạt do not disturb từ {time1} tới {time2}",
        "enable do not disturb from {time1} to {time2}",
        "bật DND từ {time1} đến {time2}",
        "turn on silent mode from {time1} to {time2}",
    ]

    examples = []
    for _ in range(n):
        kind = random.choice(["wifi", "dnd"])
        if kind == "wifi":
            tmpl = random.choice(templates_wifi)
            time_str = time_from_period(random.choice(["tối", "đêm", "sáng"]))
            user_input = tmpl.format(time=time_str)
            action = "on" if "bật" in user_input or "turn on" in user_input else "off"
            output = {
                "action": "SET_WIFI_SCHEDULE",
                "confidence": round(random.uniform(0.88, 0.97), 2),
                "language": "en" if "turn" in tmpl else "vi",
                "entities": {
                    "action": action, "time": time_str,
                    "days": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
                },
                "response_text": f"Đã lên lịch {'tắt' if action == 'off' else 'bật'} WiFi lúc {time_str}.",
                "clarification": "",
            }
        else:
            tmpl = random.choice(templates_dnd)
            t1 = time_from_period("tối")
            t2 = time_from_period("sáng")
            user_input = tmpl.format(time1=t1, time2=t2)
            output = {
                "action": "SET_DND_SCHEDULE",
                "confidence": round(random.uniform(0.88, 0.96), 2),
                "language": "en" if "enable" in tmpl else "vi",
                "entities": {"start_time": t1, "end_time": t2},
                "response_text": f"Đã bật chế độ không làm phiền từ {t1} đến {t2}.",
                "clarification": "",
            }
        examples.append(make_example(SYSTEM_PROMPT, user_input, output))
    return examples


# 11. GENERATOR: UNKNOWN — câu mơ hồ / không rõ ý định
#     Quan trọng để model học cách KHÔNG đoán bừa khi không chắc
def gen_unknown(n):
    vague_inputs = [
        "ưm cái gì đó", "hôm nay thế nào", "bạn khỏe không",
        "kể chuyện cười đi", "1 2 3 test", "ờ thì", "ờm",
        "giúp tôi với", "bạn có thể làm những gì", "bạn là ai",
        "ngày hôm nay là ngày gì", "what can you do",
        "tell me a joke", "how are you", "hmm what",
        "blah blah blah", "...", "test test 123",
        "gì vậy", "ok ok", "thử xem", "hello assistant",
        "bạn làm được gì", "random command", "test function",
        "hôm nay ăn gì", "thời tiết hôm nay",
    ]
    help_outputs = (
        "Tôi có thể giúp bạn:\n"
        "• Đặt báo thức: 'Đặt báo thức 7h sáng'\n"
        "• Giới hạn app: 'Giới hạn TikTok 30 phút/ngày'\n"
        "• Khóa app: 'Khóa Instagram'\n"
        "• Tin tức: 'Tìm tin tức về AI mỗi 8h sáng'\n"
        "• Tóm tắt email: 'Tóm tắt 5 email mới nhất lúc 8h sáng'"
    )

    examples = []
    for _ in range(n):
        user_input = random.choice(vague_inputs)
        is_help_question = user_input in ["bạn có thể làm những gì", "what can you do", "bạn làm được gì"]
        output = {
            "action": "UNKNOWN",
            "confidence": round(random.uniform(0.1, 0.5), 2),
            "language": "en" if any(c.isascii() and c.isalpha() for c in user_input[:3])
                        and user_input.islower() and " " in user_input
                        and not any(w in user_input for w in ["ưm", "bạn", "ờ"]) else "vi",
            "entities": {},
            "response_text": help_outputs if is_help_question else
                              "Xin lỗi, tôi chưa hiểu yêu cầu này. Bạn có thể nói rõ hơn không?",
            "clarification": "Bạn muốn tôi giúp gì?",
        }
        examples.append(make_example(SYSTEM_PROMPT, user_input, output))
    return examples


# 12. MAIN — tổng hợp toàn bộ generator theo tỉ lệ
GENERATORS = {
    "set_alarm": (gen_set_alarm, 0.20),
    "cancel_alarm": (gen_cancel_alarm, 0.04),
    "fetch_news": (gen_fetch_news, 0.18),
    "summarize_email": (gen_summarize_email, 0.14),
    "set_app_limit": (gen_set_app_limit, 0.20),
    "block_unblock_app": (gen_block_unblock_app, 0.10),
    "query_usage": (gen_query_usage, 0.06),
    "wifi_dnd": (gen_wifi_dnd, 0.04),
    "unknown": (gen_unknown, 0.04),
}


def main():
    parser = argparse.ArgumentParser(description="Generate fine-tuning dataset for Mobi-Assistant")
    parser.add_argument("--count", type=int, default=5000, help="Tổng số mẫu cần sinh")
    parser.add_argument("--output", type=str, default="../data/train.jsonl")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--val-split", type=float, default=0.1,
                         help="Tỉ lệ tách ra làm validation set")
    args = parser.parse_args()

    random.seed(args.seed)
    Faker.seed(args.seed)

    all_examples = []
    print(f"Sinh dữ liệu cho {args.count} mẫu theo các intent:")
    for name, (gen_fn, ratio) in GENERATORS.items():
        n = max(1, int(args.count * ratio))
        examples = gen_fn(n)
        all_examples.extend(examples)
        print(f"  - {name}: {len(examples)} mẫu")

    random.shuffle(all_examples)

    # Loại bỏ trùng lặp input giống nhau hoàn toàn
    seen = set()
    deduped = []
    for ex in all_examples:
        key = ex["input"].strip().lower()
        if key not in seen:
            seen.add(key)
            deduped.append(ex)

    print(f"\nTổng cộng: {len(all_examples)} mẫu thô -> {len(deduped)} mẫu sau khi loại trùng")

    # Tách train / validation
    val_size = int(len(deduped) * args.val_split)
    val_examples = deduped[:val_size]
    train_examples = deduped[val_size:]

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for ex in train_examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    val_path = output_path.parent / "val.jsonl"
    with open(val_path, "w", encoding="utf-8") as f:
        for ex in val_examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"\nĐã lưu {len(train_examples)} mẫu train -> {output_path}")
    print(f"Đã lưu {len(val_examples)} mẫu validation -> {val_path}")


if __name__ == "__main__":
    main()