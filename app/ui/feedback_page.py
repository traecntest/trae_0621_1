from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QComboBox, QListWidget, QListWidgetItem,
                               QTextEdit, QSplitter, QMessageBox, QSpinBox,
                               QGroupBox, QCheckBox, QScrollArea)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from ..db.dao import ClassDAO, StudentDAO
from ..services.feedback_service import FeedbackService


class GenerateFeedbackThread(QThread):
    finished_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, service, student_ids, class_id, performance, count):
        super().__init__()
        self.service = service
        self.student_ids = student_ids
        self.class_id = class_id
        self.performance = performance
        self.count = count

    def run(self):
        try:
            result = self.service.generate_feedbacks(
                self.student_ids, self.class_id,
                self.performance, self.count
            )
            self.finished_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))


class FeedbackPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.class_dao = ClassDAO()
        self.student_dao = StudentDAO()
        self.service = FeedbackService()
        self.current_class_id = None
        self.current_students = []
        self.generated_feedbacks = {}
        self.generate_thread = None
        self._init_ui()
        self._load_classes()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("📝 课堂反馈生成")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #1976D2; padding: 5px;")
        main_layout.addWidget(title)

        control_group = QGroupBox("操作区")
        control_layout = QVBoxLayout(control_group)

        class_row = QHBoxLayout()
        class_row.addWidget(QLabel("选择班级:"))
        self.class_combo = QComboBox()
        self.class_combo.setMinimumWidth(250)
        self.class_combo.currentIndexChanged.connect(self._on_class_changed)
        class_row.addWidget(self.class_combo)
        class_row.addStretch()
        control_layout.addLayout(class_row)

        perf_row = QHBoxLayout()
        perf_row.addWidget(QLabel("整体课堂表现:"))
        self.perf_combo = QComboBox()
        self.perf_combo.addItems(["优秀", "良好", "一般", "有待提高"])
        self.perf_combo.setMinimumWidth(150)
        perf_row.addWidget(self.perf_combo)
        perf_row.addSpacing(20)
        perf_row.addWidget(QLabel("生成反馈条数:"))
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 20)
        self.count_spin.setValue(10)
        perf_row.addWidget(self.count_spin)
        perf_row.addStretch()
        control_layout.addLayout(perf_row)

        btn_row = QHBoxLayout()
        self.select_all_btn = QPushButton("全选学生")
        self.select_all_btn.clicked.connect(self._select_all_students)
        self.unselect_all_btn = QPushButton("取消全选")
        self.unselect_all_btn.clicked.connect(self._unselect_all_students)
        self.generate_btn = QPushButton("🚀 批量生成反馈")
        self.generate_btn.setMinimumHeight(36)
        self.generate_btn.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; font-weight: bold; "
            "border-radius: 4px; padding: 6px 20px; }"
            "QPushButton:hover { background-color: #1976D2; }"
            "QPushButton:disabled { background-color: #BDBDBD; }"
        )
        self.generate_btn.clicked.connect(self._generate_feedbacks)
        btn_row.addWidget(self.select_all_btn)
        btn_row.addWidget(self.unselect_all_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.generate_btn)
        control_layout.addLayout(btn_row)

        main_layout.addWidget(control_group)

        splitter = QSplitter(Qt.Horizontal)

        student_group = QGroupBox("学生名单")
        student_layout = QVBoxLayout(student_group)
        self.student_list = QListWidget()
        self.student_list.setSelectionMode(QListWidget.NoSelection)
        student_layout.addWidget(self.student_list)
        splitter.addWidget(student_group)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        result_group = QGroupBox("生成的反馈文案")
        result_layout = QVBoxLayout(result_group)

        select_row2 = QHBoxLayout()
        select_row2.addWidget(QLabel("选择学生查看反馈:"))
        self.result_student_combo = QComboBox()
        self.result_student_combo.currentIndexChanged.connect(self._on_student_selected)
        select_row2.addWidget(self.result_student_combo, 1)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #1976D2; font-weight: bold;")
        select_row2.addWidget(self.status_label)
        result_layout.addLayout(select_row2)

        self.feedback_scroll = QScrollArea()
        self.feedback_scroll.setWidgetResizable(True)
        self.feedback_container = QWidget()
        self.feedback_container_layout = QVBoxLayout(self.feedback_container)
        self.feedback_container_layout.setSpacing(8)
        self.feedback_scroll.setWidget(self.feedback_container)
        result_layout.addWidget(self.feedback_scroll)

        save_row = QHBoxLayout()
        self.save_all_btn = QPushButton("💾 保存当前学生所有反馈")
        self.save_all_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; "
            "border-radius: 4px; padding: 6px 20px; }"
            "QPushButton:hover { background-color: #388E3C; }"
        )
        self.save_all_btn.clicked.connect(self._save_current_student_feedbacks)
        save_row.addStretch()
        save_row.addWidget(self.save_all_btn)
        result_layout.addLayout(save_row)

        right_layout.addWidget(result_group)

        splitter.addWidget(right_widget)
        splitter.setSizes([350, 650])
        main_layout.addWidget(splitter, 1)

    def _load_classes(self):
        self.class_combo.blockSignals(True)
        self.class_combo.clear()
        classes = self.class_dao.get_all()
        for c in classes:
            self.class_combo.addItem(
                f"{c['name']}（{c.get('teacher', '')}）", c['id']
            )
        if not classes:
            self.class_combo.addItem("暂无班级，请先生成测试数据", None)
        self.class_combo.blockSignals(False)
        if self.class_combo.count() > 0:
            self._on_class_changed(0)

    def _on_class_changed(self, index):
        if index < 0:
            return
        class_id = self.class_combo.currentData()
        self.current_class_id = class_id

        self.student_list.clear()
        self.current_students = []
        self.generated_feedbacks = {}
        self.status_label.setText("")

        self.result_student_combo.blockSignals(True)
        self.result_student_combo.clear()

        if class_id is not None:
            students = self.student_dao.get_by_class(class_id)
            self.current_students = students
            for s in students:
                item = QListWidgetItem()
                checkbox = QCheckBox(f"{s['name']}（{s.get('gender', '')}）")
                checkbox.setChecked(True)
                checkbox.stateChanged.connect(self._update_status)
                item.setSizeHint(checkbox.sizeHint())
                self.student_list.addItem(item)
                self.student_list.setItemWidget(item, checkbox)
                self.result_student_combo.addItem(s['name'], s['id'])

        self.result_student_combo.blockSignals(False)
        self._clear_feedback_container()

        if self.result_student_combo.count() > 0:
            self.result_student_combo.setCurrentIndex(0)
            self._on_student_selected(0)

        self._update_status()

    def _select_all_students(self):
        for i in range(self.student_list.count()):
            item = self.student_list.item(i)
            cb = self.student_list.itemWidget(item)
            if cb:
                cb.blockSignals(True)
                cb.setChecked(True)
                cb.blockSignals(False)
        self._update_status()

    def _unselect_all_students(self):
        for i in range(self.student_list.count()):
            item = self.student_list.item(i)
            cb = self.student_list.itemWidget(item)
            if cb:
                cb.blockSignals(True)
                cb.setChecked(False)
                cb.blockSignals(False)
        self._update_status()

    def _get_selected_student_ids(self):
        ids = []
        for i in range(self.student_list.count()):
            item = self.student_list.item(i)
            cb = self.student_list.itemWidget(item)
            if cb and cb.isChecked():
                if i < len(self.current_students):
                    ids.append(self.current_students[i]['id'])
        return ids

    def _update_status(self):
        selected = len(self._get_selected_student_ids())
        total = len(self.current_students)
        generated = len(self.generated_feedbacks)
        parts = []
        if total > 0:
            parts.append(f"已选 {selected}/{total} 人")
        if generated > 0:
            parts.append(f"已生成 {generated} 人反馈")
        self.status_label.setText("  |  ".join(parts))

    def _generate_feedbacks(self):
        if self.current_class_id is None:
            QMessageBox.warning(self, "提示", "请先选择一个班级")
            return

        student_ids = self._get_selected_student_ids()
        if not student_ids:
            QMessageBox.warning(self, "提示", "请至少勾选一名学生")
            return

        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("⏳ 正在生成反馈...")

        self.generate_thread = GenerateFeedbackThread(
            self.service, student_ids, self.current_class_id,
            self.perf_combo.currentText(),
            self.count_spin.value()
        )
        self.generate_thread.finished_signal.connect(self._on_feedback_generated)
        self.generate_thread.error_signal.connect(self._on_feedback_error)
        self.generate_thread.start()

    def _on_feedback_generated(self, result):
        self.generated_feedbacks = result
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("🚀 批量生成反馈")
        self._update_status()

        target_index = -1
        target_sid = None
        for i in range(self.result_student_combo.count()):
            sid = self.result_student_combo.itemData(i)
            if sid in result:
                target_index = i
                target_sid = sid
                break

        QMessageBox.information(
            self, "成功",
            f"已为 {len(result)} 名学生生成反馈，每人 {self.count_spin.value()} 条。\n"
            f"请在右侧下拉框选择学生查看和微调。"
        )

        if target_sid is not None and target_index >= 0:
            self.result_student_combo.blockSignals(True)
            self.result_student_combo.setCurrentIndex(target_index)
            self.result_student_combo.blockSignals(False)
            self._render_feedbacks(target_sid)

    def _on_feedback_error(self, error_msg):
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("🚀 批量生成反馈")
        QMessageBox.critical(self, "错误", f"生成反馈失败：{error_msg}")

    def _clear_feedback_container(self):
        while self.feedback_container_layout.count():
            item = self.feedback_container_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

    def _on_student_selected(self, index):
        if index < 0:
            return
        student_id = self.result_student_combo.itemData(index)
        if student_id is None:
            return
        self._render_feedbacks(student_id)

    def _render_feedbacks(self, student_id):
        self._clear_feedback_container()

        if student_id not in self.generated_feedbacks:
            student_name = ""
            for i in range(self.result_student_combo.count()):
                if self.result_student_combo.itemData(i) == student_id:
                    student_name = self.result_student_combo.itemText(i)
                    break
            tip = QLabel(
                f"📌 学生【{student_name}】暂无生成的反馈。\n\n"
                f"请先在左侧勾选学生，然后点击上方的 【🚀 批量生成反馈】 按钮。"
            )
            tip.setAlignment(Qt.AlignCenter)
            tip.setStyleSheet(
                "color: #666; padding: 30px; font-size: 13px; line-height: 1.8;"
            )
            tip.setWordWrap(True)
            self.feedback_container_layout.addWidget(tip)
            self.feedback_container_layout.addStretch()
            return

        feedbacks = self.generated_feedbacks[student_id]
        self._feedback_editors = []
        for i, fb in enumerate(feedbacks):
            fb_group = QGroupBox(f"反馈方案 {i+1}")
            fb_layout = QVBoxLayout(fb_group)

            text_edit = QTextEdit(fb)
            text_edit.setPlainText(fb)
            text_edit.setMinimumHeight(90)
            self._feedback_editors.append(text_edit)
            fb_layout.addWidget(text_edit)

            btn_row = QHBoxLayout()
            save_btn = QPushButton("💾 保存此条")
            save_btn.setStyleSheet(
                "QPushButton { background-color: #009688; color: white; "
                "padding: 4px 12px; border-radius: 3px; }"
                "QPushButton:hover { background-color: #00796B; }"
            )
            save_btn.clicked.connect(
                lambda checked=False, sid=student_id, te=text_edit:
                    self._save_single_feedback(sid, te)
            )
            btn_row.addStretch()
            btn_row.addWidget(save_btn)
            fb_layout.addLayout(btn_row)

            self.feedback_container_layout.addWidget(fb_group)
        self.feedback_container_layout.addStretch()

    def _save_single_feedback(self, student_id, text_edit):
        if self.current_class_id is None:
            QMessageBox.warning(self, "提示", "请先选择班级")
            return
        content = text_edit.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "提示", "反馈内容不能为空")
            return
        self.service.save_feedback(student_id, self.current_class_id, content)
        QMessageBox.information(self, "成功", "反馈已保存！")

    def _save_current_student_feedbacks(self):
        if self.current_class_id is None:
            QMessageBox.warning(self, "提示", "请先选择班级")
            return

        student_id = self.result_student_combo.currentData()
        if student_id is None:
            QMessageBox.warning(self, "提示", "请先选择学生")
            return

        if student_id not in self.generated_feedbacks:
            QMessageBox.warning(self, "提示", "当前学生没有生成的反馈可保存")
            return

        count = 0
        if hasattr(self, '_feedback_editors'):
            for te in self._feedback_editors:
                content = te.toPlainText().strip()
                if content:
                    self.service.save_feedback(student_id, self.current_class_id, content)
                    count += 1

        if count > 0:
            QMessageBox.information(self, "成功", f"已为当前学生保存 {count} 条反馈！")
        else:
            QMessageBox.warning(self, "提示", "没有可保存的反馈内容")

    def refresh(self):
        self._load_classes()
