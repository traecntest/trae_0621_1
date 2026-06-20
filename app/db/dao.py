from .database import DatabaseManager


class ClassDAO:
    def __init__(self):
        self.db = DatabaseManager()

    def create(self, name, grade=None, subject=None, teacher=None):
        now = self.db.now()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO classes (name, grade, subject, teacher, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (name, grade, subject, teacher, now, now)
            )
            return cursor.lastrowid

    def get_all(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM classes ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_by_id(self, class_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM classes WHERE id = ?", (class_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update(self, class_id, **kwargs):
        kwargs['updated_at'] = self.db.now()
        fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [class_id]
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE classes SET {fields} WHERE id = ?", values)
            return cursor.rowcount > 0

    def delete(self, class_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM classes WHERE id = ?", (class_id,))
            return cursor.rowcount > 0


class StudentDAO:
    def __init__(self):
        self.db = DatabaseManager()

    def create(self, class_id, name, gender=None, birthday=None, student_no=None,
               guardian_name=None, guardian_phone=None, notes=None):
        now = self.db.now()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO students (class_id, name, gender, birthday, student_no,
                   guardian_name, guardian_phone, notes, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (class_id, name, gender, birthday, student_no,
                 guardian_name, guardian_phone, notes, now, now)
            )
            return cursor.lastrowid

    def get_by_class(self, class_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE class_id = ? ORDER BY name", (class_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_by_id(self, student_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update(self, student_id, **kwargs):
        kwargs['updated_at'] = self.db.now()
        fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [student_id]
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE students SET {fields} WHERE id = ?", values)
            return cursor.rowcount > 0

    def delete(self, student_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
            return cursor.rowcount > 0


class FeedbackDAO:
    def __init__(self):
        self.db = DatabaseManager()

    def create(self, student_id, class_id, content, category=None):
        now = self.db.now()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO feedback_records (student_id, class_id, content, category, generated_at) VALUES (?, ?, ?, ?, ?)",
                (student_id, class_id, content, category, now)
            )
            return cursor.lastrowid

    def get_by_student(self, student_id, limit=10):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM feedback_records WHERE student_id = ? ORDER BY generated_at DESC LIMIT ?",
                (student_id, limit)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_by_class(self, class_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT fr.*, s.name as student_name FROM feedback_records fr "
                "JOIN students s ON fr.student_id = s.id "
                "WHERE fr.class_id = ? ORDER BY fr.generated_at DESC",
                (class_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def delete(self, feedback_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM feedback_records WHERE id = ?", (feedback_id,))
            return cursor.rowcount > 0


class ExamDAO:
    def __init__(self):
        self.db = DatabaseManager()

    def create(self, class_id, name, exam_date=None, subjects=None):
        now = self.db.now()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO exams (class_id, name, exam_date, subjects, created_at) VALUES (?, ?, ?, ?, ?)",
                (class_id, name, exam_date, subjects, now)
            )
            return cursor.lastrowid

    def get_by_class(self, class_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exams WHERE class_id = ? ORDER BY exam_date DESC", (class_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_by_id(self, exam_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exams WHERE id = ?", (exam_id,))
            row = cursor.fetchone()
            return dict(row) if row else None


class ExamScoreDAO:
    def __init__(self):
        self.db = DatabaseManager()

    def create(self, exam_id, student_id, subject, score, full_score=100, rank=None):
        now = self.db.now()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO exam_scores (exam_id, student_id, subject, score, full_score, rank, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (exam_id, student_id, subject, score, full_score, rank, now)
            )
            return cursor.lastrowid

    def batch_create(self, scores):
        now = self.db.now()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            for s in scores:
                cursor.execute(
                    "INSERT INTO exam_scores (exam_id, student_id, subject, score, full_score, rank, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (s['exam_id'], s['student_id'], s['subject'], s['score'],
                     s.get('full_score', 100), s.get('rank'), now)
                )

    def get_by_exam(self, exam_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT es.*, s.name as student_name FROM exam_scores es "
                "JOIN students s ON es.student_id = s.id "
                "WHERE es.exam_id = ? ORDER BY s.name",
                (exam_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_by_student(self, student_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT es.*, e.name as exam_name, e.exam_date FROM exam_scores es "
                "JOIN exams e ON es.exam_id = e.id "
                "WHERE es.student_id = ? ORDER BY e.exam_date DESC",
                (student_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_student_subject_scores(self, student_id, subject):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT es.score, e.name as exam_name, e.exam_date FROM exam_scores es "
                "JOIN exams e ON es.exam_id = e.id "
                "WHERE es.student_id = ? AND es.subject = ? ORDER BY e.exam_date",
                (student_id, subject)
            )
            return [dict(row) for row in cursor.fetchall()]


class PaperDAO:
    def __init__(self):
        self.db = DatabaseManager()

    def create(self, name, subject, class_id=None, total_score=100, file_path=None):
        now = self.db.now()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO papers (class_id, name, subject, total_score, file_path, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (class_id, name, subject, total_score, file_path, now)
            )
            return cursor.lastrowid

    def get_all(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM papers ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_by_id(self, paper_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM papers WHERE id = ?", (paper_id,))
            row = cursor.fetchone()
            return dict(row) if row else None


class PaperQuestionDAO:
    def __init__(self):
        self.db = DatabaseManager()

    def create(self, paper_id, question_no, content=None, score=0,
               knowledge_point=None, difficulty=0.5, common_mistakes=None):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO paper_questions (paper_id, question_no, content, score,
                   knowledge_point, difficulty, common_mistakes) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (paper_id, question_no, content, score, knowledge_point, difficulty, common_mistakes)
            )
            return cursor.lastrowid

    def batch_create(self, questions):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            for q in questions:
                cursor.execute(
                    """INSERT INTO paper_questions (paper_id, question_no, content, score,
                       knowledge_point, difficulty, common_mistakes) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (q['paper_id'], q['question_no'], q.get('content'), q.get('score', 0),
                     q.get('knowledge_point'), q.get('difficulty', 0.5), q.get('common_mistakes'))
                )

    def get_by_paper(self, paper_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM paper_questions WHERE paper_id = ? ORDER BY question_no", (paper_id,))
            return [dict(row) for row in cursor.fetchall()]


class PaperAnswerDAO:
    def __init__(self):
        self.db = DatabaseManager()

    def create(self, question_id, student_id, is_correct=0, student_answer=None, score=0):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO paper_answers (question_id, student_id, is_correct, student_answer, score) VALUES (?, ?, ?, ?, ?)",
                (question_id, student_id, is_correct, student_answer, score)
            )
            return cursor.lastrowid

    def get_wrong_answers_by_paper(self, paper_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT pa.*, pq.question_no, pq.content, pq.knowledge_point, s.name as student_name
                   FROM paper_answers pa
                   JOIN paper_questions pq ON pa.question_id = pq.id
                   JOIN students s ON pa.student_id = s.id
                   WHERE pq.paper_id = ? AND pa.is_correct = 0""",
                (paper_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_error_distribution(self, paper_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT pq.id, pq.question_no, pq.content, pq.knowledge_point, pq.score,
                   COUNT(CASE WHEN pa.is_correct = 0 THEN 1 END) as wrong_count,
                   COUNT(*) as total_count
                   FROM paper_questions pq
                   LEFT JOIN paper_answers pa ON pq.id = pa.question_id
                   WHERE pq.paper_id = ?
                   GROUP BY pq.id
                   ORDER BY wrong_count DESC""",
                (paper_id,)
            )
            return [dict(row) for row in cursor.fetchall()]


class LearningRecordDAO:
    def __init__(self):
        self.db = DatabaseManager()

    def create(self, student_id, record_type, content=None, record_date=None):
        now = self.db.now()
        if record_date is None:
            record_date = self.db.today()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO learning_records (student_id, type, content, record_date, created_at) VALUES (?, ?, ?, ?, ?)",
                (student_id, record_type, content, record_date, now)
            )
            return cursor.lastrowid

    def get_by_student(self, student_id, limit=20):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM learning_records WHERE student_id = ? ORDER BY record_date DESC LIMIT ?",
                (student_id, limit)
            )
            return [dict(row) for row in cursor.fetchall()]
