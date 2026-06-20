import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime


class DatabaseManager:
    _instance = None
    _db_path = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def set_db_path(cls, path):
        cls._db_path = path

    @classmethod
    def get_db_path(cls):
        if cls._db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            cls._db_path = os.path.join(data_dir, "edu_workbench.db")
        return cls._db_path

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.get_db_path())
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def init_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS classes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    grade TEXT,
                    subject TEXT,
                    teacher TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    gender TEXT,
                    birthday TEXT,
                    student_no TEXT,
                    guardian_name TEXT,
                    guardian_phone TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS feedback_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    class_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT,
                    generated_at TEXT NOT NULL,
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS exams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    exam_date TEXT,
                    subjects TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS exam_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exam_id INTEGER NOT NULL,
                    student_id INTEGER NOT NULL,
                    subject TEXT NOT NULL,
                    score REAL NOT NULL,
                    full_score REAL DEFAULT 100,
                    rank INTEGER,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS papers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_id INTEGER,
                    name TEXT NOT NULL,
                    subject TEXT,
                    total_score REAL DEFAULT 100,
                    file_path TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS paper_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paper_id INTEGER NOT NULL,
                    question_no TEXT NOT NULL,
                    content TEXT,
                    score REAL DEFAULT 0,
                    knowledge_point TEXT,
                    difficulty REAL DEFAULT 0.5,
                    common_mistakes TEXT,
                    FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS paper_answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER NOT NULL,
                    student_id INTEGER NOT NULL,
                    is_correct INTEGER DEFAULT 0,
                    student_answer TEXT,
                    score REAL DEFAULT 0,
                    FOREIGN KEY (question_id) REFERENCES paper_questions(id) ON DELETE CASCADE,
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS learning_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    content TEXT,
                    record_date TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
                );
            """)

    def now(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def today(self):
        return datetime.now().strftime("%Y-%m-%d")
