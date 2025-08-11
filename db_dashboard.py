import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="تقارير الطلاب المتعثرين", layout="wide")
# إنشاء جدول للعناوين المخصصة إذا لم يكن موجودًا
def init_titles_table():
    conn_titles = sqlite3.connect('students_failures.db')
    c = conn_titles.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS report_titles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL
    )''')
    conn_titles.commit()
    conn_titles.close()
init_titles_table()

# دعم اتجاه النص من اليمين لليسار (RTL)
st.markdown(
    '''<style>
    body, .stApp, .css-1d391kg, .css-1v0mbdj, .css-1c7y2kd, .css-1lcbmhc {
        direction: rtl;
        text-align: right;
        font-family: "Cairo", "Tahoma", "Arial", sans-serif;
    }
    </style>''', unsafe_allow_html=True
)
st.title("واجهة تقارير الطلاب المتعثرين")

# الاتصال بقاعدة البيانات
conn = sqlite3.connect('students_failures.db')

# استعلام مخصص
st.subheader("استعلام SQL مخصص")
query = st.text_area("اكتب استعلام SQL هنا", "SELECT * FROM failures LIMIT 10")
if st.button("تنفيذ الاستعلام"):
    try:
        df = pd.read_sql_query(query, conn)
        st.dataframe(df)
    except (sqlite3.DatabaseError, pd.errors.DatabaseError, ValueError, TypeError) as e:
        st.error(f"خطأ في الاستعلام أو البيانات: {e}")

# تقارير جاهزة
st.subheader("تقارير جاهزة")
report_type = st.selectbox("اختر التقرير", [
    "عدد واسماء الطلاب الراسبين في مادة لكل مرحلة لكل فصل دراسي لكل عام",
    "عدد الطلاب الراسبين في كل مادة لكل مرحلة لكل فصل دراسي لكل عام",
    "عدد الطلاب الراسبين في كل مادة",
    "عدد الطلاب الراسبين في كل مرحلة",
    "عدد الطلاب الراسبين في كل فصل دراسي",
    "عدد الطلاب الراسبين في كل عام دراسي",
    "قائمة الطلاب المتعثرين مع التفاصيل"
])

if report_type == "عدد الطلاب الراسبين في كل مادة لكل مرحلة لكل فصل دراسي لكل عام":
    query = '''
    SELECT y.name AS العام, t.name AS الفصل, s.name AS المرحلة, sub.name AS المادة, COUNT(DISTINCT f.student_id) AS عدد_الطلاب_الراسبين
    FROM failures f
    JOIN years y ON f.year_id = y.id
    JOIN terms t ON f.term_id = t.id
    JOIN stages s ON f.stage_id = s.id
    JOIN subjects sub ON f.subject_id = sub.id
    GROUP BY y.name, t.name, s.name, sub.name
    ORDER BY y.name, t.name, s.name, sub.name
    '''
    df = pd.read_sql_query(query, conn)
    st.dataframe(df)
    # زر تحميل التقرير كـ PDF
    import io, datetime
    with st.spinner("جاري تجهيز تقرير PDF..."):
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfbase import pdfmetrics
        import arabic_reshaper
        from bidi.algorithm import get_display
        pdf_buffer = io.BytesIO()
        try:
            pdfmetrics.registerFont(TTFont('Amiri-Regular', 'Amiri/Amiri-Regular.ttf'))
            pdfmetrics.registerFont(TTFont('Amiri-Bold', 'Amiri/Amiri-Bold.ttf'))
            font_name = 'Amiri-Regular'
            font_bold = 'Amiri-Bold'
        except (FileNotFoundError, OSError):
            font_name = 'Helvetica'
            font_bold = 'Helvetica-Bold'
        page_size = A4
        def ar_text(text):
            try:
                reshaped = arabic_reshaper.reshape(str(text))
                return get_display(reshaped)
            except (TypeError, ValueError):
                return str(text)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='ArabicTitle', fontName=font_bold, fontSize=14, alignment=1, spaceAfter=8))
        styles.add(ParagraphStyle(name='Arabic', fontName=font_name, fontSize=12, alignment=1))
        elements = []
        today_str = datetime.datetime.now().strftime('%Y-%m-%d')
        elements.append(Paragraph(ar_text('تقرير إحصائي: عدد الطلاب الراسبين في كل مادة لكل مرحلة لكل فصل دراسي لكل عام'), styles['ArabicTitle']))
        elements.append(Paragraph(ar_text('تاريخ التقرير: ' + today_str), styles['Arabic']))
        elements.append(Spacer(1, 12))
        data_table = [ [ar_text(col) for col in df.columns] ]
        for _, row in df.iterrows():
            data_table.append([ar_text(str(val)) for val in row])
        table = Table(data_table, repeatRows=1)
        style_list = [
            ('FONTNAME', (0,0), (-1,0), font_bold),
            ('FONTNAME', (0,1), (-1,-1), font_name),
            ('FONTSIZE', (0,0), (-1,-1), 11),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ]
        table.setStyle(TableStyle(style_list))
        elements.append(table)
        doc = SimpleDocTemplate(pdf_buffer, pagesize=page_size, rightMargin=20, leftMargin=20, topMargin=60, bottomMargin=30)
        doc.build(elements)
        st.download_button(
            label="تحميل التقرير كـ PDF للطباعة (إحصائي)",
            data=pdf_buffer.getvalue(),
            file_name="stat_report.pdf",
            mime="application/pdf"
        )
# (Removed duplicate block for "عدد واسماء الطلاب الراسبين في مادة لكل مرحلة لكل فصل دراسي لكل عام")
elif report_type == "عدد الطلاب الراسبين في كل مادة":
    query = '''
    SELECT sub.name AS المادة, COUNT(DISTINCT f.student_id) AS عدد_الطلاب_الراسبين
    FROM failures f
    JOIN subjects sub ON f.subject_id = sub.id
    GROUP BY sub.name
    ORDER BY عدد_الطلاب_الراسبين DESC
    '''
    df = pd.read_sql_query(query, conn)
    st.dataframe(df)
    # زر تحميل التقرير كـ PDF
    import io, datetime
    with st.spinner("جاري تجهيز تقرير PDF..."):
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfbase import pdfmetrics
        import arabic_reshaper
        from bidi.algorithm import get_display
        pdf_buffer = io.BytesIO()
        try:
            pdfmetrics.registerFont(TTFont('Amiri-Regular', 'Amiri/Amiri-Regular.ttf'))
            pdfmetrics.registerFont(TTFont('Amiri-Bold', 'Amiri/Amiri-Bold.ttf'))
            font_name = 'Amiri-Regular'
            font_bold = 'Amiri-Bold'
        except Exception:
            font_name = 'Helvetica'
            font_bold = 'Helvetica-Bold'
        page_size = A4
        def ar_text(text):
            try:
                reshaped = arabic_reshaper.reshape(str(text))
                return get_display(reshaped)
            except Exception:
                return str(text)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='ArabicTitle', fontName=font_bold, fontSize=14, alignment=1, spaceAfter=8))
        styles.add(ParagraphStyle(name='Arabic', fontName=font_name, fontSize=12, alignment=1))
        elements = []
        today_str = datetime.datetime.now().strftime('%Y-%m-%d')
        elements.append(Paragraph(ar_text(f'تقرير إحصائي: عدد الطلاب الراسبين في كل مادة'), styles['ArabicTitle']))
        elements.append(Paragraph(ar_text(f'تاريخ التقرير: {today_str}'), styles['Arabic']))
        elements.append(Spacer(1, 12))
        data_table = [ [ar_text(col) for col in df.columns] ]
        for _, row in df.iterrows():
            data_table.append([ar_text(str(val)) for val in row])
        table = Table(data_table, repeatRows=1)
        style_list = [
            ('FONTNAME', (0,0), (-1,0), font_bold),
            ('FONTNAME', (0,1), (-1,-1), font_name),
            ('FONTSIZE', (0,0), (-1,-1), 11),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ]
        table.setStyle(TableStyle(style_list))
        elements.append(table)
        doc = SimpleDocTemplate(pdf_buffer, pagesize=page_size, rightMargin=20, leftMargin=20, topMargin=60, bottomMargin=30)
        doc.build(elements)
        st.download_button(
            label="تحميل التقرير كـ PDF للطباعة (إحصائي)",
            data=pdf_buffer.getvalue(),
            file_name="stat_report.pdf",
            mime="application/pdf"
        )
elif report_type == "عدد الطلاب الراسبين في كل مرحلة":
    query = '''
    SELECT s.name AS المرحلة, COUNT(DISTINCT f.student_id) AS عدد_الطلاب_الراسبين
    FROM failures f
    JOIN stages s ON f.stage_id = s.id
    GROUP BY s.name
    ORDER BY عدد_الطلاب_الراسبين DESC
    '''
    df = pd.read_sql_query(query, conn)
    st.dataframe(df)
    # زر تحميل التقرير كـ PDF
    import io, datetime
    with st.spinner("جاري تجهيز تقرير PDF..."):
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfbase import pdfmetrics
        import arabic_reshaper
        from bidi.algorithm import get_display
        pdf_buffer = io.BytesIO()
        try:
            pdfmetrics.registerFont(TTFont('Amiri-Regular', 'Amiri/Amiri-Regular.ttf'))
            pdfmetrics.registerFont(TTFont('Amiri-Bold', 'Amiri/Amiri-Bold.ttf'))
            font_name = 'Amiri-Regular'
            font_bold = 'Amiri-Bold'
        except Exception:
            font_name = 'Helvetica'
            font_bold = 'Helvetica-Bold'
        page_size = A4
        def ar_text(text):
            try:
                reshaped = arabic_reshaper.reshape(str(text))
                return get_display(reshaped)
            except Exception:
                return str(text)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='ArabicTitle', fontName=font_bold, fontSize=14, alignment=1, spaceAfter=8))
        styles.add(ParagraphStyle(name='Arabic', fontName=font_name, fontSize=12, alignment=1))
        elements = []
        today_str = datetime.datetime.now().strftime('%Y-%m-%d')
        elements.append(Paragraph(ar_text(f'تقرير إحصائي: عدد الطلاب الراسبين في كل مرحلة'), styles['ArabicTitle']))
        elements.append(Paragraph(ar_text(f'تاريخ التقرير: {today_str}'), styles['Arabic']))
        elements.append(Spacer(1, 12))
        data_table = [ [ar_text(col) for col in df.columns] ]
        for _, row in df.iterrows():
            data_table.append([ar_text(str(val)) for val in row])
        table = Table(data_table, repeatRows=1)
        style_list = [
            ('FONTNAME', (0,0), (-1,0), font_bold),
            ('FONTNAME', (0,1), (-1,-1), font_name),
            ('FONTSIZE', (0,0), (-1,-1), 11),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ]
        table.setStyle(TableStyle(style_list))
        elements.append(table)
        doc = SimpleDocTemplate(pdf_buffer, pagesize=page_size, rightMargin=20, leftMargin=20, topMargin=60, bottomMargin=30)
        doc.build(elements)
        st.download_button(
            label="تحميل التقرير كـ PDF للطباعة (إحصائي)",
            data=pdf_buffer.getvalue(),
            file_name="stat_report.pdf",
            mime="application/pdf"
        )
elif report_type == "عدد الطلاب الراسبين في كل فصل دراسي":
    query = '''
    SELECT t.name AS الفصل, COUNT(DISTINCT f.student_id) AS عدد_الطلاب_الراسبين
    FROM failures f
    JOIN terms t ON f.term_id = t.id
    GROUP BY t.name
    ORDER BY عدد_الطلاب_الراسبين DESC
    '''
    df = pd.read_sql_query(query, conn)
    st.dataframe(df)
    # زر تحميل التقرير كـ PDF
    import io, datetime
    with st.spinner("جاري تجهيز تقرير PDF..."):
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfbase import pdfmetrics
        import arabic_reshaper
        from bidi.algorithm import get_display
        pdf_buffer = io.BytesIO()
        try:
            pdfmetrics.registerFont(TTFont('Amiri-Regular', 'Amiri/Amiri-Regular.ttf'))
            pdfmetrics.registerFont(TTFont('Amiri-Bold', 'Amiri/Amiri-Bold.ttf'))
            font_name = 'Amiri-Regular'
            font_bold = 'Amiri-Bold'
        except Exception:
            font_name = 'Helvetica'
            font_bold = 'Helvetica-Bold'
        page_size = A4
        def ar_text(text):
            try:
                reshaped = arabic_reshaper.reshape(str(text))
                return get_display(reshaped)
            except Exception:
                return str(text)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='ArabicTitle', fontName=font_bold, fontSize=14, alignment=1, spaceAfter=8))
        styles.add(ParagraphStyle(name='Arabic', fontName=font_name, fontSize=12, alignment=1))
        elements = []
        today_str = datetime.datetime.now().strftime('%Y-%m-%d')
        elements.append(Paragraph(ar_text(f'تقرير إحصائي: عدد الطلاب الراسبين في كل فصل دراسي'), styles['ArabicTitle']))
        elements.append(Paragraph(ar_text(f'تاريخ التقرير: {today_str}'), styles['Arabic']))
        elements.append(Spacer(1, 12))
        data_table = [ [ar_text(col) for col in df.columns] ]
        for _, row in df.iterrows():
            data_table.append([ar_text(str(val)) for val in row])
        table = Table(data_table, repeatRows=1)
        style_list = [
            ('FONTNAME', (0,0), (-1,0), font_bold),
            ('FONTNAME', (0,1), (-1,-1), font_name),
            ('FONTSIZE', (0,0), (-1,-1), 11),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ]
        table.setStyle(TableStyle(style_list))
        elements.append(table)
        doc = SimpleDocTemplate(pdf_buffer, pagesize=page_size, rightMargin=20, leftMargin=20, topMargin=60, bottomMargin=30)
        doc.build(elements)
        st.download_button(
            label="تحميل التقرير كـ PDF للطباعة (إحصائي)",
            data=pdf_buffer.getvalue(),
            file_name="stat_report.pdf",
            mime="application/pdf"
        )
elif report_type == "عدد الطلاب الراسبين في كل عام دراسي":
    query = '''
    SELECT y.name AS العام, COUNT(DISTINCT f.student_id) AS عدد_الطلاب_الراسبين
    FROM failures f
    JOIN years y ON f.year_id = y.id
    GROUP BY y.name
    ORDER BY عدد_الطلاب_الراسبين DESC
    '''
    df = pd.read_sql_query(query, conn)
    st.dataframe(df)
    # زر تحميل التقرير كـ PDF
    import io, datetime
    with st.spinner("جاري تجهيز تقرير PDF..."):
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfbase import pdfmetrics
        import arabic_reshaper
        from bidi.algorithm import get_display
        pdf_buffer = io.BytesIO()
        try:
            pdfmetrics.registerFont(TTFont('Amiri-Regular', 'Amiri/Amiri-Regular.ttf'))
            pdfmetrics.registerFont(TTFont('Amiri-Bold', 'Amiri/Amiri-Bold.ttf'))
            font_name = 'Amiri-Regular'
            font_bold = 'Amiri-Bold'
        except Exception:
            font_name = 'Helvetica'
            font_bold = 'Helvetica-Bold'
        page_size = A4
        def ar_text(text):
            try:
                reshaped = arabic_reshaper.reshape(str(text))
                return get_display(reshaped)
            except Exception:
                return str(text)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='ArabicTitle', fontName=font_bold, fontSize=14, alignment=1, spaceAfter=8))
        styles.add(ParagraphStyle(name='Arabic', fontName=font_name, fontSize=12, alignment=1))
        elements = []
        today_str = datetime.datetime.now().strftime('%Y-%m-%d')
        elements.append(Paragraph(ar_text(f'تقرير إحصائي: عدد الطلاب الراسبين في كل عام دراسي'), styles['ArabicTitle']))
        elements.append(Paragraph(ar_text(f'تاريخ التقرير: {today_str}'), styles['Arabic']))
        elements.append(Spacer(1, 12))
        data_table = [ [ar_text(col) for col in df.columns] ]
        for _, row in df.iterrows():
            data_table.append([ar_text(str(val)) for val in row])
        table = Table(data_table, repeatRows=1)
        style_list = [
            ('FONTNAME', (0,0), (-1,0), font_bold),
            ('FONTNAME', (0,1), (-1,-1), font_name),
            ('FONTSIZE', (0,0), (-1,-1), 11),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ]
        table.setStyle(TableStyle(style_list))
        elements.append(table)
        doc = SimpleDocTemplate(pdf_buffer, pagesize=page_size, rightMargin=20, leftMargin=20, topMargin=60, bottomMargin=30)
        doc.build(elements)
        st.download_button(
            label="تحميل التقرير كـ PDF للطباعة (إحصائي)",
            data=pdf_buffer.getvalue(),
            file_name="stat_report.pdf",
            mime="application/pdf"
        )

elif report_type == "عدد واسماء الطلاب الراسبين في مادة لكل مرحلة لكل فصل دراسي لكل عام":
    # إدارة العناوين المخصصة
    if 'titles_list' not in st.session_state:
        conn_titles = sqlite3.connect('students_failures.db')
        c_titles = conn_titles.cursor()
        c_titles.execute("SELECT id, title FROM report_titles")
        st.session_state['titles_list'] = [row[1] for row in c_titles.fetchall()]
        conn_titles.close()

    st.subheader("عنوان التقرير المخصص")
    col_title1, col_title2, col_title3 = st.columns([2,4,0.7])
    with col_title1:
        selected_title = st.selectbox("اختر عنوان التقرير للطباعة", st.session_state['titles_list'] if st.session_state['titles_list'] else ["تقرير الطلاب الراسبين (قابل للطباعة)"])
    with col_title2:
        new_title = st.text_input("أضف عنوان جديد للتقرير", label_visibility="collapsed", placeholder="أضف عنوان جديد للتقرير")
    with col_title3:
        add_title_clicked = st.button("إضافة العنوان", use_container_width=True)
    if add_title_clicked and new_title.strip():
        conn_titles = sqlite3.connect('students_failures.db')
        c_titles = conn_titles.cursor()
        c_titles.execute("INSERT INTO report_titles (title) VALUES (?)", (new_title.strip(),))
        conn_titles.commit()
        # تحديث القائمة فوراً
        c_titles.execute("SELECT id, title FROM report_titles")
        st.session_state['titles_list'] = [row[1] for row in c_titles.fetchall()]
        conn_titles.close()
        st.success("تمت إضافة العنوان بنجاح!")
    # جلب القيم الفريدة لعناصر التصفية
    المواد = pd.read_sql_query('SELECT DISTINCT name FROM subjects', conn)['name'].tolist()
    المراحل = pd.read_sql_query('SELECT DISTINCT name FROM stages', conn)['name'].tolist()
    الفصول = pd.read_sql_query('SELECT DISTINCT name FROM terms', conn)['name'].tolist()
    الاعوام = pd.read_sql_query('SELECT DISTINCT name FROM years', conn)['name'].tolist()
    # لا حاجة لجلب قائمة الأرقام، سنستخدم إدخال نصي

    col_id, col1, col2, col3, col4 = st.columns(5)
    with col_id:
        رقم_الهوية_مدخل = st.text_input('رقم الهوية (اختياري)')
        نوع_مطابقة_الهوية = st.radio('مطابقة رقم الهوية', ['مطابق تماماً', 'مطابقة جزئية'], horizontal=True)
    with col1:
        المادة = st.selectbox('اختر المادة', ['كل المواد'] + المواد)
    with col2:
        المرحلة = st.selectbox('اختر المرحلة', ['كل المراحل'] + المراحل)
    with col3:
        الفصل = st.selectbox('اختر الفصل الدراسي', ['كل الفصول'] + الفصول)
    with col4:
        العام = st.selectbox('اختر العام الدراسي', ['كل الأعوام'] + الاعوام)

    # بناء شروط التصفية
    filters = []
    اسم_الطالب_مفلتر = None
    اخفاء_عمود_الاسم = False
    if رقم_الهوية_مدخل.strip():
        if نوع_مطابقة_الهوية == 'مطابق تماماً':
            filters.append(f"stu.national_id = '{رقم_الهوية_مدخل.strip()}'")
        else:
            filters.append(f"stu.national_id LIKE '%{رقم_الهوية_مدخل.strip()}%'")
        # جلب اسم الطالب إذا كان الفلترة برقم الهوية فقط
        query_name = f"""
        SELECT stu.name FROM failures f
        JOIN students stu ON f.student_id = stu.id
        WHERE stu.national_id = '{رقم_الهوية_مدخل.strip()}'
        LIMIT 1
        """
        try:
            df_name = pd.read_sql_query(query_name, conn)
            if not df_name.empty:
                اسم_الطالب_مفلتر = df_name.iloc[0,0]
                اخفاء_عمود_الاسم = True
        except Exception:
            اسم_الطالب_مفلتر = None
    if المادة != 'كل المواد':
        filters.append(f"sub.name = '{المادة}'")
    if المرحلة != 'كل المراحل':
        filters.append(f"s.name = '{المرحلة}'")
    if الفصل != 'كل الفصول':
        filters.append(f"t.name = '{الفصل}'")
    if العام != 'كل الأعوام':
        filters.append(f"y.name = '{العام}'")
    where_clause = ''
    if filters:
        where_clause = 'WHERE ' + ' AND '.join(filters)
    else:
        where_clause = ''

    query = f'''
    SELECT 
        y.name AS العام,
        t.name AS الفصل,
        s.name AS المرحلة,
        sub.name AS المادة,
        stu.name AS اسم_الطالب,
        stu.national_id AS رقم_الهوية
    FROM failures f
    JOIN years y ON f.year_id = y.id
    JOIN terms t ON f.term_id = t.id
    JOIN stages s ON f.stage_id = s.id
    JOIN subjects sub ON f.subject_id = sub.id
    JOIN students stu ON f.student_id = stu.id
    {where_clause}
    ORDER BY y.name, t.name, s.name, sub.name, stu.name
    '''
    df = pd.read_sql_query(query, conn)
    st.markdown(f"<h4 style='color:#1976d2;text-align:right;'>عدد الصفوف المفلترة: <span style='color:#d32f2f;'>{len(df)}</span></h4>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True)
    # زر تحميل التقرير كـ Excel
    import io
    with st.spinner("جاري تجهيز تقرير Excel..."):
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        st.download_button(
            label="تحميل التقرير كـ Excel",
            data=excel_buffer.getvalue(),
            file_name="filtered_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # زر تحميل التقرير كـ PDF
    col_pdf1, col_pdf2, col_pdf3 = st.columns([3,1,1])
    with col_pdf3:
        hide_seq_col = st.checkbox("إخفاء عمود التسلسل", value=False)
    with col_pdf2:
        page_orientation = st.radio("اتجاه الصفحة", ["عمودي (A4)", "عرضي (A4 Landscape)"], horizontal=True)
    with col_pdf1:
        import io
        with st.spinner("جاري تجهيز تقرير PDF..."):
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.pdfbase import pdfmetrics
            import arabic_reshaper
            from bidi.algorithm import get_display
            pdf_buffer = io.BytesIO()
            # تسجيل الخط العربي (Amiri فقط)
            try:
                pdfmetrics.registerFont(TTFont('Amiri-Regular', 'Amiri/Amiri-Regular.ttf'))
                pdfmetrics.registerFont(TTFont('Amiri-Bold', 'Amiri/Amiri-Bold.ttf'))
                font_name = 'Amiri-Regular'
                font_bold = 'Amiri-Bold'
            except Exception:
                font_name = 'Helvetica'
                font_bold = 'Helvetica-Bold'
            # تحديد حجم الصفحة حسب اختيار المستخدم
            if page_orientation == "عرضي (A4 Landscape)":
                page_size = landscape(A4)
            else:
                page_size = A4
            # إعداد دالة رأس الصفحة
            def draw_header(canvas, doc):
                canvas.saveState()
                # إعداد الخط
                canvas.setFont(font_bold, 14)
                today_str = datetime.datetime.now().strftime('%Y-%m-%d')
                # التاريخ يسار
                canvas.drawRightString(doc.pagesize[0]-20, doc.pagesize[1]-30, ar_text(f'التاريخ: {today_str}'))
                # اسم الطالب تحت التاريخ إذا تمت الفلترة برقم الهوية فقط
                if اسم_الطالب_مفلتر:
                    canvas.drawRightString(doc.pagesize[0]-20, doc.pagesize[1]-50, ar_text(f'اسم الطالب: {اسم_الطالب_مفلتر}'))
                # العنوان وسط
                canvas.drawCentredString(doc.pagesize[0]/2, doc.pagesize[1]-30, ar_text(selected_title))
                # عدد الطلاب يمين (بدون تكرار)
                unique_students = df['رقم_الهوية'].nunique() if 'رقم_الهوية' in df.columns else len(df)
                canvas.drawString(20, doc.pagesize[1]-30, ar_text(f'عدد الطلاب (بدون تكرار): {unique_students}'))
                # عدد مواد الرسوب (عدد الصفوف)
                canvas.drawString(20, doc.pagesize[1]-50, ar_text(f'عدد مواد الرسوب: {len(df)}'))
                # الفلاتر تحت العنوان
                filter_labels = []
                if المادة != 'كل المواد':
                    filter_labels.append(f'المادة: {المادة}')
                if المرحلة != 'كل المراحل':
                    filter_labels.append(f'المرحلة: {المرحلة}')
                if الفصل != 'كل الفصول':
                    filter_labels.append(f'الفصل: {الفصل}')
                if العام != 'كل الأعوام':
                    filter_labels.append(f'العام: {العام}')
                if filter_labels:
                    filters_text = ' | '.join(filter_labels)
                    canvas.setFont(font_name, 12)
                    canvas.drawString(20, doc.pagesize[1]-70, ar_text(filters_text))
                canvas.restoreState()

            # إعداد دالة ذيل الصفحة
            def draw_footer(canvas, doc):
                canvas.saveState()
                canvas.setFont(font_name, 11)
                page_num = canvas.getPageNumber()
                # رقم الصفحة يسار، عدد الصفحات يمين
                canvas.drawString(20, 15, ar_text(f'صفحة {page_num} من {{}}'))
                canvas.restoreState()

            import datetime
            doc = SimpleDocTemplate(pdf_buffer, pagesize=page_size, rightMargin=20, leftMargin=20, topMargin=60, bottomMargin=30)
        elements = []
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='ArabicTitle', fontName=font_bold, fontSize=14, alignment=1, rightIndent=0, leftIndent=0, spaceAfter=8))
        styles.add(ParagraphStyle(name='Arabic', fontName=font_name, fontSize=12, alignment=1, rightIndent=0, leftIndent=0))
        styles.add(ParagraphStyle(name='LeftArabic', fontName=font_name, fontSize=12, alignment=0, rightIndent=0, leftIndent=0))
        def ar_text(text):
            try:
                reshaped = arabic_reshaper.reshape(str(text))
                return get_display(reshaped)
            except Exception:
                return str(text)
        # إعداد الجدول
        base_cols = list(df.columns)
        filter_cols = []
        if المادة != 'كل المواد':
            filter_cols.append('المادة')
        if المرحلة != 'كل المراحل':
            filter_cols.append('المرحلة')
        if الفصل != 'كل الفصول':
            filter_cols.append('الفصل')
        if العام != 'كل الأعوام':
            filter_cols.append('العام')
        # إضافة عمود الدرجة
        if 'الدرجة' not in base_cols:
            base_cols.append('الدرجة')
        # ترتيب الأعمدة: الدرجة في أقصى اليمين
        col_order = ['الدرجة', 'التسلسل', 'اسم_الطالب', 'المادة', 'المرحلة', 'الفصل', 'العام', 'التوقيع']
        # إخفاء أعمدة الفلاتر
        visible_cols = [col for col in col_order if col not in filter_cols]
        # إخفاء عمود اسم الطالب إذا تمت الفلترة برقم الهوية فقط
        if اخفاء_عمود_الاسم and 'اسم_الطالب' in visible_cols:
            visible_cols.remove('اسم_الطالب')
        # إخفاء عمود التسلسل إذا تم اختيار ذلك
        if hide_seq_col and 'التسلسل' in visible_cols:
            visible_cols.remove('التسلسل')
        if len(df) == 0:
            elements.append(Spacer(1, 24))
            elements.append(Paragraph(ar_text('لا توجد بيانات مطابقة للفلاتر المختارة.'), styles['Arabic']))
        else:
            data_table = [ [ar_text(col) for col in visible_cols] ]
            for idx, row in enumerate(df.iterrows(), 1):
                _, row_data = row
                row_dict = row_data.to_dict()
                row_list = []
                for col in visible_cols:
                    if col == 'التسلسل':
                        row_list.append(str(idx))
                    elif col == 'التوقيع':
                        row_list.append('')
                    elif col == 'الدرجة':
                        row_list.append(row_dict.get('الدرجة', ''))
                    elif col == 'المرحلة':
                        val = row_dict.get('المرحلة', '')
                        if 'الأول' in val:
                            row_list.append('1')
                        elif 'الثاني' in val:
                            row_list.append('2')
                        elif 'الثالث' in val:
                            row_list.append('3')
                        else:
                            row_list.append('')
                    elif col == 'الفصل':
                        val = row_dict.get('الفصل', '')
                        if 'الأول' in val:
                            row_list.append('1')
                        elif 'الثاني' in val:
                            row_list.append('2')
                        elif 'الثالث' in val:
                            row_list.append('3')
                        else:
                            row_list.append('')
                    else:
                        row_list.append(ar_text(row_dict.get(col, '')))
                data_table.append(row_list)
            data_table = [row[::-1] for row in data_table]
            col_names_final = visible_cols
            from reportlab.pdfbase.pdfmetrics import stringWidth
            from reportlab.lib.pagesizes import A4
            font_size = 12
            font_used = font_name
            num_cols = len(col_names_final)
            raw_widths = []
            for col_idx, col in enumerate(col_names_final):
                col_values = [str(data_table[row_idx][col_idx]) for row_idx in range(len(data_table))]
                max_text = max(col_values, key=len)
                width = stringWidth(max_text, font_used, font_size) + 20
                raw_widths.append(max(50, min(width, 220)))
            from reportlab.lib.pagesizes import A4, landscape
            if page_orientation == "عرضي (A4 Landscape)":
                PAGE_WIDTH = landscape(A4)[0] - 20 - 20
            else:
                PAGE_WIDTH = A4[0] - 20 - 20
            total_raw = sum(raw_widths)
            if total_raw > 0:
                col_widths = [w * PAGE_WIDTH / total_raw for w in raw_widths]
            else:
                col_widths = [PAGE_WIDTH / num_cols] * num_cols
            row_height = 30
            row_heights = [row_height] * len(data_table)
            # تكرار رأس الجدول في كل صفحة
            table = Table(data_table, colWidths=col_widths, rowHeights=row_heights, repeatRows=1)
            # تحديد رقم عمود الاسم بعد العكس (RTL)
            if 'اسم_الطالب' in col_names_final:
                name_col_idx = col_names_final[::-1].index('اسم_الطالب')
            else:
                name_col_idx = None
            style_list = [
                ('FONTNAME', (0,0), (-1,0), font_bold),
                ('FONTNAME', (0,1), (-1,-1), font_name),
                ('FONTSIZE', (0,0), (-1,-1), 11),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ]
            if name_col_idx is not None:
                style_list.append(('ALIGN', (name_col_idx,0), (name_col_idx,-1), 'RIGHT'))
            for i in range(num_cols):
                style_list.append(('WORDWRAP', (i,0), (i,-1), 'CJK'))
            table.setStyle(TableStyle(style_list))
            elements.append(table)
        # حساب عدد الصفحات
        def count_pages():
            temp_buffer = io.BytesIO()
            temp_doc = SimpleDocTemplate(temp_buffer, pagesize=page_size, rightMargin=20, leftMargin=20, topMargin=60, bottomMargin=30)
            # إعادة بناء عناصر الجدول فقط (بدون نصوص أو فواصل)
            temp_elements = []
            temp_table = Table(data_table, colWidths=col_widths, rowHeights=row_heights, repeatRows=1)
            temp_table.setStyle(TableStyle(style_list))
            temp_elements.append(temp_table)
            temp_doc.build(temp_elements, onFirstPage=lambda c, d: None, onLaterPages=lambda c, d: None)
            from PyPDF2 import PdfReader
            temp_buffer.seek(0)
            reader = PdfReader(temp_buffer)
            return len(reader.pages)
        try:
            from PyPDF2 import PdfReader
            total_pages = count_pages()
        except Exception:
            total_pages = None
        # تحديث دالة ذيل الصفحة لإظهار عدد الصفحات
        def draw_footer_with_total(canvas, doc):
            canvas.saveState()
            try:
                canvas.setFont('Amiri-Regular', 11)
            except Exception:
                canvas.setFont('Helvetica', 11)
            page_num = canvas.getPageNumber()
            if total_pages:
                canvas.drawString(20, 15, ar_text(f'صفحة {page_num} من {total_pages}'))
            else:
                canvas.drawString(20, 15, ar_text(f'صفحة {page_num}'))
            canvas.restoreState()
        doc.build(elements, onFirstPage=lambda c, d: (draw_header(c, d), draw_footer_with_total(c, d)), onLaterPages=lambda c, d: (draw_header(c, d), draw_footer_with_total(c, d)))
        st.download_button(
            label="تحميل التقرير كـ PDF للطباعة (يدعم العربية)",
            data=pdf_buffer.getvalue(),
            file_name="filtered_report.pdf",
mime="application/pdf"
        )

if report_type == "قائمة الطلاب المتعثرين مع التفاصيل":
    query = '''
    SELECT s.name AS اسم_الطالب, s.national_id AS رقم_الهوية, stg.name AS المرحلة, tr.name AS المسار, sys.name AS النظام_الدراسي, t.name AS الفصل, y.name AS العام, sub.name AS المادة, f.m_value AS م, COUNT(*) OVER (PARTITION BY s.id) AS عدد_مرات_التعثر
    FROM failures f
    JOIN students s ON f.student_id = s.id
    JOIN stages stg ON f.stage_id = stg.id
    JOIN tracks tr ON f.track_id = tr.id
    JOIN study_systems sys ON f.study_system_id = sys.id
    JOIN terms t ON f.term_id = t.id
    JOIN years y ON f.year_id = y.id
    JOIN subjects sub ON f.subject_id = sub.id
    ORDER BY s.name, y.name, t.name, sub.name
    '''
    df = pd.read_sql_query(query, conn)
    st.dataframe(df)

conn.close()