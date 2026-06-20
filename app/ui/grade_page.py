from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QComboBox, QTableWidget, QTableWidgetItem,
                               QSplitter, QMessageBox, QGroupBox, QFileDialog,
                               QTabWidget, QTextEdit, QLineEdit, QDateEdit,
                               QHeaderView, QProgressBar)
from PySide6.QtCore import Qt, QThread, Signal, QDate
from PySide6.QtGui import QFont, QColor, QBrush
from ..db.dao import ClassDAO
from ..services.grade_service import GradeService
from .chart_widget import ChartWidget


class ImportExcelThread(QThread):
    finished_signal = Signal(dict)
    error_signal = Signal(str)
    progress_signal = Signal(int)

    def __init__(self, service, file_path, class_id, exam_name, exam_date):
        super().__init__()
        self.service = service
        self.file_path = file_path
        self.class_id = class_id
        self.exam_name = exam_name
        self.exam_date = exam_date

    def run(self):
        try:
            self.progress_signal.emit(20)
            parsed = self.service.parse_excel(self.file_path)
            self.progress_signal.emit(60)
            exam_id, count = self.service.import_scores(
                self.class_id, self.exam_name, parsed, self.exam_date
            )
            self.progress_signal.emit(100)
            self.finished_signal.emit({'exam_id': exam_id, 'imported': count})
        except Exception as e:
            self.error_signal.emit(str(e))


class GradePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.class_dao = ClassDAO()
        self.service = GradeService()
        self._init_ui()
        self._load_classes()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("📊 成绩分析中心")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #1976D2; padding: 5px;")
        main_layout.addWidget(title)

        top_group = QGroupBox("成绩导入")
        top_layout = QVBoxLayout(top_group)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("选择班级:"))
        self.class_combo = QComboBox()
        self.class_combo.setMinimumWidth(200)
        self.class_combo.currentIndexChanged.connect(self._on_class_changed)
        row1.addWidget(self.class_combo)
        row1.addSpacing(15)
        row1.addWidget(QLabel("考试名称:"))
        self.exam_name_edit = QLineEdit()
        self.exam_name_edit.setPlaceholderText("如：期中考试、第一次月考")
        self.exam_name_edit.setMinimumWidth(180)
        row1.addWidget(self.exam_name_edit)
        row1.addSpacing(15)
        row1.addWidget(QLabel("考试日期:"))
        self.exam_date_edit = QDateEdit()
        self.exam_date_edit.setCalendarPopup(True)
        self.exam_date_edit.setDate(QDate.currentDate())
        row1.addWidget(self.exam_date_edit)
        row1.addStretch()
        top_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("拖拽Excel文件到此处，或点击右侧按钮选择...")
        self.file_path_edit.setMinimumWidth(400)
        self.browse_btn = QPushButton("📂 选择Excel文件")
        self.browse_btn.clicked.connect(self._browse_file)
        self.import_btn = QPushButton("🚀 开始导入")
        self.import_btn.setMinimumHeight(32)
        self.import_btn.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; font-weight: bold; "
            "border-radius: 4px; padding: 6px 20px; }"
            "QPushButton:hover { background-color: #1976D2; }"
            "QPushButton:disabled { background-color: #BDBDBD; }"
        )
        self.import_btn.clicked.connect(self._import_scores)
        row2.addWidget(self.file_path_edit, 1)
        row2.addWidget(self.browse_btn)
        row2.addWidget(self.import_btn)
        top_layout.addLayout(row2)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        top_layout.addWidget(self.progress_bar)

        main_layout.addWidget(top_group)

        splitter = QSplitter(Qt.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        exam_group = QGroupBox("考试列表")
        exam_layout = QVBoxLayout(exam_group)
        self.exam_combo = QComboBox()
        self.exam_combo.currentIndexChanged.connect(self._on_exam_changed)
        exam_layout.addWidget(self.exam_combo)
        self.score_table = QTableWidget()
        self.score_table.setAlternatingRowColors(True)
        self.score_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        exam_layout.addWidget(self.score_table, 1)
        left_layout.addWidget(exam_group)

        splitter.addWidget(left_widget)

        right_tab = QTabWidget()

        self.stats_tab = QWidget()
        self._init_stats_tab()
        right_tab.addTab(self.stats_tab, "📈 统计分析")

        self.chart_tab = QWidget()
        self._init_chart_tab()
        right_tab.addTab(self.chart_tab, "📊 可视化图表")

        self.report_tab = QWidget()
        self._init_report_tab()
        right_tab.addTab(self.report_tab, "📝 学情报告")

        splitter.addWidget(right_tab)
        splitter.setSizes([450, 650])
        main_layout.addWidget(splitter, 1)

    def _init_stats_tab(self):
        layout = QVBoxLayout(self.stats_tab)
        self.stats_table = QTableWidget()
        self.stats_table.setAlternatingRowColors(True)
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.stats_table)

        rank_group = QGroupBox("班级排名")
        rank_layout = QVBoxLayout(rank_group)
        self.rank_table = QTableWidget()
        self.rank_table.setAlternatingRowColors(True)
        self.rank_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.rank_table.setMaximumHeight(250)
        rank_layout.addWidget(self.rank_table)
        layout.addWidget(rank_group)

    def _init_chart_tab(self):
        layout = QVBoxLayout(self.chart_tab)

        chart_select = QHBoxLayout()
        chart_select.addWidget(QLabel("图表类型:"))
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems([
            "成绩分布直方图", "各科平均分柱状图",
            "及格率饼图", "学生个人趋势图", "学生雷达图"
        ])
        self.chart_type_combo.currentIndexChanged.connect(self._update_chart)
        chart_select.addWidget(self.chart_type_combo)
        chart_select.addSpacing(20)
        chart_select.addWidget(QLabel("选择学生:"))
        self.chart_student_combo = QComboBox()
        self.chart_student_combo.currentIndexChanged.connect(self._update_chart)
        chart_select.addWidget(self.chart_student_combo)
        chart_select.addSpacing(20)
        chart_select.addWidget(QLabel("选择学科:"))
        self.chart_subject_combo = QComboBox()
        self.chart_subject_combo.currentIndexChanged.connect(self._update_chart)
        chart_select.addWidget(self.chart_subject_combo)
        chart_select.addStretch()
        layout.addLayout(chart_select)

        self.chart_widget = ChartWidget()
        layout.addWidget(self.chart_widget, 1)

    def _init_report_tab(self):
        layout = QVBoxLayout(self.report_tab)

        btn_row = QHBoxLayout()
        btn_row.addWidget(QLabel("选择学生生成报告:"))
        self.report_student_combo = QComboBox()
        btn_row.addWidget(self.report_student_combo)
        self.detect_weak_btn = QPushButton("🔍 自动识别薄弱学生")
        self.detect_weak_btn.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; font-weight: bold; "
            "border-radius: 4px; padding: 6px 15px; }"
            "QPushButton:hover { background-color: #F57C00; }"
        )
        self.detect_weak_btn.clicked.connect(self._detect_weak_students)
        btn_row.addWidget(self.detect_weak_btn)
        self.gen_report_btn = QPushButton("📝 生成学情报告")
        self.gen_report_btn.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; font-weight: bold; "
            "border-radius: 4px; padding: 6px 15px; }"
            "QPushButton:hover { background-color: #1976D2; }"
        )
        self.gen_report_btn.clicked.connect(self._generate_student_report)
        btn_row.addWidget(self.gen_report_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setFont(QFont("Microsoft YaHei", 10))
        layout.addWidget(self.report_text, 1)

    def _load_classes(self):
        self.class_combo.clear()
        classes = self.class_dao.get_all()
        for c in classes:
            self.class_combo.addItem(
                f"{c['name']}（{c.get('teacher', '')}）", c['id']
            )
        if not classes:
            self.class_combo.addItem("暂无班级，请先生成测试数据", None)

    def _on_class_changed(self, index):
        class_id = self.class_combo.currentData()
        self.exam_combo.clear()
        self.report_student_combo.clear()
        self.chart_student_combo.clear()
        self.score_table.setRowCount(0)
        self.score_table.setColumnCount(0)
        self.stats_table.setRowCount(0)
        self.stats_table.setColumnCount(0)
        self.rank_table.setRowCount(0)
        self.rank_table.setColumnCount(0)
        self.chart_widget.clear()
        self.report_text.clear()

        if class_id is None:
            self.exam_combo.addItem("暂无考试", None)
            return

        exams = self.service.get_exam_list(class_id)
        for e in exams:
            self.exam_combo.addItem(
                f"{e['name']}（{e.get('exam_date', '')}）", e['id']
            )
        if not exams:
            self.exam_combo.addItem("暂无考试数据，请先导入成绩", None)

        from ..db.dao import StudentDAO
        sd = StudentDAO()
        students = sd.get_by_class(class_id)
        for s in students:
            self.report_student_combo.addItem(s['name'], s['id'])
            self.chart_student_combo.addItem(s['name'], s['id'])

    def _on_exam_changed(self, index):
        exam_id = self.exam_combo.currentData()
        if exam_id is None:
            return
        self._load_score_table(exam_id)
        self._load_stats_table(exam_id)
        self._update_chart_subjects(exam_id)
        self._update_chart()

    def _load_score_table(self, exam_id):
        scores = self.service.get_exam_scores(exam_id)
        if not scores:
            return

        student_scores = {}
        subjects = []
        for s in scores:
            sid = s['student_id']
            if sid not in student_scores:
                student_scores[sid] = {'name': s['student_name']}
            student_scores[sid][s['subject']] = s['score']
            if s['subject'] not in subjects:
                subjects.append(s['subject'])

        self.score_table.setRowCount(len(student_scores))
        self.score_table.setColumnCount(len(subjects) + 1)
        headers = ['学生姓名'] + subjects
        self.score_table.setHorizontalHeaderLabels(headers)

        for row, (sid, data) in enumerate(student_scores.items()):
            self.score_table.setItem(row, 0, QTableWidgetItem(data['name']))
            for col, subj in enumerate(subjects):
                score = data.get(subj, '-')
                item = QTableWidgetItem(str(score))
                if isinstance(score, (int, float)):
                    if score < 60:
                        item.setForeground(QBrush(QColor('#F44336')))
                    elif score >= 90:
                        item.setForeground(QBrush(QColor('#4CAF50')))
                item.setTextAlignment(Qt.AlignCenter)
                self.score_table.setItem(row, col + 1, item)

    def _load_stats_table(self, exam_id):
        stats = self.service.calculate_statistics(exam_id)
        rankings = stats.pop('_rankings', [])

        subject_keys = [k for k in stats.keys()]
        self.stats_table.setRowCount(len(subject_keys))
        self.stats_table.setColumnCount(7)
        self.stats_table.setHorizontalHeaderLabels(
            ['学科', '平均分', '最高分', '最低分', '标准差', '及格率', '优秀率']
        )
        for row, subj in enumerate(subject_keys):
            d = stats[subj]
            items = [
                QTableWidgetItem(subj),
                QTableWidgetItem(str(d['avg'])),
                QTableWidgetItem(str(d['max'])),
                QTableWidgetItem(str(d['min'])),
                QTableWidgetItem(str(d['std'])),
                QTableWidgetItem(f"{d['pass_rate']}%"),
                QTableWidgetItem(f"{d['excellent_rate']}%")
            ]
            for col, it in enumerate(items):
                it.setTextAlignment(Qt.AlignCenter)
                self.stats_table.setItem(row, col, it)

        self.rank_table.setRowCount(len(rankings))
        self.rank_table.setColumnCount(4)
        self.rank_table.setHorizontalHeaderLabels(['排名', '姓名', '总分', '平均分'])
        for row, r in enumerate(rankings):
            items = [
                QTableWidgetItem(str(r['rank'])),
                QTableWidgetItem(r['name']),
                QTableWidgetItem(str(r['total'])),
                QTableWidgetItem(str(r['avg']))
            ]
            for col, it in enumerate(items):
                it.setTextAlignment(Qt.AlignCenter)
                self.rank_table.setItem(row, col, it)
            if r['rank'] <= 3:
                for col in range(4):
                    self.rank_table.item(row, col).setBackground(QBrush(QColor('#FFF9C4')))

    def _update_chart_subjects(self, exam_id):
        scores = self.service.get_exam_scores(exam_id)
        subjects = list(set(s['subject'] for s in scores))
        self.chart_subject_combo.blockSignals(True)
        self.chart_subject_combo.clear()
        self.chart_subject_combo.addItems(subjects)
        self.chart_subject_combo.blockSignals(False)

    def _update_chart(self):
        exam_id = self.exam_combo.currentData()
        chart_type = self.chart_type_combo.currentText()
        student_id = self.chart_student_combo.currentData()
        subject = self.chart_subject_combo.currentText()

        if chart_type == "成绩分布直方图":
            if exam_id is None:
                return
            stats = self.service.calculate_statistics(exam_id)
            all_scores = []
            for k, v in stats.items():
                if k != '_rankings':
                    all_scores.extend(v.get('scores', []))
            if all_scores:
                self.chart_widget.plot_histogram(all_scores, title="全班成绩分布")
        elif chart_type == "各科平均分柱状图":
            if exam_id is None:
                return
            stats = self.service.calculate_statistics(exam_id)
            subjects = [k for k in stats.keys() if k != '_rankings']
            avgs = [stats[k]['avg'] for k in subjects]
            if subjects:
                self.chart_widget.plot_bar_chart(subjects, avgs,
                                                   title="各科平均分对比",
                                                   ylabel="平均分")
        elif chart_type == "及格率饼图":
            if exam_id is None:
                return
            stats = self.service.calculate_statistics(exam_id)
            subjects = [k for k in stats.keys() if k != '_rankings']
            if subjects:
                pass_counts = [stats[k]['pass_count'] for k in subjects]
                fail_counts = [stats[k]['count'] - stats[k]['pass_count'] for k in subjects]
                total_pass = sum(pass_counts)
                total_fail = sum(fail_counts)
                self.chart_widget.plot_pie_chart(
                    ['及格人数', '不及格人数'],
                    [total_pass, total_fail],
                    title="全班及格情况统计"
                )
        elif chart_type == "学生个人趋势图":
            if student_id is None or not subject:
                return
            trend = self.service.get_student_trend_data(student_id, subject)
            if trend['dates']:
                self.chart_widget.plot_line_chart(
                    trend['dates'], trend['scores'],
                    title=f"{self.chart_student_combo.currentText()} - {subject} 成绩趋势"
                )
        elif chart_type == "学生雷达图":
            if student_id is None or exam_id is None:
                return
            scores = self.service.get_exam_scores(exam_id)
            student_scores = [s for s in scores if s['student_id'] == student_id]
            if student_scores:
                subjects = [s['subject'] for s in student_scores]
                values = [s['score'] for s in student_scores]
                self.chart_widget.plot_radar_chart(
                    subjects, values,
                    title=f"{self.chart_student_combo.currentText()} 学科能力雷达图"
                )

    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择成绩文件", "",
            "Excel文件 (*.xlsx *.xls);;CSV文件 (*.csv);;所有文件 (*.*)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)

    def _import_scores(self):
        class_id = self.class_combo.currentData()
        file_path = self.file_path_edit.text().strip()
        exam_name = self.exam_name_edit.text().strip()

        if class_id is None:
            QMessageBox.warning(self, "提示", "请先选择班级")
            return
        if not file_path:
            QMessageBox.warning(self, "提示", "请选择Excel/CSV文件")
            return
        if not exam_name:
            QMessageBox.warning(self, "提示", "请填写考试名称")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.import_btn.setEnabled(False)

        self.import_thread = ImportExcelThread(
            self.service, file_path, class_id, exam_name,
            self.exam_date_edit.date().toString("yyyy-MM-dd")
        )
        self.import_thread.progress_signal.connect(self.progress_bar.setValue)
        self.import_thread.finished_signal.connect(self._on_import_finished)
        self.import_thread.error_signal.connect(self._on_import_error)
        self.import_thread.start()

    def _on_import_finished(self, result):
        self.progress_bar.setVisible(False)
        self.import_btn.setEnabled(True)
        QMessageBox.information(
            self, "成功",
            f"导入成功！\n考试ID: {result['exam_id']}\n导入成绩条数: {result['imported']}"
        )
        self._on_class_changed(self.class_combo.currentIndex())
        self.file_path_edit.clear()
        self.exam_name_edit.clear()

    def _on_import_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.import_btn.setEnabled(True)
        QMessageBox.critical(self, "错误", f"导入失败：{error_msg}")

    def _detect_weak_students(self):
        class_id = self.class_combo.currentData()
        if class_id is None:
            QMessageBox.warning(self, "提示", "请先选择班级")
            return

        weak = self.service.detect_weak_students(class_id, 70)
        if not weak:
            self.report_text.setHtml(
                "<div style='padding:20px; color:#4CAF50; text-align:center; font-size:14px;'>"
                "<h3>🎉 太棒了！</h3>本班暂无平均分低于70分的薄弱学生</div>"
            )
            return

        html = f"<h3 style='color:#F44336;'>⚠️ 识别到 {len(weak)} 名薄弱学生（平均分<70）</h3><hr>"
        for s in weak:
            report = s['report']
            html += f"""
            <div style='border:1px solid #FFCDD2; border-radius:6px; padding:12px; margin:10px 0; background:#FFEBEE;'>
                <h4 style='margin:0 0 8px 0; color:#D32F2F;'>
                    🏅 #{s['rank']} {s['name']} - 平均分 {s['avg_score']} / 总分 {s['total_score']}
                </h4>
                <p><b>总体评价：</b>{report.get('summary','')}</p>
                <p><b>优势：</b>{report.get('strengths','')}</p>
                <p><b>薄弱点：</b>{report.get('weaknesses','')}</p>
                <p><b>学习建议：</b></p>
                <ul>
                    {''.join(f'<li>{x}</li>' for x in report.get('suggestions', []))}
                </ul>
                <p><b>趋势：</b>{report.get('trend','')}</p>
            </div>
            """
        self.report_text.setHtml(html)

    def _generate_student_report(self):
        student_id = self.report_student_combo.currentData()
        if student_id is None:
            QMessageBox.warning(self, "提示", "请选择学生")
            return
        report = self.service.generate_student_report(student_id)
        name = self.report_student_combo.currentText()
        html = f"""
        <h2 style='color:#1976D2; text-align:center;'>📋 {name} 同学学情分析报告</h2>
        <hr>
        <h3 style='color:#388E3C;'>📝 总体评价</h3>
        <p style='line-height:1.8; padding:0 10px;'>{report.get('summary','')}</p>
        <h3 style='color:#388E3C;'>💪 优势分析</h3>
        <p style='line-height:1.8; padding:0 10px;'>{report.get('strengths','')}</p>
        <h3 style='color:#F57C00;'>⚠️ 薄弱点分析</h3>
        <p style='line-height:1.8; padding:0 10px;'>{report.get('weaknesses','')}</p>
        <h3 style='color:#1976D2;'>📖 个性化学习建议</h3>
        <ol style='line-height:2;'>
            {''.join(f'<li>{x}</li>' for x in report.get('suggestions', []))}
        </ol>
        <h3 style='color:#7B1FA2;'>📈 成绩趋势</h3>
        <p style='line-height:1.8; padding:0 10px;'>{report.get('trend','')}</p>
        <hr>
        <p style='color:#999; text-align:right;'>生成时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        """
        self.report_text.setHtml(html)

    def refresh(self):
        self._load_classes()
