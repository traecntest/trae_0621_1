from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QStackedWidget, QFrame,
                               QMessageBox, QDialog, QLineEdit, QFormLayout,
                               QDialogButtonBox, QSpinBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QLinearGradient
from ..db.database import DatabaseManager
from ..utils.test_data_generator import TestDataGenerator
from .feedback_page import FeedbackPage
from .grade_page import GradePage
from .paper_page import PaperPage


class NavButton(QPushButton):
    def __init__(self, icon_text, text, parent=None):
        super().__init__(parent)
        self.icon_text = icon_text
        self.setText(f"  {icon_text}  {text}")
        self.setMinimumHeight(48)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                background-color: transparent;
                color: #CFD8DC;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.08);
                color: white;
            }
            QPushButton:checked {
                background-color: rgba(33, 150, 243, 0.3);
                color: white;
                border-left: 3px solid #2196F3;
            }
        """)


class HeaderWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(60)
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)

        title = QLabel("🎓 K12教育AI工作台")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title.setStyleSheet("color: #1976D2;")
        layout.addWidget(title)

        layout.addStretch()

        self.data_btn = QPushButton("📊 生成测试数据")
        self.data_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800; color: white; font-weight: bold;
                border-radius: 4px; padding: 8px 16px;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        layout.addWidget(self.data_btn)

        self.setting_btn = QPushButton("⚙️ 设置")
        self.setting_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B; color: white; font-weight: bold;
                border-radius: 4px; padding: 8px 16px;
            }
            QPushButton:hover { background-color: #455A64; }
        """)
        layout.addWidget(self.setting_btn)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor("#E3F2FD"))
        gradient.setColorAt(1, QColor("#BBDEFB"))
        painter.fillRect(self.rect(), gradient)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("K12教育AI工作台")
        self.resize(1280, 800)
        self.setMinimumSize(1024, 680)

        self.db = DatabaseManager()
        self.db.init_tables()

        self._init_ui()
        self._setup_connections()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.header = HeaderWidget()
        main_layout.addWidget(self.header)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self.nav_frame = QFrame()
        self.nav_frame.setFixedWidth(220)
        self.nav_frame.setStyleSheet("""
            QFrame {
                background-color: #263238;
                border: none;
            }
        """)
        nav_layout = QVBoxLayout(self.nav_frame)
        nav_layout.setContentsMargins(10, 20, 10, 20)
        nav_layout.setSpacing(6)

        nav_title = QLabel("功能导航")
        nav_title.setStyleSheet("color: #90A4AE; font-size: 12px; padding: 5px 10px;")
        nav_layout.addWidget(nav_title)

        self.btn_feedback = NavButton("📝", "课堂反馈")
        self.btn_grade = NavButton("📊", "成绩分析")
        self.btn_paper = NavButton("📄", "试卷分析")

        self.btn_feedback.setChecked(True)

        nav_layout.addWidget(self.btn_feedback)
        nav_layout.addWidget(self.btn_grade)
        nav_layout.addWidget(self.btn_paper)
        nav_layout.addStretch()

        footer = QLabel("v1.0.0  本地数据安全存储")
        footer.setStyleSheet("color: #607D8B; font-size: 10px; padding: 10px; text-align: center;")
        footer.setAlignment(Qt.AlignCenter)
        nav_layout.addWidget(footer)

        body.addWidget(self.nav_frame)

        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("""
            QStackedWidget {
                background-color: #FAFAFA;
            }
        """)

        self.feedback_page = FeedbackPage()
        self.grade_page = GradePage()
        self.paper_page = PaperPage()

        self.content_stack.addWidget(self.feedback_page)
        self.content_stack.addWidget(self.grade_page)
        self.content_stack.addWidget(self.paper_page)

        body.addWidget(self.content_stack, 1)

        main_layout.addLayout(body, 1)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #FAFAFA;
            }
            QGroupBox {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                margin-top: 12px;
                font-weight: bold;
                color: #37474F;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #455A64;
            }
            QPushButton {
                font-family: "Microsoft YaHei";
            }
            QLabel {
                font-family: "Microsoft YaHei";
            }
            QComboBox, QLineEdit, QSpinBox, QDateEdit, QTextEdit, QTableWidget, QListWidget {
                font-family: "Microsoft YaHei";
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: white;
                selection-background-color: #2196F3;
            }
            QComboBox:focus, QLineEdit:focus, QSpinBox:focus,
            QDateEdit:focus, QTextEdit:focus, QTableWidget:focus {
                border: 1px solid #2196F3;
            }
            QTableWidget {
                gridline-color: #E0E0E0;
            }
            QHeaderView::section {
                background-color: #ECEFF1;
                padding: 6px;
                border: none;
                border-right: 1px solid #E0E0E0;
                border-bottom: 1px solid #E0E0E0;
                font-weight: bold;
                color: #455A64;
            }
            QScrollBar:vertical {
                border: none;
                background: #F5F5F5;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background: #BDBDBD;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #9E9E9E;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QTabWidget::pane {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                background: white;
                top: -1px;
            }
            QTabBar::tab {
                background: #ECEFF1;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                color: #607D8B;
            }
            QTabBar::tab:selected {
                background: white;
                color: #1976D2;
                font-weight: bold;
                border: 1px solid #E0E0E0;
                border-bottom: 1px solid white;
            }
        """)

    def _setup_connections(self):
        self.btn_feedback.clicked.connect(lambda: self._switch_page(0))
        self.btn_grade.clicked.connect(lambda: self._switch_page(1))
        self.btn_paper.clicked.connect(lambda: self._switch_page(2))

        self.header.data_btn.clicked.connect(self._generate_test_data)
        self.header.setting_btn.clicked.connect(self._show_settings)

    def _switch_page(self, index):
        self.btn_feedback.setChecked(index == 0)
        self.btn_grade.setChecked(index == 1)
        self.btn_paper.setChecked(index == 2)
        self.content_stack.setCurrentIndex(index)

        if index == 0:
            self.feedback_page.refresh()
        elif index == 1:
            self.grade_page.refresh()
        elif index == 2:
            self.paper_page.refresh()

    def _generate_test_data(self):
        dialog = TestDataDialog(self)
        if dialog.exec() == QDialog.Accepted:
            try:
                gen = TestDataGenerator()
                result = gen.generate_all(
                    class_count=dialog.class_count,
                    students_per_class=dialog.student_count,
                    exams_per_class=dialog.exam_count,
                    feedbacks_per_student=dialog.feedback_count,
                    papers_per_class=dialog.paper_count
                )
                QMessageBox.information(
                    self, "成功",
                    f"测试数据生成成功！\n\n"
                    f"班级数：{len(result['classes'])}\n"
                    f"学生总数：{result['total_students']}\n"
                    f"考试数：{result['total_exams']}\n"
                    f"试卷数：{result['total_papers']}"
                )
                self._switch_page(self.content_stack.currentIndex())
            except Exception as e:
                QMessageBox.critical(self, "错误", f"生成测试数据失败：{str(e)}")

    def _show_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()


class TestDataDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("生成测试数据")
        self.setMinimumWidth(360)
        self.class_count = 3
        self.student_count = 25
        self.exam_count = 3
        self.feedback_count = 2
        self.paper_count = 2
        self._init_ui()

    def _init_ui(self):
        layout = QFormLayout(self)

        self.class_spin = QSpinBox()
        self.class_spin.setRange(1, 10)
        self.class_spin.setValue(3)
        layout.addRow("班级数量：", self.class_spin)

        self.student_spin = QSpinBox()
        self.student_spin.setRange(5, 60)
        self.student_spin.setValue(25)
        layout.addRow("每班学生数：", self.student_spin)

        self.exam_spin = QSpinBox()
        self.exam_spin.setRange(1, 10)
        self.exam_spin.setValue(3)
        layout.addRow("每班考试数：", self.exam_spin)

        self.feedback_spin = QSpinBox()
        self.feedback_spin.setRange(1, 10)
        self.feedback_spin.setValue(2)
        layout.addRow("每生反馈数：", self.feedback_spin)

        self.paper_spin = QSpinBox()
        self.paper_spin.setRange(1, 10)
        self.paper_spin.setValue(2)
        layout.addRow("每班试卷数：", self.paper_spin)

        tip = QLabel("⚠️ 生成的数据将存入本地数据库，可重复生成。")
        tip.setStyleSheet("color: #FF9800; font-size: 11px;")
        layout.addRow(tip)

        btns = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _on_ok(self):
        self.class_count = self.class_spin.value()
        self.student_count = self.student_spin.value()
        self.exam_count = self.exam_spin.value()
        self.feedback_count = self.feedback_spin.value()
        self.paper_count = self.paper_spin.value()
        self.accept()


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统设置")
        self.setMinimumWidth(400)
        self._init_ui()

    def _init_ui(self):
        layout = QFormLayout(self)

        tip = QLabel("💡 填写阿里云百炼API Key后，将启用真实AI生成。\n留空则使用内置模拟数据（功能可用）。")
        tip.setStyleSheet("color: #1976D2; font-size: 11px; padding: 5px;")
        tip.setWordWrap(True)
        layout.addRow(tip)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("sk-xxxxxxxxxxxxxxxxxxxxxxxx")
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        layout.addRow("API Key：", self.api_key_edit)

        self.endpoint_edit = QLineEdit()
        self.endpoint_edit.setPlaceholderText("https://dashscope.aliyuncs.com/...")
        layout.addRow("Endpoint（可选）：", self.endpoint_edit)

        db_path = DatabaseManager.get_db_path()
        db_label = QLabel(db_path)
        db_label.setStyleSheet("color: #666; font-size: 11px;")
        db_label.setWordWrap(True)
        layout.addRow("数据库路径：", db_label)

        btns = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        btns.accepted.connect(self._on_save)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _on_save(self):
        api_key = self.api_key_edit.text().strip()
        endpoint = self.endpoint_edit.text().strip()

        from ..services.llm_service import BailianService
        from ..services.feedback_service import FeedbackService
        from ..services.grade_service import GradeService
        from ..services.paper_service import PaperService

        BailianService().set_config(api_key, endpoint)

        QMessageBox.information(self, "成功", "设置已保存！")
        self.accept()
