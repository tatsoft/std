import sys
import sqlite3
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
import datetime
import openpyxl
from openpyxl.styles import Font as XLFont
import arabic_reshaper
from bidi.algorithm import get_display

DB_PATH = 'students_failures.db'

# Helper for Arabic text
def ar_text(text):
    try:
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except Exception:
        return str(text)

class StudentFailuresApp(QMainWindow):
    def load_filters(self):
        c = self.conn.cursor()
        self.subject_combo.clear()
        self.subject_combo.addItem('كل المواد')
        for row in c.execute('SELECT DISTINCT name FROM subjects'):
            self.subject_combo.addItem(row[0])
        self.stage_combo.clear()
        self.stage_combo.addItem('كل المراحل')
        for row in c.execute('SELECT DISTINCT name FROM stages'):
            self.stage_combo.addItem(row[0])
        self.term_combo.clear()
        self.term_combo.addItem('كل الفصول')
        for row in c.execute('SELECT DISTINCT name FROM terms'):
            self.term_combo.addItem(row[0])
        self.year_combo.clear()
        self.year_combo.addItem('كل الأعوام')
        for row in c.execute('SELECT DISTINCT name FROM years'):
            self.year_combo.addItem(row[0])
    def __init__(self):
        super().__init__()
        self.setWindowTitle('واجهة تقارير الطلاب المتعثرين')
        self.setGeometry(100, 100, 1100, 700)
        # Set global RTL and font
        font = QFont('Cairo', 12)
        self.setFont(font)
        self.setLayoutDirection(Qt.RightToLeft)
        QApplication.instance().setLayoutDirection(Qt.RightToLeft)
        QApplication.instance().setFont(font)
        self.conn = sqlite3.connect(DB_PATH)
        self.init_ui()         # Create widgets first
        self.load_filters()    # Then load filters
        self.load_data()       # Then load data

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        filter_layout = QHBoxLayout()

        font = QFont('Cairo', 12)

        self.national_id_input = QLineEdit()
        self.national_id_input.setPlaceholderText('رقم الهوية (اختياري)')
        self.national_id_input.setFont(font)
        filter_layout.addWidget(self.national_id_input)

        self.subject_combo = QComboBox()
        self.subject_combo.setFont(font)
        lbl_subject = QLabel('المادة:')
        lbl_subject.setFont(font)
        filter_layout.addWidget(lbl_subject)
        filter_layout.addWidget(self.subject_combo)

        self.stage_combo = QComboBox()
        self.stage_combo.setFont(font)
        lbl_stage = QLabel('المرحلة:')
        lbl_stage.setFont(font)
        filter_layout.addWidget(lbl_stage)
        filter_layout.addWidget(self.stage_combo)

        self.term_combo = QComboBox()
        self.term_combo.setFont(font)
        lbl_term = QLabel('الفصل:')
        lbl_term.setFont(font)
        filter_layout.addWidget(lbl_term)
        filter_layout.addWidget(self.term_combo)

        self.year_combo = QComboBox()
        self.year_combo.setFont(font)
        lbl_year = QLabel('العام:')
        lbl_year.setFont(font)
        filter_layout.addWidget(lbl_year)
        filter_layout.addWidget(self.year_combo)

        # Connect filter signals to reload data
        self.subject_combo.currentIndexChanged.connect(self.load_data)
        self.stage_combo.currentIndexChanged.connect(self.load_data)
        self.term_combo.currentIndexChanged.connect(self.load_data)
        self.year_combo.currentIndexChanged.connect(self.load_data)
        self.national_id_input.returnPressed.connect(self.load_data)


        # Add export and customize columns buttons
        export_layout = QHBoxLayout()
        self.btn_export_excel = QPushButton('تصدير إلى Excel')
        self.btn_export_excel.setFont(font)
        self.btn_export_excel.clicked.connect(self.export_excel)
        export_layout.addWidget(self.btn_export_excel)

        self.btn_export_pdf = QPushButton('تصدير إلى PDF')
        self.btn_export_pdf.setFont(font)
        self.btn_export_pdf.clicked.connect(self.export_pdf)
        export_layout.addWidget(self.btn_export_pdf)


        self.btn_customize_columns = QPushButton('تخصيص الأعمدة')
        self.btn_customize_columns.setFont(font)
        self.btn_customize_columns.clicked.connect(self.show_column_customizer)
        export_layout.addWidget(self.btn_customize_columns)

        # Add the table widget and layouts (must be at the end after all variables are defined)
        self.table = QTableWidget()
        self.table.setFont(font)
        self.table.setLayoutDirection(Qt.RightToLeft)
        main_layout.addLayout(filter_layout)
        main_layout.addLayout(export_layout)
        main_layout.addWidget(self.table)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Apply dark theme stylesheet
        dark_stylesheet = """
        QWidget {
            background-color: #232629;
            color: #f0f0f0;
            font-family: 'Cairo';
        }
        QLineEdit, QComboBox, QTableWidget, QTableView {
            background-color: #31363b;
            color: #f0f0f0;
            border: 1px solid #444;
        }
        QHeaderView::section {
            background-color: #1976D2;
            color: white;
            font-weight: bold;
        }
        QPushButton {
            background-color: #1976D2;
            color: white;
            border-radius: 6px;
            padding: 6px 12px;
        }
        QPushButton:hover {
            background-color: #1565c0;
        }
        """
        self.setStyleSheet(dark_stylesheet)

    def show_column_customizer(self):
        if not hasattr(self, 'df') or self.df.empty:
            QMessageBox.warning(self, 'تنبيه', 'لا توجد بيانات لتخصيص الأعمدة.')
            return
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QPushButton, QHBoxLayout
        dialog = QDialog(self)
        dialog.setWindowTitle('تخصيص الأعمدة')
        layout = QVBoxLayout()
        self.column_checkboxes = []
        columns_rtl = list(self.df.columns)[::-1]
        for idx, col in enumerate(columns_rtl):
            cb = QCheckBox(str(col))
            cb.setChecked(not self.table.isColumnHidden(idx))
            cb.setFont(QFont('Cairo', 12))
            layout.addWidget(cb)
            self.column_checkboxes.append((cb, idx))
        btns = QHBoxLayout()
        btn_ok = QPushButton('موافق')
        btn_ok.setFont(QFont('Cairo', 12))
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel = QPushButton('إلغاء')
        btn_cancel.setFont(QFont('Cairo', 12))
        btn_cancel.clicked.connect(dialog.reject)
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)
        dialog.setLayout(layout)
        if dialog.exec():
            for cb, idx in self.column_checkboxes:
                self.table.setColumnHidden(idx, not cb.isChecked())

    def export_pdf(self):
        if not hasattr(self, 'df') or self.df.empty:
            QMessageBox.warning(self, 'تنبيه', 'لا توجد بيانات للتصدير.')
            return
        path, _ = QFileDialog.getSaveFileName(self, 'حفظ ملف PDF', '', 'PDF Files (*.pdf)')
        if not path:
            return
        try:
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Flowable
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.pdfbase import pdfmetrics
            from reportlab.lib.utils import ImageReader
            import arabic_reshaper
            from bidi.algorithm import get_display
            import datetime, os
            # Use Amiri font if available
            try:
                pdfmetrics.registerFont(TTFont('Amiri-Regular', 'Amiri/Amiri-Regular.ttf'))
                pdfmetrics.registerFont(TTFont('Amiri-Bold', 'Amiri/Amiri-Bold.ttf'))
                font_name = 'Amiri-Regular'
                font_bold = 'Amiri-Bold'
            except Exception:
                font_name = 'Helvetica'
                font_bold = 'Helvetica-Bold'

            def ar_text(text):
                try:
                    reshaped = arabic_reshaper.reshape(str(text))
                    return get_display(reshaped)
                except Exception:
                    return str(text)

            # Header info
            today_str = datetime.datetime.now().strftime('%Y-%m-%d')
            title = 'تقرير الطلاب المتعثرين'
            filters = []
            if self.subject_combo.currentText() != 'كل المواد':
                filters.append(f'المادة: {self.subject_combo.currentText()}')
            if self.stage_combo.currentText() != 'كل المراحل':
                filters.append(f'المرحلة: {self.stage_combo.currentText()}')
            if self.term_combo.currentText() != 'كل الفصول':
                filters.append(f'الفصل: {self.term_combo.currentText()}')
            if self.year_combo.currentText() != 'كل الأعوام':
                filters.append(f'العام: {self.year_combo.currentText()}')
            filters_text = ' | '.join(filters) if filters else ''
            unique_students = self.df['رقم_الهوية'].nunique() if 'رقم_الهوية' in self.df.columns else len(self.df)
            num_rows = len(self.df)


            # Use fixed column order for PDF export (RTL): رقم_الهوية, اسم_الطالب, المادة, المرحلة, الفصل, العام
            fixed_order = ['رقم_الهوية', 'اسم_الطالب', 'المادة', 'المرحلة', 'الفصل', 'العام']
            columns_rtl = [col for col in fixed_order if col in self.df.columns]
            data_table = []
            # Header row (RTL order)
            data_table.append([ar_text(col) for col in columns_rtl])
            # Data rows (RTL order)
            for _, row in self.df.iterrows():
                row_rtl = [ar_text(row[col]) for col in columns_rtl]
                data_table.append(row_rtl)

            # PDF document
            page_size = A4
            styles = getSampleStyleSheet()
            # alignment=2 is TA_RIGHT, but for RTL we use alignment=2 and wordWrap='RTL'
            # Use direction='rtl' if available (for newer reportlab)
            try:
                styles.add(ParagraphStyle(name='ArabicTitle', fontName=font_bold, fontSize=18, alignment=2, spaceAfter=8, textColor=colors.white, wordWrap='RTL', direction='rtl'))
                styles.add(ParagraphStyle(name='Arabic', fontName=font_name, fontSize=12, alignment=2, wordWrap='RTL', direction='rtl'))
                styles.add(ParagraphStyle(name='Boxed', fontName=font_name, fontSize=12, alignment=2, backColor=colors.whitesmoke, borderPadding=6, borderColor=colors.HexColor('#1976D2'), borderWidth=1, borderRadius=4, wordWrap='RTL', leading=18, rightIndent=0, leftIndent=0, direction='rtl'))
            except TypeError:
                styles.add(ParagraphStyle(name='ArabicTitle', fontName=font_bold, fontSize=18, alignment=2, spaceAfter=8, textColor=colors.white, wordWrap='RTL'))
                styles.add(ParagraphStyle(name='Arabic', fontName=font_name, fontSize=12, alignment=2, wordWrap='RTL'))
                styles.add(ParagraphStyle(name='Boxed', fontName=font_name, fontSize=12, alignment=2, backColor=colors.whitesmoke, borderPadding=6, borderColor=colors.HexColor('#1976D2'), borderWidth=1, borderRadius=4, wordWrap='RTL', leading=18, rightIndent=0, leftIndent=0))

            # Table: auto-fit each column to max text width, then scale to fit page width, increase row height, force RTL
            from reportlab.pdfbase.pdfmetrics import stringWidth
            available_width = page_size[0] - 32  # left+right margins (16+16)
            col_count = len(columns_rtl)
            table_font_size = 12
            paddings = 8  # left+right padding per cell
            # Calculate max width for each column
            col_widths = []
            for col_idx in range(col_count):
                maxw = 0
                for row in data_table:
                    txt = str(row[col_idx])
                    w = stringWidth(txt, font_name if col_idx > 0 else font_bold, table_font_size)
                    if w > maxw:
                        maxw = w
                col_widths.append(maxw + paddings)
            total_width = sum(col_widths)
            # Scale all columns so total width == available_width
            if total_width > 0:
                scale = available_width / total_width
                col_widths = [w * scale for w in col_widths]
            # Increase row height by increasing TOPPADDING and BOTTOMPADDING
            table = Table(data_table, repeatRows=1, hAlign='RIGHT', colWidths=col_widths)
            style_list = [
                ('FONTNAME', (0,0), (-1,0), font_bold),
                ('FONTNAME', (0,1), (-1,-1), font_name),
                ('FONTSIZE', (0,0), (-1,-1), table_font_size),
                ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('GRID', (0,0), (-1,-1), 0.7, colors.HexColor('#1976D2')),
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1976D2')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.lightgrey]),
                ('LEFTPADDING', (0,0), (-1,-1), 2),
                ('RIGHTPADDING', (0,0), (-1,-1), 2),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ]
            # Try to force RTL direction for table (if supported)
            try:
                style_list.append(('RIGHTTORIGHT', (0,0), (-1,-1), None))
            except Exception:
                pass
            table.setStyle(TableStyle(style_list))


            elements = []

            # Custom header bar (colored, with logo, title, date)
            class HeaderBar(Flowable):
                def __init__(self, width, height):
                    super().__init__()
                    self.width = width
                    self.height = height
                def draw(self):
                    c = self.canv
                    c.saveState()
                    c.setFillColor(colors.HexColor('#1976D2'))
                    c.roundRect(0, 0, self.width, self.height, 12, fill=1, stroke=0)
                    # Logo
                    logo_path = 'MOELogo.png'
                    logo_h = self.height * 0.7
                    logo_w = logo_h
                    if os.path.exists(logo_path):
                        try:
                            logo = ImageReader(logo_path)
                            c.drawImage(logo, 10, (self.height-logo_h)/2, width=logo_w, height=logo_h, mask='auto')
                        except Exception:
                            pass
                    # Title (force Amiri font if available)
                    try:
                        c.setFont(font_bold, 18)
                    except Exception:
                        c.setFont('Helvetica-Bold', 18)
                    c.setFillColor(colors.white)
                    c.drawRightString(self.width-20, self.height/2+6, ar_text(title))
                    # Date
                    try:
                        c.setFont(font_name, 12)
                    except Exception:
                        c.setFont('Helvetica', 12)
                    c.drawString(logo_w+20, self.height/2-8, ar_text(f'التاريخ: {today_str}'))
                    c.restoreState()

            elements.append(HeaderBar(page_size[0]-32, 38))
            elements.append(Spacer(1, 8))



            # Filters and stats box (multi-line, right-aligned, wrap, force Amiri font)
            box_lines = []
            if filters_text:
                box_lines.append(f'<b>الفلاتر:</b> {filters_text}')
            box_lines.append(f'<b>عدد الطلاب (بدون تكرار):</b> {unique_students}')
            box_lines.append(f'<b>عدد مواد الرسوب:</b> {num_rows}')
            box_text = '<br/>'.join(box_lines)
            elements.append(Paragraph(ar_text(box_text), styles['Boxed']))
            elements.append(Spacer(1, 10))

            # Add table with right alignment (flush right)
            elements.append(table)

            # Footer with page number
            def draw_footer(canvas, doc):
                canvas.saveState()
                try:
                    canvas.setFont(font_name, 11)
                except Exception:
                    canvas.setFont('Helvetica', 11)
                page_num = canvas.getPageNumber()
                # Always use ar_text for page label
                canvas.drawRightString(page_size[0]-50, 15, ar_text(f'صفحة {page_num}'))
                canvas.restoreState()

            # Reduce top margin
            doc = SimpleDocTemplate(path, pagesize=page_size, rightMargin=16, leftMargin=16, topMargin=18, bottomMargin=18)
            doc.build(elements, onFirstPage=lambda c, d: draw_footer(c, d), onLaterPages=lambda c, d: draw_footer(c, d))
            reply = QMessageBox.question(self, 'تم', 'تم تصدير البيانات إلى PDF بنجاح.\nهل تريد فتح المجلد؟',
                                        QMessageBox.Yes | QMessageBox.Close, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                try:
                    import subprocess
                    subprocess.Popen(f'explorer /select,"{path}"')
                except Exception:
                    pass
        except ImportError:
            QMessageBox.critical(self, 'خطأ', 'يجب تثبيت مكتبة reportlab و arabic_reshaper و python-bidi.')
        except Exception as e:
            QMessageBox.critical(self, 'خطأ', f'حدث خطأ أثناء تصدير PDF: {e}')
    def build_query(self):
        filters = []
        if self.national_id_input.text().strip():
            filters.append(f"stu.national_id LIKE '%{self.national_id_input.text().strip()}%'")
        if self.subject_combo.currentText() != 'كل المواد':
            filters.append(f"sub.name = '{self.subject_combo.currentText()}'")
        if self.stage_combo.currentText() != 'كل المراحل':
            filters.append(f"s.name = '{self.stage_combo.currentText()}'")
        if self.term_combo.currentText() != 'كل الفصول':
            filters.append(f"t.name = '{self.term_combo.currentText()}'")
        if self.year_combo.currentText() != 'كل الأعوام':
            filters.append(f"y.name = '{self.year_combo.currentText()}'")
        where_clause = 'WHERE ' + ' AND '.join(filters) if filters else ''
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
        return query

    def load_data(self):
        font = QFont('Cairo', 12)
        query = self.build_query()
        try:
            df = pd.read_sql_query(query, self.conn)
        except Exception as e:
            QMessageBox.critical(self, 'خطأ', f'خطأ في الاستعلام: {e}')
            return
        self.df = df
        # Reverse columns for RTL display
        columns_rtl = list(df.columns)[::-1]
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(columns_rtl))
        self.table.setHorizontalHeaderLabels([str(col) for col in columns_rtl])
        self.table.setLayoutDirection(Qt.RightToLeft)
        self.table.horizontalHeader().setFont(font)
        for i, row in df.iterrows():
            row_rtl = list(row)[::-1]
            for j, val in enumerate(row_rtl):
                item = QTableWidgetItem(str(val))
                # Detect column type for alignment
                col_name = columns_rtl[j]
                if (col_name in ['رقم_الهوية', 'م', 'عدد_الطلاب_الراسبين', 'عدد_مرات_التعثر'] or str(val).isdigit()):
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item.setFont(font)
                self.table.setItem(i, j, item)
        self.table.resizeColumnsToContents()
        # Restore column visibility if user customized
        if hasattr(self, 'column_checkboxes'):
            for cb, idx in self.column_checkboxes:
                self.table.setColumnHidden(idx, not cb.isChecked())

    def export_excel(self):
        if not hasattr(self, 'df') or self.df.empty:
            QMessageBox.warning(self, 'تنبيه', 'لا توجد بيانات للتصدير.')
            return
        path, _ = QFileDialog.getSaveFileName(self, 'حفظ ملف Excel', '', 'Excel Files (*.xlsx)')
        if not path:
            return
        wb = openpyxl.Workbook()
        ws = wb.active
        cairo_font = XLFont(name='Cairo', size=12)
        # Header
        ws.append([ar_text(col) for col in self.df.columns])
        # Data
        for _, row in self.df.iterrows():
            ws.append([ar_text(val) for val in row])
        for row in ws.iter_rows():
            for cell in row:
                cell.font = cairo_font
        wb.save(path)
        reply = QMessageBox.question(self, 'تم', 'تم تصدير البيانات إلى Excel بنجاح.\nهل تريد فتح المجلد؟',
                                    QMessageBox.Yes | QMessageBox.Close, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            try:
                import subprocess
                subprocess.Popen(f'explorer /select,"{path}"')
            except Exception:
                pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = StudentFailuresApp()
    window.show()
    sys.exit(app.exec())
