import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from app.db.database import DatabaseManager
from app.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    app.setApplicationName("K12教育AI工作台")
    app.setOrganizationName("EDU Workbench")

    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    db = DatabaseManager()
    db.init_tables()

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
