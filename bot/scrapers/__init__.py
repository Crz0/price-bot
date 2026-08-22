"""
سجل كل المتاجر المدعومة. عشان تضيف متجر جديد لاحقاً:
1. أنشئ ملف جديد (مثلاً jarir.py) بنفس شكل الملفات الموجودة
   (دالة search(query) -> list[dict])
2. استورده هنا وضيفه بقائمة STORES بالأسفل
هذا كل شي -- باقي الكود (main.py) يتعامل مع أي عدد متاجر تلقائياً.
"""
from . import noon
from . import amazon_sa
from . import extra

STORES = [
    ("Noon", noon.search),
    ("Amazon.sa", amazon_sa.search),
    ("Extra", extra.search),
]
