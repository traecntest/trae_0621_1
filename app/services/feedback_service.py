from typing import List, Dict
from ..db.dao import StudentDAO, FeedbackDAO, LearningRecordDAO, ExamScoreDAO
from .llm_service import BailianService


class FeedbackService:
    def __init__(self):
        self.student_dao = StudentDAO()
        self.feedback_dao = FeedbackDAO()
        self.learning_dao = LearningRecordDAO()
        self.score_dao = ExamScoreDAO()
        self.llm = BailianService()

    def set_llm_config(self, api_key: str, endpoint: str = ""):
        self.llm.set_config(api_key, endpoint)

    def get_students_by_class(self, class_id: int) -> List[Dict]:
        return self.student_dao.get_by_class(class_id)

    def _get_student_learning_history(self, student_id: int) -> List[Dict]:
        records = self.learning_dao.get_by_student(student_id, limit=10)
        scores = self.score_dao.get_by_student(student_id)
        history = []
        for s in scores:
            history.append({
                "type": "exam",
                "subject": s.get("subject", ""),
                "score": s.get("score", 0),
                "exam_name": s.get("exam_name", ""),
                "date": s.get("exam_date", "")
            })
        history.extend(records)
        return history

    def generate_feedbacks(self, student_ids: List[int], class_id: int,
                           classroom_performance: str = "",
                           feedback_count: int = 10) -> Dict[int, List[str]]:
        results = {}
        for sid in student_ids:
            student = self.student_dao.get_by_id(sid)
            if not student:
                continue
            history = self._get_student_learning_history(sid)
            feedbacks = self.llm.generate_feedback(
                student_info=student,
                learning_history=history,
                classroom_performance=classroom_performance,
                count=feedback_count
            )
            results[sid] = feedbacks
        return results

    def save_feedback(self, student_id: int, class_id: int,
                      content: str, category: str = "课堂反馈") -> int:
        return self.feedback_dao.create(student_id, class_id, content, category)

    def batch_save_feedbacks(self, feedbacks_data: List[Dict]) -> List[int]:
        ids = []
        for data in feedbacks_data:
            fid = self.feedback_dao.create(
                data["student_id"],
                data["class_id"],
                data["content"],
                data.get("category", "课堂反馈")
            )
            ids.append(fid)
        return ids

    def get_class_feedbacks(self, class_id: int) -> List[Dict]:
        return self.feedback_dao.get_by_class(class_id)

    def get_student_feedbacks(self, student_id: int, limit: int = 10) -> List[Dict]:
        return self.feedback_dao.get_by_student(student_id, limit)
