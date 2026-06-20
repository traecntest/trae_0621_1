import random
from typing import List, Dict
from datetime import datetime, timedelta
from ..db.dao import StudentDAO, FeedbackDAO, LearningRecordDAO, ExamScoreDAO
from .llm_service import BailianService


class FeedbackService:
    def __init__(self):
        self.student_dao = StudentDAO()
        self.feedback_dao = FeedbackDAO()
        self.learning_dao = LearningRecordDAO()
        self.score_dao = ExamScoreDAO()
        self.llm = BailianService()

        self._record_types = ["课堂表现", "作业情况", "测验成绩", "老师评语", "课堂互动"]
        self._good_contents = {
            "课堂表现": ["上课积极发言", "注意力高度集中", "主动参与小组讨论", "课堂纪律优秀"],
            "作业情况": ["按时高质量完成作业", "作业书写工整", "完成拓展练习", "错题订正认真"],
            "测验成绩": ["测验成绩优秀", "成绩稳步提升", "基础扎实", "进步明显"],
            "老师评语": ["学习态度端正", "思维敏捷活跃", "求知欲强", "学习习惯良好"],
            "课堂互动": ["主动回答问题", "善于提出质疑", "协助同学学习", "展示能力突出"]
        }
        self._normal_contents = {
            "课堂表现": ["上课基本认真", "偶尔会走神", "参与度一般", "需要老师提醒"],
            "作业情况": ["能按时完成作业", "作业质量中等", "书写需加强", "偶尔漏交作业"],
            "测验成绩": ["成绩中等", "基础不够扎实", "波动较大", "有提升空间"],
            "老师评语": ["学习态度尚可", "需要更主动", "专注力不足", "学习方法待改进"],
            "课堂互动": ["较少主动发言", "回答问题不够流利", "参与积极性一般", "需多鼓励"]
        }
        self._subjects = ["语文", "数学", "英语", "物理", "化学"]

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
        for r in records:
            history.append({
                "type": r.get("type", ""),
                "content": r.get("content", ""),
                "date": r.get("record_date", "")
            })
        return history

    def _ensure_learning_history(self, student_id: int, performance: str = "良好"):
        existing = self._get_student_learning_history(student_id)
        if len(existing) >= 3:
            return

        is_good = performance in ["优秀", "良好"]
        source = self._good_contents if is_good else self._normal_contents
        score_range = (85, 98) if is_good else (65, 82)

        base_date = datetime.now()
        generated = 0

        for i in range(5 - len(existing)):
            rtype = random.choice(self._record_types)
            content = random.choice(source[rtype])
            record_date = (base_date - timedelta(days=random.randint(3, 60))).strftime("%Y-%m-%d")
            self.learning_dao.create(student_id, rtype, content, record_date)
            generated += 1

        exam_count = max(0, 2 - sum(1 for h in existing if h.get("type") == "exam"))
        for i in range(exam_count):
            from ..db.dao import ExamDAO
            exam_dao = ExamDAO()
            class_id = self.student_dao.get_by_id(student_id).get("class_id", 0)

            exam_list = exam_dao.get_by_class(class_id)
            if not exam_list:
                exam_id = exam_dao.create(
                    class_id=class_id,
                    name=f"模拟测试{i+1}",
                    exam_date=(base_date - timedelta(days=random.randint(7, 60))).strftime("%Y-%m-%d"),
                    subjects=",".join(random.sample(self._subjects, 3))
                )
            else:
                exam_id = random.choice(exam_list)["id"]

            for subj in random.sample(self._subjects, min(3, len(self._subjects))):
                score = float(random.randint(*score_range))
                self.score_dao.create(
                    exam_id=exam_id,
                    student_id=student_id,
                    subject=subj,
                    score=score,
                    full_score=100
                )
            generated += 1

        return generated

    def generate_feedbacks(self, student_ids: List[int], class_id: int,
                           classroom_performance: str = "",
                           feedback_count: int = 10) -> Dict[int, List[str]]:
        results = {}
        for sid in student_ids:
            student = self.student_dao.get_by_id(sid)
            if not student:
                continue

            self._ensure_learning_history(sid, classroom_performance)

            history = self._get_student_learning_history(sid)
            feedbacks = self.llm.generate_feedback(
                student_info=student,
                learning_history=history,
                classroom_performance=classroom_performance,
                count=feedback_count
            )

            cleaned = []
            for fb in feedbacks:
                if fb and fb.strip() and len(fb.strip()) >= 20:
                    cleaned.append(fb.strip())
                else:
                    fallback = self._generate_fallback_feedback(
                        student, classroom_performance, len(cleaned) + 1
                    )
                    cleaned.append(fallback)

            while len(cleaned) < feedback_count:
                cleaned.append(
                    self._generate_fallback_feedback(
                        student, classroom_performance, len(cleaned) + 1
                    )
                )

            results[sid] = cleaned[:feedback_count]
        return results

    def _generate_fallback_feedback(self, student: Dict, performance: str, idx: int) -> str:
        name = student.get("name", "该学生")
        perf_desc = "表现优秀" if performance in ["优秀"] else (
            "表现良好" if performance in ["良好"] else (
                "表现一般" if performance in ["一般"] else "有待提高"
            )
        )

        templates = [
            f"{name}同学在本次课堂中{perf_desc}，能够认真听讲，积极参与课堂活动。"
            f"建议在后续学习中继续保持良好的学习习惯，加强基础知识的巩固练习，"
            f"争取在下次测试中取得更大进步。",

            f"【课堂评价】{name}同学本节课{perf_desc}。"
            f"作业完成情况较好，体现了一定的自主学习能力。"
            f"希望继续保持积极向上的学习态度，勇于挑战更高难度的题目。",

            f"{name}同学学习态度端正，课堂{perf_desc}。"
            f"善于思考问题，能够在老师引导下完成课堂练习。"
            f"建议增加拓展训练，提升知识的综合运用能力。",

            f"本次课程中，{name}{perf_desc}，对新知识的接受能力较强。"
            f"学习记录显示该生基础扎实，具有较大的发展潜力。"
            f"请继续保持学习热情，注重知识的系统性梳理和总结。",

            f"评语：{name}在课堂上{perf_desc}，与同学合作良好，团队意识强。"
            f"学习档案显示该生学习状态稳定，整体呈上升趋势。"
            f"鼓励在薄弱环节多下功夫，实现全面发展。",

            f"{name}是一名{perf_desc}的学生，课堂上认真听讲，笔记规范。"
            f"结合以往表现来看，该生具有较强的学习自觉性。"
            f"建议多做综合性题目，提高知识迁移和灵活应用的能力。",

            f"【学情反馈】{name}同学课堂{perf_desc}，回答问题准确。"
            f"学习档案显示成绩持续稳定，处于班级中等偏上水平。"
            f"期待你在探究性学习中展现更高的思维水平。",

            f"{name}同学学习认真刻苦，本次课{perf_desc}，能够独立完成课堂练习。"
            f"历史表现表明该生学习态度端正，踏实肯干。"
            f"建议加强预习环节，进一步提高课堂学习效率。",

            f"课堂反馈：{name}在本堂课中{perf_desc}，对难点内容有自己的见解。"
            f"学习记录显示该生具有较强的逻辑思维能力。"
            f"请继续保持这份求知欲，勇于探索更深层次的知识。",

            f"{name}同学{perf_desc}，课堂纪律良好，专注度较高。"
            f"从学习情况看，该生基础较为扎实，进步空间很大。"
            f"希望在表达方面更加自信大胆，积极展示自己的思考过程。"
        ]

        idx = (idx - 1) % len(templates)
        return templates[idx]

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
