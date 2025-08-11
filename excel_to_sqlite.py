import pandas as pd
import sqlite3

# تحميل بيانات Sheet16 فقط
file_path = 'التعثر - Copy.xlsx'
df = pd.read_excel(file_path, sheet_name='Sheet16')

# إنشاء قاعدة بيانات SQLite
conn = sqlite3.connect('students_failures.db')
cursor = conn.cursor()

# حذف جدول الطلاب إذا كان موجودًا ثم إعادة إنشائه بالعمود الصحيح
tables = ['failures', 'students', 'subjects', 'stages', 'tracks', 'study_systems', 'terms', 'years']
for t in tables:
    cursor.execute(f'DROP TABLE IF EXISTS {t}')

# إنشاء الجداول بشكل منظم (تطبيع)
cursor.execute('''
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    national_id TEXT,
    UNIQUE(name, national_id)
)
''')
cursor.execute('''
CREATE TABLE stages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
''')
cursor.execute('''
CREATE TABLE tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
''')
cursor.execute('''
CREATE TABLE study_systems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
''')
cursor.execute('''
CREATE TABLE terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
''')
cursor.execute('''
CREATE TABLE years (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
''')
cursor.execute('''
CREATE TABLE subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
''')
cursor.execute('''
CREATE TABLE failures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    subject_id INTEGER,
    stage_id INTEGER,
    track_id INTEGER,
    study_system_id INTEGER,
    term_id INTEGER,
    year_id INTEGER,
    m_value TEXT,
    FOREIGN KEY(student_id) REFERENCES students(id),
    FOREIGN KEY(subject_id) REFERENCES subjects(id),
    FOREIGN KEY(stage_id) REFERENCES stages(id),
    FOREIGN KEY(track_id) REFERENCES tracks(id),
    FOREIGN KEY(study_system_id) REFERENCES study_systems(id),
    FOREIGN KEY(term_id) REFERENCES terms(id),
    FOREIGN KEY(year_id) REFERENCES years(id)
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS stages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS study_systems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS years (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS failures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    subject_id INTEGER,
    stage_id INTEGER,
    track_id INTEGER,
    study_system_id INTEGER,
    term_id INTEGER,
    year_id INTEGER,
    m_value TEXT,
    FOREIGN KEY(student_id) REFERENCES students(id),
    FOREIGN KEY(subject_id) REFERENCES subjects(id),
    FOREIGN KEY(stage_id) REFERENCES stages(id),
    FOREIGN KEY(track_id) REFERENCES tracks(id),
    FOREIGN KEY(study_system_id) REFERENCES study_systems(id),
    FOREIGN KEY(term_id) REFERENCES terms(id),
    FOREIGN KEY(year_id) REFERENCES years(id)
)
''')

# إدخال البيانات بشكل منظم
for _, row in df.iterrows():
    # الطلاب
    cursor.execute('INSERT OR IGNORE INTO students (name, national_id) VALUES (?, ?)', (row['اسم الطالب'], str(row['رقم الهوية'])))
    cursor.execute('SELECT id FROM students WHERE name=? AND national_id=?', (row['اسم الطالب'], str(row['رقم الهوية'])))
    student_id = cursor.fetchone()[0]
    # المواد
    cursor.execute('INSERT OR IGNORE INTO subjects (name) VALUES (?)', (row['مادة التعثر'],))
    cursor.execute('SELECT id FROM subjects WHERE name=?', (row['مادة التعثر'],))
    subject_id = cursor.fetchone()[0]
    # المرحلة
    cursor.execute('INSERT OR IGNORE INTO stages (name) VALUES (?)', (row['المرحلة'],))
    cursor.execute('SELECT id FROM stages WHERE name=?', (row['المرحلة'],))
    stage_id = cursor.fetchone()[0]
    # المسار
    cursor.execute('INSERT OR IGNORE INTO tracks (name) VALUES (?)', (row['المسار'],))
    cursor.execute('SELECT id FROM tracks WHERE name=?', (row['المسار'],))
    track_id = cursor.fetchone()[0]
    # النظام الدراسي
    cursor.execute('INSERT OR IGNORE INTO study_systems (name) VALUES (?)', (row['النظام الدراسي'],))
    cursor.execute('SELECT id FROM study_systems WHERE name=?', (row['النظام الدراسي'],))
    study_system_id = cursor.fetchone()[0]
    # الفصل الدراسي
    cursor.execute('INSERT OR IGNORE INTO terms (name) VALUES (?)', (row['الفصل الدراسي'],))
    cursor.execute('SELECT id FROM terms WHERE name=?', (row['الفصل الدراسي'],))
    term_id = cursor.fetchone()[0]
    # العام الدراسي
    cursor.execute('INSERT OR IGNORE INTO years (name) VALUES (?)', (row['العام الدراسي'],))
    cursor.execute('SELECT id FROM years WHERE name=?', (row['العام الدراسي'],))
    year_id = cursor.fetchone()[0]
    # سجل التعثر
    cursor.execute('''
        INSERT INTO failures (student_id, subject_id, stage_id, track_id, study_system_id, term_id, year_id, m_value)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (student_id, subject_id, stage_id, track_id, study_system_id, term_id, year_id, str(row['م'])))

conn.commit()
conn.close()
print('تم إنشاء قاعدة البيانات وتطبيعها بنجاح.')
