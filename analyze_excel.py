# قوائم الطلاب المتعثرين حسب المرحلة والفصل الدراسي والمادة
import pandas as pd
# تحميل بيانات ملف Excel
file_path = 'التعثر - Copy.xlsx'
df = pd.read_excel(file_path, sheet_name='Sheet16')

# إنشاء قائمة بأسماء الطلاب المتعثرين في ملف نصي
if 'اسم الطالب' in df.columns:
    student_list = sorted(set(df['اسم الطالب'].dropna()))
    with open('student_list.txt', 'w', encoding='utf-8') as f:
        for student in student_list:
            f.write(student + '\n')

# مثال: ملخص إحصائي للبيانات

# دمج جميع التقارير في ملف Excel واحد
with pd.ExcelWriter('all_reports.xlsx', engine='openpyxl') as writer:
    # ملخص إحصائي
    summary = df.describe(include='all')
    # إحصائية بعدد الطلاب الراسبين في كل مادة لكل مرحلة لكل فصل دراسي لكل عام
    if {'اسم الطالب', 'المادة', 'المرحلة', 'الفصل', 'السنة'}.issubset(df.columns):
        fail_stats = df.groupby(['السنة', 'الفصل', 'المرحلة', 'المادة'])['اسم الطالب'].nunique().reset_index()
        fail_stats.rename(columns={'اسم الطالب': 'عدد الطلاب الراسبين'}, inplace=True)
        fail_stats.to_excel(writer, sheet_name='إحصائية الرسوب حسب المادة', index=False)
    summary.to_excel(writer, sheet_name='ملخص إحصائي')

    # توزيع القيم في كل عمود
    for col in df.columns:
        value_counts = df[col].value_counts()
        # إزالة أو استبدال الأحرف غير المسموح بها في اسم الورقة
        safe_col = str(col).replace(':', '-').replace('/', '-').replace('\\', '-').replace('*', '-').replace('?', '-').replace('[', '-').replace(']', '-')
        sheet_name = f'توزيع_{safe_col}'[:31]  # الحد الأقصى لطول اسم الورقة في Excel هو 31 حرفًا
        value_counts.to_excel(writer, sheet_name=sheet_name)

        # قوائم الطلاب المتعثرين حسب المرحلة والفصل الدراسي والمادة
        if {'اسم الطالب', 'المرحلة', 'الفصل', 'المادة'}.issubset(df.columns):
            grouped = df.groupby(['المرحلة', 'الفصل', 'المادة'])['اسم الطالب'].apply(lambda x: ', '.join(sorted(set(x)))).reset_index()
            grouped.columns = ['المرحلة', 'الفصل', 'المادة', 'قائمة الطلاب المتعثرين']
            grouped.to_excel(writer, sheet_name='قوائم الطلاب حسب المرحلة', index=False)

    # تحليلات متقدمة إذا توفرت الأعمدة المطلوبة
    if {'اسم الطالب', 'المادة', 'السنة', 'الفصل'}.issubset(df.columns):
        # الطلاب الأكثر تكرارًا في التعثر
        top_students = df['اسم الطالب'].value_counts().reset_index()
        top_students.columns = ['اسم الطالب', 'عدد مرات التعثر']
        top_students.to_excel(writer, sheet_name='الطلاب الأكثر تعثرًا', index=False)

        # المواد الأكثر تعثرًا لكل طالب
        student_subjects = df.groupby('اسم الطالب')['المادة'].apply(lambda x: x.value_counts().head(3)).reset_index()
        student_subjects.columns = ['اسم الطالب', 'المادة', 'عدد مرات التعثر']
        student_subjects.to_excel(writer, sheet_name='مواد التعثر لكل طالب', index=False)

        # الفصول الأعلى تعثرًا
        top_terms = df['الفصل'].value_counts().reset_index()
        top_terms.columns = ['الفصل', 'عدد حالات التعثر']
        top_terms.to_excel(writer, sheet_name='الفصول الأعلى تعثرًا', index=False)

        # السنوات الأعلى تعثرًا
        top_years = df['السنة'].value_counts().reset_index()
        top_years.columns = ['السنة', 'عدد حالات التعثر']
        top_years.to_excel(writer, sheet_name='السنوات الأعلى تعثرًا', index=False)

        # الطلاب المتعثرين في أكثر من مادة
        multi_subject = df.groupby('اسم الطالب')['المادة'].nunique().reset_index()
        multi_subject = multi_subject[multi_subject['المادة'] > 1]
        multi_subject.columns = ['اسم الطالب', 'عدد المواد المتعثر فيها']
        multi_subject.to_excel(writer, sheet_name='طلاب تعثروا في أكثر من مادة', index=False)

        # الطلاب المتعثرين في أكثر من فصل
        multi_term = df.groupby('اسم الطالب')['الفصل'].nunique().reset_index()
        multi_term = multi_term[multi_term['الفصل'] > 1]
        multi_term.columns = ['اسم الطالب', 'عدد الفصول المتعثر فيها']
        multi_term.to_excel(writer, sheet_name='طلاب تعثروا في أكثر من فصل', index=False)

print('تم إنشاء ملف تقارير واحد بنجاح.')
