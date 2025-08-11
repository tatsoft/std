# إعداد وتشغيل المشروع باستخدام بيئة venv

## خطوات الإنشاء والتشغيل (Windows PowerShell)

1. إنشاء البيئة الافتراضية:
```
python -m venv venv
```

2. تفعيل البيئة:
```
venv\Scripts\Activate
```

3. تثبيت المتطلبات:
```
pip install -r requirements.txt
```

4. تشغيل التطبيق:
```
streamlit run db_dashboard.py
```

---

## ملاحظات:
- لا تضف sqlite3 إلى requirements.txt، فهي مدمجة مع بايثون.
- إذا واجهت أي خطأ في الحزم، تأكد من تفعيل البيئة قبل التثبيت.
- لتثبيت بايثون: [python.org](https://www.python.org/downloads/)
