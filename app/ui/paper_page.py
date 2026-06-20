from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QComboBox, QTableWidget, QTableWidgetItem,
                               QSplitter, QMessageBox, QGroupBox, QFileDialog,
                               QTabWidget, QTextEdit, QLineEdit, QHeaderView,
                               QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QColor, QBrush
from ..db.dao import ClassDAO
from ..services.paper_service import PaperService
from .chart_widget import ChartWidget


class AnalyzePaperThread(QThread):
    finished_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, service, file_path, paper_name, subject, class_id):
        super().__init__()
        self.service = service
        self.file_path = file_path
        self.paper_name = paper_name
        self.subject = subject
        self.class_id = class_id

    def run(self):
        try:
            result = self.service.analyze_paper(
                self.file_path, self.paper_name, self.subject, self.class_id
            )
            self.finished_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))


class PaperPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.class_dao = ClassDAO()
        self.service = PaperService()
        self._init_ui()
        self._load_classes()
        self._load_paper_list()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("📄 试卷智能分析")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #1976D2; padding: 5px;")
        main_layout.addWidget(title)

        top_group = QGroupBox("试卷上传与分析")
        top_layout = QVBoxLayout(top_group)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("试卷名称:"))
        self.paper_name_edit = QLineEdit()
        self.paper_name_edit.setPlaceholderText("如：高一期中数学试卷")
        self.paper_name_edit.setMinimumWidth(200)
        row1.addWidget(self.paper_name_edit)
        row1.addSpacing(15)
        row1.addWidget(QLabel("学科:"))
        self.subject_combo = QComboBox()
        self.subject_combo.addItems(["语文", "数学", "英语", "物理", "化学",
                                      "生物", "历史", "地理", "政治"])
        row1.addWidget(self.subject_combo)
        row1.addSpacing(15)
        row1.addWidget(QLabel("关联班级:"))
        self.class_combo = QComboBox()
        self.class_combo.setMinimumWidth(200)
        row1.addWidget(self.class_combo)
        row1.addStretch()
        top_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText(
            "拖拽试卷图片/PDF/文本到此处，或点击右侧按钮选择..."
        )
        self.file_path_edit.setMinimumWidth(450)
        self.browse_btn = QPushButton("📂 选择试卷文件")
        self.browse_btn.clicked.connect(self._browse_file)
        self.analyze_btn = QPushButton("🔍 智能分析试卷")
        self.analyze_btn.setMinimumHeight(32)
        self.analyze_btn.setStyleSheet(
            "QPushButton { background-color: #9C27B0; color: white; font-weight: bold; "
            "border-radius: 4px; padding: 6px 20px; }"
            "QPushButton:hover { background-color: #7B1FA2; }"
            "QPushButton:disabled { background-color: #BDBDBD; }"
        )
        self.analyze_btn.clicked.connect(self._analyze_paper)
        row2.addWidget(self.file_path_edit, 1)
        row2.addWidget(self.browse_btn)
        row2.addWidget(self.analyze_btn)
        top_layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("💡 或直接粘贴题目内容（每行一题）:"))
        row3.addStretch()
        top_layout.addLayout(row3)

        self.questions_text = QTextEdit()
        self.questions_text.setPlaceholderText("1. 题目内容...\n2. 题目内容...\n3. 题目内容...")
        self.questions_text.setMaximumHeight(80)
        top_layout.addWidget(self.questions_text)

        row4 = QHBoxLayout()
        self.analyze_text_btn = QPushButton("📝 从文本分析")
        self.analyze_text_btn.setStyleSheet(
            "QPushButton { background-color: #009688; color: white; font-weight: bold; "
            "border-radius: 4px; padding: 6px 20px; }"
            "QPushButton:hover { background-color: #00796B; }"
        )
        self.analyze_text_btn.clicked.connect(self._analyze_from_text)
        row4.addStretch()
        row4.addWidget(self.analyze_text_btn)
        top_layout.addLayout(row4)

        main_layout.addWidget(top_group)

        splitter = QSplitter(Qt.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        paper_group = QGroupBox("已分析试卷")
        paper_layout = QVBoxLayout(paper_group)
        self.paper_list = QListWidget()
        self.paper_list.itemClicked.connect(self._on_paper_selected)
        paper_layout.addWidget(self.paper_list)
        left_layout.addWidget(paper_group)

        splitter.addWidget(left_widget)

        right_tab = QTabWidget()

        self.questions_tab = QWidget()
        self._init_questions_tab()
        right_tab.addTab(self.questions_tab, "📋 题目拆解")

        self.error_tab = QWidget()
        self._init_error_tab()
        right_tab.addTab(self.error_tab, "❌ 错题分布")

        self.review_tab = QWidget()
        self._init_review_tab()
        right_tab.addTab(self.review_tab, "🎯 讲评提纲")

        splitter.addWidget(right_tab)
        splitter.setSizes([300, 800])
        main_layout.addWidget(splitter, 1)

    def _init_questions_tab(self):
        layout = QVBoxLayout(self.questions_tab)
        self.questions_table = QTableWidget()
        self.questions_table.setAlternatingRowColors(True)
        self.questions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.questions_table)

    def _init_error_tab(self):
        layout = QVBoxLayout(self.error_tab)

        btn_row = QHBoxLayout()
        self.refresh_error_btn = QPushButton("🔄 刷新错题统计")
        self.refresh_error_btn.clicked.connect(self._refresh_error_distribution)
        btn_row.addWidget(self.refresh_error_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.error_chart = ChartWidget()
        layout.addWidget(self.error_chart, 1)

        self.error_table = QTableWidget()
        self.error_table.setAlternatingRowColors(True)
        self.error_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.error_table.setMaximumHeight(250)
        layout.addWidget(self.error_table)

    def _init_review_tab(self):
        layout = QVBoxLayout(self.review_tab)

        btn_row = QHBoxLayout()
        self.gen_review_btn = QPushButton("📝 生成讲评提纲")
        self.gen_review_btn.setStyleSheet(
            "QPushButton { background-color: #FF5722; color: white; font-weight: bold; "
            "border-radius: 4px; padding: 8px 20px; }"
            "QPushButton:hover { background-color: #E64A19; }"
        )
        self.gen_review_btn.clicked.connect(self._generate_review_outline)
        btn_row.addStretch()
        btn_row.addWidget(self.gen_review_btn)
        layout.addLayout(btn_row)

        self.review_text = QTextEdit()
        self.review_text.setReadOnly(True)
        self.review_text.setFont(QFont("Microsoft YaHei", 10))
        layout.addWidget(self.review_text, 1)

    def _load_classes(self):
        self.class_combo.clear()
        self.class_combo.addItem("（不关联班级）", None)
        classes = self.class_dao.get_all()
        for c in classes:
            self.class_combo.addItem(
                f"{c['name']}（{c.get('teacher', '')}）", c['id']
            )

    def _load_paper_list(self):
        self.paper_list.clear()
        papers = self.service.get_paper_list()
        for p in papers:
            item = QListWidgetItem(
                f"📄 {p['name']}\n   {p.get('subject', '')} | {p.get('created_at', '')[:10]}"
            )
            item.setData(Qt.UserRole, p['id'])
            self.paper_list.addItem(item)
        if not papers:
            item = QListWidgetItem("暂无已分析的试卷，请先上传分析")
            item.setData(Qt.UserRole, None)
            self.paper_list.addItem(item)

    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择试卷文件", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp);;PDF文件 (*.pdf);;"
            "文本文件 (*.txt);;所有文件 (*.*)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)

    def _analyze_paper(self):
        file_path = self.file_path_edit.text().strip()
        paper_name = self.paper_name_edit.text().strip()
        subject = self.subject_combo.currentText()
        class_id = self.class_combo.currentData()

        if not file_path:
            QMessageBox.warning(self, "提示", "请选择试卷文件")
            return
        if not paper_name:
            QMessageBox.warning(self, "提示", "请填写试卷名称")
            return

        self.analyze_btn.setEnabled(False)
        self.analyze_btn.setText("⏳ 正在OCR识别与分析...")

        self.analyze_thread = AnalyzePaperThread(
            self.service, file_path, paper_name, subject, class_id
        )
        self.analyze_thread.finished_signal.connect(self._on_analyze_finished)
        self.analyze_thread.error_signal.connect(self._on_analyze_error)
        self.analyze_thread.start()

    def _analyze_from_text(self):
        text = self.questions_text.toPlainText().strip()
        paper_name = self.paper_name_edit.text().strip()
        subject = self.subject_combo.currentText()
        class_id = self.class_combo.currentData()

        if not text:
            QMessageBox.warning(self, "提示", "请粘贴题目内容")
            return
        if not paper_name:
            QMessageBox.warning(self, "提示", "请填写试卷名称")
            return

        self.analyze_text_btn.setEnabled(False)
        try:
            result = self.service.analyze_paper_from_text(
                text, paper_name, subject, class_id
            )
            self._on_analyze_finished(result)
            self.questions_text.clear()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"分析失败：{str(e)}")
        finally:
            self.analyze_text_btn.setEnabled(True)

    def _on_analyze_finished(self, result):
        self.analyze_btn.setEnabled(True)
        self.analyze_btn.setText("🔍 智能分析试卷")
        QMessageBox.information(
            self, "成功",
            f"试卷分析完成！\n共识别 {result['question_count']} 道题目"
        )
        self._load_paper_list()
        self.paper_name_edit.clear()
        self.file_path_edit.clear()

    def _on_analyze_error(self, error_msg):
        self.analyze_btn.setEnabled(True)
        self.analyze_btn.setText("🔍 智能分析试卷")
        QMessageBox.critical(self, "错误", f"分析失败：{error_msg}")

    def _on_paper_selected(self, item):
        paper_id = item.data(Qt.UserRole)
        if paper_id is None:
            return

        detail = self.service.get_paper_detail(paper_id)
        self._load_questions_table(detail.get('questions', []))
        self._refresh_error_distribution()
        self.review_text.clear()

    def _load_questions_table(self, questions):
        self.questions_table.setRowCount(len(questions))
        self.questions_table.setColumnCount(6)
        self.questions_table.setHorizontalHeaderLabels(
            ['题号', '题目内容', '分值', '考点', '难度系数', '易错点']
        )
        for row, q in enumerate(questions):
            items = [
                QTableWidgetItem(str(q.get('question_no', ''))),
                QTableWidgetItem(str(q.get('content', ''))),
                QTableWidgetItem(str(q.get('score', 0))),
                QTableWidgetItem(str(q.get('knowledge_point', ''))),
                QTableWidgetItem(str(q.get('difficulty', 0))),
                QTableWidgetItem(str(q.get('common_mistakes', '')))
            ]
            for col, it in enumerate(items):
                it.setTextAlignment(Qt.AlignCenter if col != 1 else Qt.AlignLeft | Qt.AlignVCenter)
                if col == 4:
                    diff = q.get('difficulty', 0)
                    if diff >= 0.7:
                        it.setForeground(QBrush(QColor('#F44336')))
                    elif diff >= 0.5:
                        it.setForeground(QBrush(QColor('#FF9800')))
                    else:
                        it.setForeground(QBrush(QColor('#4CAF50')))
            self.questions_table.setItem(row, 0, items[0])
            self.questions_table.setItem(row, 1, items[1])
            self.questions_table.setItem(row, 2, items[2])
            self.questions_table.setItem(row, 3, items[3])
            self.questions_table.setItem(row, 4, items[4])
            self.questions_table.setItem(row, 5, items[5])

    def _refresh_error_distribution(self):
        current_item = self.paper_list.currentItem()
        if not current_item:
            return
        paper_id = current_item.data(Qt.UserRole)
        if paper_id is None:
            return

        error_dist = self.service.get_error_distribution(paper_id)
        if error_dist:
            labels = [f"第{e.get('question_no','?')}题" for e in error_dist]
            values = [e.get('wrong_count', 0) for e in error_dist]
            if any(v > 0 for v in values):
                self.error_chart.plot_bar_chart(
                    labels, values,
                    title="各题错误人数分布",
                    xlabel="题号",
                    ylabel="错误人数"
                )

        self.error_table.setRowCount(len(error_dist))
        self.error_table.setColumnCount(5)
        self.error_table.setHorizontalHeaderLabels(
            ['题号', '题目内容', '考点', '错误人数', '错误率']
        )
        for row, e in enumerate(error_dist):
            total = max(e.get('total_count', 1), 1)
            wrong = e.get('wrong_count', 0)
            rate = f"{wrong / total * 100:.1f}%" if total > 0 else "0%"
            items = [
                QTableWidgetItem(str(e.get('question_no', ''))),
                QTableWidgetItem(str(e.get('content', ''))[:50]),
                QTableWidgetItem(str(e.get('knowledge_point', ''))),
                QTableWidgetItem(str(wrong)),
                QTableWidgetItem(rate)
            ]
            for col, it in enumerate(items):
                it.setTextAlignment(Qt.AlignCenter)
                if col == 4 and wrong / total >= 0.4:
                    it.setForeground(QBrush(QColor('#F44336')))
            self.error_table.setItem(row, 0, items[0])
            self.error_table.setItem(row, 1, items[1])
            self.error_table.setItem(row, 2, items[2])
            self.error_table.setItem(row, 3, items[3])
            self.error_table.setItem(row, 4, items[4])

    def _generate_review_outline(self):
        current_item = self.paper_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择一份已分析的试卷")
            return
        paper_id = current_item.data(Qt.UserRole)
        if paper_id is None:
            QMessageBox.warning(self, "提示", "请选择有效的试卷")
            return

        outline = self.service.generate_review_outline(paper_id)
        html = f"""
        <h2 style='color:#FF5722; text-align:center;'>🎯 {outline.get('paper_name','')} 试卷讲评提纲</h2>
        <p style='color:#666; text-align:center;'>学科：{outline.get('subject','')}</p>
        <hr>
        """
        for section in outline.get('outline', []):
            html += f"<h3 style='color:#1976D2;'>{section.get('title','')}</h3>"
            html += f"<p style='line-height:1.6; padding:0 10px; color:#555;'>{section.get('content','')}</p>"
            items = section.get('items', [])
            if items:
                html += "<ul style='line-height:2; padding-left:30px;'>"
                for it in items:
                    html += f"<li style='margin:5px 0;'>{it}</li>"
                html += "</ul>"
        html += f"""
        <hr>
        <p style='color:#999; text-align:right;'>
            生成时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}
        </p>
        """
        self.review_text.setHtml(html)

    def refresh(self):
        self._load_classes()
        self._load_paper_list()
