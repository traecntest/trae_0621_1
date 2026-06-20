import random
from datetime import datetime, timedelta
from typing import List, Dict
from ..db.dao import (ClassDAO, StudentDAO, FeedbackDAO, ExamDAO,
                        ExamScoreDAO, PaperDAO, PaperQuestionDAO,
                        PaperAnswerDAO, LearningRecordDAO)


class TestDataGenerator:
    def __init__(self):
        self.class_dao = ClassDAO()
        self.student_dao = StudentDAO()
        self.feedback_dao = FeedbackDAO()
        self.exam_dao = ExamDAO()
        self.score_dao = ExamScoreDAO()
        self.paper_dao = PaperDAO()
        self.question_dao = PaperQuestionDAO()
        self.answer_dao = PaperAnswerDAO()
        self.learning_dao = LearningRecordDAO()

        self.first_names = ["张", "李", "王", "刘", "陈", "杨", "赵", "黄", "周", "吴",
                            "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马", "罗"]
        self.given_names = ["伟", "芳", "娜", "敏", "静", "丽", "强", "磊", "军", "洋",
                            "勇", "艳", "杰", "涛", "明", "超", "秀英", "霞", "平", "刚",
                            "桂英", "致远", "梓涵", "雨桐", "思琪", "浩宇", "子轩", "欣怡",
                            "梓萱", "浩然", "雨萱", "一诺", "子墨", "思远", "沐宸", "若曦"]
        self.subjects = ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"]
        self.grades = ["初一", "初二", "初三", "高一", "高二", "高三", "小四", "小五", "小六"]

    def random_name(self) -> str:
        return random.choice(self.first_names) + random.choice(self.given_names)

    def random_phone(self) -> str:
        return "1" + random.choice(["3", "5", "7", "8", "9"]) + "".join(
            [str(random.randint(0, 9)) for _ in range(9)]
        )

    def generate_classes(self, count: int = 3) -> List[int]:
        class_ids = []
        for i in range(count):
            grade = random.choice(self.grades)
            subject = random.choice(self.subjects[:5])
            class_id = self.class_dao.create(
                name=f"{grade}{subject}{i+1}班",
                grade=grade,
                subject=subject,
                teacher=self.random_name() + "老师"
            )
            class_ids.append(class_id)
        return class_ids

    def generate_students(self, class_id: int, count: int = 30) -> List[int]:
        student_ids = []
        used_names = set()
        for i in range(count):
            while True:
                name = self.random_name()
                if name not in used_names:
                    used_names.add(name)
                    break
            gender = random.choice(["男", "女"])
            birth_year = random.randint(2005, 2015)
            birth_month = random.randint(1, 12)
            birth_day = random.randint(1, 28)
            sid = self.student_dao.create(
                class_id=class_id,
                name=name,
                gender=gender,
                birthday=f"{birth_year}-{birth_month:02d}-{birth_day:02d}",
                student_no=f"STU{class_id:04d}{i+1:04d}",
                guardian_name=self.random_name(),
                guardian_phone=self.random_phone(),
                notes=random.choice(["", "学习认真", "需要关注", "基础较好", "活泼好动", "安静内向"])
            )
            student_ids.append(sid)
        return student_ids

    def generate_learning_records(self, student_id: int, count: int = 5) -> None:
        types = ["课堂表现", "作业情况", "测验成绩", "老师评语", "家长反馈"]
        contents = {
            "课堂表现": ["上课积极发言", "注意力集中", "参与小组讨论", "课堂纪律良好"],
            "作业情况": ["按时完成作业", "作业质量高", "书写工整", "需加强练习"],
            "测验成绩": ["测验成绩优秀", "成绩稳步提升", "需加强基础", "进步明显"],
            "老师评语": ["学习态度端正", "思维敏捷", "需更加努力", "潜力巨大"],
            "家长反馈": ["在家学习认真", "需家长监督", "自主学习能力强"]
        }
        base_date = datetime.now()
        for i in range(count):
            rtype = random.choice(types)
            record_date = (base_date - timedelta(days=random.randint(1, 90))).strftime("%Y-%m-%d")
            self.learning_dao.create(
                student_id=student_id,
                record_type=rtype,
                content=random.choice(contents[rtype]),
                record_date=record_date
            )

    def generate_exams(self, class_id: int, student_ids: List[int],
                        count: int = 3) -> List[int]:
        exam_ids = []
        subjects = random.sample(self.subjects, k=random.randint(3, 6))
        for e in range(count):
            exam_date = (datetime.now() - timedelta(days=random.randint(7, 180))).strftime("%Y-%m-%d")
            exam_id = self.exam_dao.create(
                class_id=class_id,
                name=f"第{e+1}次月考",
                exam_date=exam_date,
                subjects=",".join(subjects)
            )
            exam_ids.append(exam_id)

            scores = []
            for sid in student_ids:
                for subj in subjects:
                    if random.random() < 0.15:
                        score = random.randint(40, 69)
                    elif random.random() < 0.5:
                        score = random.randint(70, 84)
                    elif random.random() < 0.8:
                        score = random.randint(85, 94)
                    else:
                        score = random.randint(95, 100)
                    scores.append({
                        'exam_id': exam_id,
                        'student_id': sid,
                        'subject': subj,
                        'score': float(score),
                        'full_score': 100
                    })
            self.score_dao.batch_create(scores)

        return exam_ids

    def generate_feedbacks(self, class_id: int, student_ids: List[int],
                            count_per_student: int = 2) -> None:
        templates = [
            "课堂表现优秀，积极参与讨论，学习态度端正。",
            "作业完成认真，知识点掌握扎实，继续保持。",
            "本次测验进步明显，希望再接再厉。",
            "上课注意力集中，思维活跃，回答问题准确。",
            "需要加强课堂互动，多参与小组讨论。",
            "基础有待加强，建议多做练习巩固知识点。",
            "学习态度认真，能够按时完成各项任务。",
            "本次课堂表现活跃，对新知识接受能力强。"
        ]
        for sid in student_ids:
            for _ in range(count_per_student):
                self.feedback_dao.create(
                    student_id=sid,
                    class_id=class_id,
                    content=random.choice(templates),
                    category=random.choice(["课堂反馈", "作业反馈", "测验反馈"])
                )

    def generate_papers(self, class_id: int, student_ids: List[int],
                         count: int = 2) -> List[int]:
        paper_ids = []
        knowledge_points = ["一元二次方程", "函数图像", "几何证明", "概率统计",
                            "三角函数", "向量运算", "导数应用", "立体几何"]
        mistakes = ["计算错误", "概念混淆", "审题不清", "公式记错",
                    "步骤遗漏", "单位错误", "逻辑不严谨"]

        for p in range(count):
            paper_id = self.paper_dao.create(
                name=f"单元测试卷{p+1}",
                subject=random.choice(self.subjects[:5]),
                class_id=class_id,
                total_score=100
            )
            paper_ids.append(paper_id)

            questions = []
            for i in range(1, 11):
                questions.append({
                    "paper_id": paper_id,
                    "question_no": str(i),
                    "content": f"第{i}题：示例题目内容（{random.choice(knowledge_points)}相关）",
                    "score": random.choice([5, 8, 10, 12]),
                    "knowledge_point": random.choice(knowledge_points),
                    "difficulty": round(random.uniform(0.3, 0.9), 2),
                    "common_mistakes": random.choice(mistakes)
                })
            self.question_dao.batch_create(questions)

            q_list = self.question_dao.get_by_paper(paper_id)
            for sid in student_ids:
                for q in q_list:
                    is_correct = 1 if random.random() > 0.35 else 0
                    self.answer_dao.create(
                        question_id=q['id'],
                        student_id=sid,
                        is_correct=is_correct,
                        student_answer="" if is_correct else "错误答案示例",
                        score=q['score'] if is_correct else random.randint(0, int(q['score'] / 2))
                    )

        return paper_ids

    def generate_all(self, class_count: int = 3, students_per_class: int = 25,
                      exams_per_class: int = 3, feedbacks_per_student: int = 2,
                      papers_per_class: int = 2) -> Dict:
        result = {
            "classes": [],
            "total_students": 0,
            "total_exams": 0,
            "total_papers": 0
        }
        for _ in range(class_count):
            cids = self.generate_classes(1)
            class_id = cids[0]
            result["classes"].append(class_id)

            sids = self.generate_students(class_id, students_per_class)
            result["total_students"] += len(sids)

            for sid in sids:
                self.generate_learning_records(sid, random.randint(3, 8))

            eids = self.generate_exams(class_id, sids, exams_per_class)
            result["total_exams"] += len(eids)

            self.generate_feedbacks(class_id, sids, feedbacks_per_student)

            pids = self.generate_papers(class_id, sids, papers_per_class)
            result["total_papers"] += len(pids)

        return result
