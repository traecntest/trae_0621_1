from typing import List, Dict
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

TOOLBAR_TEXT_MAP = {
    'Home': '🏠 重置视图',
    'Back': '⬅️ 上一视图',
    'Forward': '➡️ 下一视图',
    'Pan': '✋ 平移/缩放',
    'Zoom': '🔍 区域缩放',
    'Subplots': '📐 子图设置',
    'Customize': '⚙️ 自定义参数',
    'Save': '💾 保存图片',
    'Reset original view': '重置视图',
    'Back to previous view': '返回上一视图',
    'Forward to next view': '前进到下一视图',
    'Pan axes with left mouse, zoom with right': '左键平移，右键缩放',
    'Zoom to rectangle': '框选区域缩放',
    'Configure subplots': '配置子图参数',
    'Edit axis, curve and image parameters': '编辑坐标轴和曲线参数',
    'Save the figure': '保存当前图表'
}


class ChineseNavigationToolbar(NavigationToolbar):
    def _init_toolbar(self):
        super()._init_toolbar() if hasattr(super(), '_init_toolbar') else None
        self._translate_actions()

    def _translate_actions(self):
        for action in self.actions():
            text = action.text()
            tooltip = action.toolTip()
            if text in TOOLBAR_TEXT_MAP:
                action.setText(TOOLBAR_TEXT_MAP[text])
            for en, zh in TOOLBAR_TEXT_MAP.items():
                if tooltip and en in tooltip:
                    action.setToolTip(zh)
                    break


class ChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar = ChineseNavigationToolbar(self.canvas, self)
        self._apply_chinese_toolbar()

        layout = QVBoxLayout(self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.setContentsMargins(0, 0, 0, 0)

    def _apply_chinese_toolbar(self):
        for action in self.toolbar.actions():
            text = action.text().strip()
            if text in TOOLBAR_TEXT_MAP:
                action.setText(TOOLBAR_TEXT_MAP[text])
            tooltip = action.toolTip()
            for en, zh in TOOLBAR_TEXT_MAP.items():
                if tooltip and en in tooltip:
                    action.setToolTip(zh)
                    break

    def clear(self):
        self.figure.clear()
        self.canvas.draw()

    def plot_line_chart(self, dates: List[str], scores: List[float],
                        title: str = "成绩趋势图", xlabel: str = "考试",
                        ylabel: str = "分数"):
        self.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(dates, scores, marker='o', linewidth=2, markersize=6,
                color='#2196F3', label='成绩')
        ax.axhline(y=60, color='#F44336', linestyle='--', alpha=0.7, label='及格线')
        ax.axhline(y=90, color='#4CAF50', linestyle='--', alpha=0.7, label='优秀线')
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_ylim(0, 105)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        for i, v in enumerate(scores):
            ax.annotate(f'{v}', (dates[i], v), textcoords="offset points",
                        xytext=(0, 10), ha='center', fontsize=9)
        self.figure.tight_layout()
        self.canvas.draw()

    def plot_radar_chart(self, subjects: List[str], scores: List[float],
                         full_scores: List[float] = None,
                         title: str = "学科能力雷达图"):
        self.clear()
        if full_scores is None:
            full_scores = [100] * len(subjects)
        normalized = [s / f * 100 for s, f in zip(scores, full_scores)]

        angles = np.linspace(0, 2 * np.pi, len(subjects), endpoint=False).tolist()
        normalized += normalized[:1]
        angles += angles[:1]

        ax = self.figure.add_subplot(111, polar=True)
        ax.plot(angles, normalized, 'o-', linewidth=2, color='#2196F3')
        ax.fill(angles, normalized, alpha=0.25, color='#2196F3')
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(subjects)
        ax.set_ylim(0, 100)
        ax.set_title(title, fontsize=12, fontweight='bold', pad=20)
        self.figure.tight_layout()
        self.canvas.draw()

    def plot_bar_chart(self, categories: List[str], values: List[float],
                       title: str = "柱状图", xlabel: str = "", ylabel: str = "",
                       colors: List[str] = None):
        self.clear()
        ax = self.figure.add_subplot(111)
        if colors is None:
            colors = ['#2196F3'] * len(categories)
        bars = ax.bar(categories, values, color=colors, alpha=0.8)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3, axis='y')
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)
        self.figure.tight_layout()
        self.canvas.draw()

    def plot_pie_chart(self, labels: List[str], values: List[float],
                       title: str = "饼图"):
        self.clear()
        ax = self.figure.add_subplot(111)
        colors = ['#2196F3', '#4CAF50', '#FF9800', '#F44336', '#9C27B0',
                  '#00BCD4', '#FFEB3B', '#795548']
        wedges, texts, autotexts = ax.pie(
            values, labels=labels, autopct='%1.1f%%',
            startangle=90, colors=colors[:len(labels)],
            textprops={'fontsize': 10}
        )
        ax.set_title(title, fontsize=12, fontweight='bold')
        self.figure.tight_layout()
        self.canvas.draw()

    def plot_histogram(self, scores: List[float], bins: int = 10,
                       title: str = "成绩分布直方图", xlabel: str = "分数段",
                       ylabel: str = "人数"):
        self.clear()
        ax = self.figure.add_subplot(111)
        ranges = [(0, 60), (60, 70), (70, 80), (80, 90), (90, 101)]
        labels = ['<60', '60-69', '70-79', '80-89', '90-100']
        counts = [0] * len(ranges)
        for s in scores:
            for i, (low, high) in enumerate(ranges):
                if low <= s < high:
                    counts[i] += 1
                    break
        colors = ['#F44336', '#FF9800', '#FFEB3B', '#8BC34A', '#4CAF50']
        bars = ax.bar(labels, counts, color=colors, alpha=0.8)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3, axis='y')
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{int(height)}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=10)
        self.figure.tight_layout()
        self.canvas.draw()

    def plot_multi_line(self, data_dict: Dict[str, Dict],
                        title: str = "多学生成绩对比",
                        xlabel: str = "考试", ylabel: str = "分数"):
        self.clear()
        ax = self.figure.add_subplot(111)
        colors = ['#2196F3', '#F44336', '#4CAF50', '#FF9800', '#9C27B0',
                  '#00BCD4', '#795548', '#E91E63']
        for i, (name, d) in enumerate(data_dict.items()):
            ax.plot(d.get('dates', []), d.get('scores', []),
                    marker='o', linewidth=2, markersize=5,
                    color=colors[i % len(colors)], label=name)
        ax.axhline(y=60, color='#9E9E9E', linestyle='--', alpha=0.5)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_ylim(0, 105)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', fontsize=9)
        self.figure.tight_layout()
        self.canvas.draw()
