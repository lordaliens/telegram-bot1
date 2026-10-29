import os
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

logger = logging.getLogger(__name__)

genai_available = False
if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        genai_available = True
    except Exception as e:
        logger.warning(f"Could not initialize Google Generative AI: {e}")

def generate_power_yoga_plan(client: Dict[str, Any], progress_logs: List[Dict[str, Any]]) -> str:
    """
    Generates a personalized Power Yoga workout and diet plan in Persian.
    Uses Google Gemini API if GEMINI_API_KEY is configured, otherwise generates a high-quality Persian structured rule-based plan.
    """
    first_name = client.get("first_name", "")
    last_name = client.get("last_name", "")
    age = client.get("age", 0)
    height = client.get("height", 0.0)
    weight = client.get("weight", 0.0)
    history = client.get("training_history", "ثبت نشده")

    progress_summary = ""
    if progress_logs:
        progress_summary = "سوابق تغییرات وزن و پیشرفت شاگرد:\n" + "\n".join(
            [f"- تاریخ: {p.get('recorded_at', '')} | وزن: {p.get('weight')} کیلوگرم | توضیحات: {p.get('notes', '')}" for p in progress_logs]
        )

    prompt = f"""
شما یک مربی ارشد و بین‌المللی پاور یوگا (Power Yoga) و متخصص تغذیه ورزشی هستید.
لطفاً یک برنامه جامع، مدرن و کاملاً اختصاصی به زبان فارسی برای شاگرد زیر تنظیم کنید:

اطلاعات شاگرد:
- نام و نام خانوادگی: {first_name} {last_name}
- سن: {age} سال
- قد: {height} سانتی‌متر
- وزن فعلی: {weight} کیلوگرم
- سوابق تمرینی: {history}

{progress_summary}

برنامه ارائه شده باید شامل بخش‌های زیر باشد:
۱. تحلیل شاخص‌های بدنی و هدف‌گذاری پاور یوگا
۲. برنامه تمرینی هفتگی آنلاین و به‌روز پاور یوگا (شامل گرم کردن، آساناها و سیکل‌های اصلی قدرت/تعادل/انعطاف، سرد کردن و ریلکسیشن Savasana)
۳. دستورالعمل‌های صادر شده برای کنترل تنفس (Pranayama) و ایمنی حرکات
۴. برنامه رژیم غذایی مدرن و متناسب با تمرینات پاور یوگا (وعده‌های اصلی، میان‌وعده‌های قبل و بعد از تمرین، هیدراتاسیون)

پاسخ را کاملاً منظم، شکیل و با لحن حرفه‌ای و انگیزشی به زبان فارسی بنویسید.
"""

    if genai_available and GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")

    # Rule-based generator fallback in case Gemini API key is not set or network fails
    height_m = height / 100.0 if height > 0 else 1.75
    bmi = round(weight / (height_m * height_m), 1) if height_m > 0 else 22.0

    return f"""
🧘‍♂️ **برنامه اختصاصی پاور یوگا و رژیم غذایی هوشمند**
👤 **شاگرد:** {first_name} {last_name} | **سن:** {age} سال | **قد:** {height} cm | **وزن:** {weight} kg
📊 **شاخص توده بدنی (BMI):** {bmi}

---

### ۱. تحلیل بدنی و هدف‌گذاری
با توجه به سابقه تمرینی ({history}) و وزن فعلی {weight} کیلوگرم، تمرکز این دوره بر **افزایش استقامت عضلانی، بهبود تعادل دینامیک، تقویت عضلات کور (Core) و چربی‌سوزی هوشمند** با سیکل‌های پاور یوگا خواهد بود.

---

### ۲. برنامه تمرینی آنلاین و روزآمد پاور یوگا (۴ روز در هفته)

#### 🏋️‍♂️ روز اول: قدرت حرکتی و تقویت عضلات کور (Core & Power Flow)
- **گرم کردن (۱۰ دقیقه):** ۵ دور سلام بر خورشید الف (Surya Namaskar A) + تنفس عمیق شکمی
- **سیکل اصلی (۳۰ دقیقه):**
  - چاتورانگا دانداسانا (Chaturanga Dandasana) 🔁 ۱۰ مرتبه همراه با مکث ۳ ثانیه
  - وضعیت سگ سر پایین به سگ سر بالا (Downward to Upward Dog Flow) 🔁 ۸ مرتبه
  - ژست جنگجو ۲ (Virabhadrasana II) ⏱ هر طرف ۴۵ ثانیه
  - ژست کلاغ (Bakasana) ⏱ ۳ ست ۱۵ ثانیه‌ای (جهت تعادل و قدرت مچ/شانه)
- **سرد کردن (۱۰ دقیقه):** ژست کودک (Balasana) + ساواسان (Savasana) با تنفس ریتمیک

#### 🧘‍♀️ روز دوم: انعطاف‌پذیری و تعادل پیشرفته (Flexibility & Balance Flow)
- **گرم کردن (۱۰ دقیقه):** ۵ دور سلام بر خورشید ب (Surya Namaskar B)
- **سیکل اصلی (۳۰ دقیقه):**
  - ژست مثلث (Trikonasana) ⏱ هر طرف ۵۰ ثانیه
  - ژست درخت (Vrikshasana) ⏱ هر طرف ۱ دقیقه
  - ژست ملخ (Salabhasana) 🔁 ۳ ست ۱۰ تایی برای تقویت فیله کمر
- **سرد کردن (۱۰ دقیقه):** کشش همسترینگ نشسته + ساواسان

#### 🏋️‍♂️ روز سوم: استقامت و چربی‌سوزی پاور یوگا (Dynamic Cardio Power)
- **سیکل هوازی یوگا (۳۵ دقیقه):**
  - پرش از سگ سر پایین به پلانک 🔁 ۱۲ مرتبه
  - ژست صندلی (Utkatasana) با مکث ۳۰ ثانیه‌ای 🔁 ۴ ست
  - ژست جنگجو ۳ (Virabhadrasana III) ⏱ هر طرف ۳۰ ثانیه
- **سرد کردن (۱۰ دقیقه):** ریلکسیشن عمیق و مدیتیشن تمرکزی

#### 🧘‍♀️ روز چهارم: بازیابی فعال و کشش عمیق (Active Recovery)
- کشش کامل زنجیره پشتی، باز کردن لگن (Pigeon Pose) و کشش ستون فقرات به مدت ۳۰ دقیقه.

---

### ۳. برنامه رژیم غذایی هوشمند و متناسب با تمرینات
- **صبحانه:** ۲ عدد تخم‌مرغ آب‌پز + ۱ کف دست نان سنگک + ۳۰ گرم پنیر کم‌چرب و گردو + چای سبز
- **میان‌وعده صبح:** ۱ عدد سیب یا فیله فیبردار + ۵ عدد بادام درختی
- **ناهار:** ۱۵۰ گرم سینه مرغ یا ماهی گریل‌شده + ۱ لیوان برنج قهوه‌ای/کته + بشقاب سالاد فصل با روغن زیتون و لیمو
- **میان‌وعده قبل تمرین (۱ ساعت قبل):** ۱ عدد موز + ۱ قاشق مربی‌خوری عسل یا کره بادام‌زمینی
- **میان‌وعده بعد تمرین (بلافاصله):** اسکوپ پروتئین یا ۱ لیوان شیر کم‌چرب + ۲ عدد خرما
- **شام:** بشقاب سبزیجات بخارپز (بروکلی، هویج، کدو) + ۱۰۰ گرم عدسی یا عدس‌پلو کم‌چرب
- **هیدراتاسیون:** حداقل ۸ تا ۱۰ لیوان آب در روز.
"""
