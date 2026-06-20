import os
from typing import List, Dict
from ..db.dao import PaperDAO, PaperQuestionDAO, PaperAnswerDAO, StudentDAO
from .llm_service import BailianService


class PaperService:
    def __init__(self):
        self.paper_dao = PaperDAO()
        self.question_dao = PaperQuestionDAO()
        self.answer_dao = PaperAnswerDAO()
        self.student_dao = StudentDAO()
        self.llm = BailianService()

    def set_llm_config(self, api_key: str, endpoint: str = ""):
        self.llm.set_config(api_key, endpoint)

    def ocr_recognize(self, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext in ['.txt']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif ext in ['.png', '.jpg', '.jpeg', '.bmp', '.pdf']:
                return self._mock_ocr_result()
            else:
                return self._mock_ocr_result()
        except Exception:
            return self._mock_ocr_result()

    def _mock_ocr_result(self) -> str:
        return """1. 已知一元二次方程 x² - 5x + 6 = 0，求方程的两个根。
2. 计算：sin30° + cos60° - tan45°
3. 已知函数 f(x) = 2x² - 3x + 1，求 f(2) 的值。
4. 证明：等腰三角形两底角相等。
5. 从1,2,3,4,5中随机取两个数，求两数之和为偶数的概率。
6. 已知向量 a=(1,2), b=(3,-1)，求 a·b 的值。
7. 求函数 y = x³ - 3x² + 2 的极值。
8. 已知正方体 ABCD-A1B1C1D1 的棱长为2，求对角线 AC1 的长度。
9. 解不等式：2x - 3 > 5
10. 已知等差数列{an}中，a1=2, d=3，求 a10 的值。"""

    def analyze_paper(self, file_path: str, paper_name: str,
                      subject: str, class_id: int = None) -> Dict:
        ocr_text = self.ocr_recognize(file_path)

        paper_id = self.paper_dao.create(
            name=paper_name,
            subject=subject,
            class_id=class_id,
            file_path=file_path
        )

        questions = self.llm.analyze_paper_questions(ocr_text)
        for q in questions:
            q['paper_id'] = paper_id
        self.question_dao.batch_create(questions)

        total_score = sum(q.get('score', 0) for q in questions)
        if total_score > 0:
            pass

        return {
            'paper_id': paper_id,
            'question_count': len(questions),
            'questions': questions,
            'ocr_text': ocr_text,
            'total_score': total_score
        }

    def analyze_paper_from_text(self, questions_text: str, paper_name: str,
                                subject: str, class_id: int = None) -> Dict:
        paper_id = self.paper_dao.create(
            name=paper_name,
            subject=subject,
            class_id=class_id
        )

        questions = self.llm.analyze_paper_questions(questions_text)
        for q in questions:
            q['paper_id'] = paper_id
        self.question_dao.batch_create(questions)

        return {
            'paper_id': paper_id,
            'question_count': len(questions),
            'questions': questions
        }

    def get_paper_list(self) -> List[Dict]:
        return self.paper_dao.get_all()

    def get_paper_detail(self, paper_id: int) -> Dict:
        paper = self.paper_dao.get_by_id(paper_id)
        if not paper:
            return {}
        questions = self.question_dao.get_by_paper(paper_id)
        paper['questions'] = questions
        return paper

    def record_answers(self, paper_id: int, student_id: int,
                       answers: List[Dict]) -> int:
        questions = self.question_dao.get_by_paper(paper_id)
        q_map = {str(q['question_no']): q['id'] for q in questions}

        count = 0
        for ans in answers:
            q_no = str(ans.get('question_no', ''))
            if q_no in q_map:
                is_correct = 1 if ans.get('is_correct', False) else 0
                self.answer_dao.create(
                    question_id=q_map[q_no],
                    student_id=student_id,
                    is_correct=is_correct,
                    student_answer=ans.get('student_answer', ''),
                    score=ans.get('score', 0)
                )
                count += 1
        return count

    def get_error_distribution(self, paper_id: int) -> List[Dict]:
        return self.answer_dao.get_error_distribution(paper_id)

    def generate_review_outline(self, paper_id: int) -> Dict:
        paper = self.paper_dao.get_by_id(paper_id)
        if not paper:
            return {}

        questions = self.question_dao.get_by_paper(paper_id)
        error_dist = self.answer_dao.get_error_distribution(paper_id)

        kp_stats = {}
        for q in questions:
            kp = q.get('knowledge_point', '未分类')
            if kp not in kp_stats:
                kp_stats[kp] = {'questions': [], 'difficulties': [], 'total_score': 0}
            kp_stats[kp]['questions'].append(q)
            kp_stats[kp]['difficulties'].append(q.get('difficulty', 0.5))
            kp_stats[kp]['total_score'] += q.get('score', 0)

        high_error = [e for e in error_dist
                      if e.get('wrong_count', 0) > 0 and e.get('total_count', 0) > 0
                      and e['wrong_count'] / e['total_count'] >= 0.4]
        high_error_sorted = sorted(high_error,
                                   key=lambda x: x.get('wrong_count', 0),
                                   reverse=True)

        sections = []
        if high_error_sorted:
            sections.append({
                "title": "一、重点错题讲解",
                "content": "本次考试错误率较高的题目需要重点讲评：",
                "items": [
                    f"第{q['question_no']}题（错误率："
                    f"{q['wrong_count']}/{q['total_count']}）："
                    f"{q.get('content', '')[:50]}... 考点：{q.get('knowledge_point', '未知')}"
                    for q in high_error_sorted[:5]
                ]
            })

        if kp_stats:
            sections.append({
                "title": "二、考点知识梳理",
                "content": "本次试卷涉及的主要知识点及分布：",
                "items": [
                    f"【{kp}】共{len(d['questions'])}题，"
                    f"总分{d['total_score']}分，"
                    f"平均难度{sum(d['difficulties'])/len(d['difficulties']):.2f}"
                    for kp, d in kp_stats.items()
                ]
            })

        hard_questions = sorted(
            [q for q in questions if q.get('difficulty', 0) >= 0.7],
            key=lambda x: x.get('difficulty', 0), reverse=True
        )
        if hard_questions:
            sections.append({
                "title": "三、难点突破",
                "content": "本次试卷难度较高的题目及解题思路：",
                "items": [
                    f"第{q['question_no']}题（难度{q.get('difficulty', 0):.2f}）："
                    f"{q.get('common_mistakes', '需关注解题步骤规范性')}"
                    for q in hard_questions[:5]
                ]
            })

        mistake_types = {}
        for q in questions:
            cm = q.get('common_mistakes', '')
            if cm:
                mistake_types[cm] = mistake_types.get(cm, 0) + 1
        if mistake_types:
            sorted_mistakes = sorted(mistake_types.items(),
                                     key=lambda x: x[1], reverse=True)
            sections.append({
                "title": "四、常见易错点总结",
                "content": "学生在答题中暴露的共性问题：",
                "items": [f"{m}（出现{k}次）" for m, k in sorted_mistakes]
            })

        sections.append({
            "title": "五、巩固练习建议",
            "content": "针对本次考试情况，建议进行以下强化训练：",
            "items": [
                "完成对应考点的专题训练题",
                "整理错题本，定期回顾复习",
                "加强基础概念的理解和辨析",
                "提高解题规范性和计算准确率"
            ]
        })

        return {
            "paper_name": paper.get('name', ''),
            "subject": paper.get('subject', ''),
            "outline": sections
        }
