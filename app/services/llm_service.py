import json
import time
import random
from typing import List, Dict, Optional


class BailianService:
    def __init__(self, api_key: str = "", endpoint: str = ""):
        self.api_key = api_key
        self.endpoint = endpoint
        self._use_mock = not api_key

    def set_config(self, api_key: str, endpoint: str = ""):
        self.api_key = api_key
        self.endpoint = endpoint
        self._use_mock = not api_key

    def generate_feedback(self, student_info: Dict, learning_history: List[Dict],
                          classroom_performance: str, count: int = 10) -> List[str]:
        if self._use_mock:
            return self._mock_generate_feedback(student_info, learning_history,
                                                classroom_performance, count)
        return self._call_bailian_feedback(student_info, learning_history,
                                           classroom_performance, count)

    def _mock_generate_feedback(self, student_info: Dict, learning_history: List[Dict],
                                classroom_performance: str, count: int) -> List[str]:
        student_name = student_info.get('name', '该学生')
        templates = [
            f"{student_name}同学在本次课堂中表现{self._perf_desc(classroom_performance)}，"
            f"能够积极参与课堂讨论，思维敏捷。从学习记录来看，{self._history_desc(learning_history)}。"
            f"建议在后续学习中继续保持良好的学习习惯，加强知识点的巩固练习。",

            f"【课堂评价】{student_name}本节课{self._perf_desc(classroom_performance)}。"
            f"作业完成质量较高，体现了较强的自主学习能力。"
            f"结合过往表现，{self._history_desc(learning_history)}。"
            f"希望继续保持积极向上的学习态度，争取更大进步。",

            f"{student_name}同学学习态度端正，课堂表现{self._perf_desc(classroom_performance)}。"
            f"善于思考问题，能够主动提问。回顾学习历程，{self._history_desc(learning_history)}。"
            f"建议增加拓展练习，提升综合应用能力。",

            f"本次课程中，{student_name}{self._perf_desc(classroom_performance)}，"
            f"对新知识的接受能力较强，能快速掌握重点内容。"
            f"从历史数据看，{self._history_desc(learning_history)}。"
            f"请继续保持学习热情，注重知识的系统性梳理。",

            f"评语：{student_name}在课堂上{self._perf_desc(classroom_performance)}，"
            f"与同学合作良好，团队意识强。学习记录显示，{self._history_desc(learning_history)}。"
            f"鼓励在薄弱环节多下功夫，实现全面发展。",

            f"{student_name}是一名{self._perf_desc(classroom_performance)}的学生，"
            f"课堂上认真听讲，笔记规范。结合以往表现，{self._history_desc(learning_history)}。"
            f"建议多做综合性题目，提高知识迁移能力。",

            f"【学情反馈】{student_name}同学课堂表现{self._perf_desc(classroom_performance)}，"
            f"回答问题积极且准确。学习轨迹显示，{self._history_desc(learning_history)}。"
            f"期待你在挑战题中展现更高的思维水平。",

            f"{student_name}同学学习认真刻苦，本次课表现{self._perf_desc(classroom_performance)}，"
            f"能够独立完成课堂练习。历史表现表明，{self._history_desc(learning_history)}。"
            f"建议加强预习，提高课堂效率。",

            f"课堂反馈：{student_name}在本堂课中{self._perf_desc(classroom_performance)}，"
            f"对难点内容有独到见解。学习档案显示，{self._history_desc(learning_history)}。"
            f"请继续保持求知欲，勇于探索更深层次的知识。",

            f"{student_name}同学{self._perf_desc(classroom_performance)}，"
            f"课堂纪律良好，专注力较高。从学习情况看，{self._history_desc(learning_history)}。"
            f"希望在表达方面更加自信大胆，积极展示自己的思考过程。",

            f"【详细评价】{student_name}本节课{self._perf_desc(classroom_performance)}，"
            f"在小组活动中表现出色，能够带领小组成员共同进步。"
            f"回顾学习历程，{self._history_desc(learning_history)}。"
            f"建议继续发挥领导力，同时注重个人薄弱知识点的强化训练。",

            f"{student_name}同学思维活跃，课堂表现{self._perf_desc(classroom_performance)}，"
            f"善于发现问题并提出质疑。学习记录显示，{self._history_desc(learning_history)}。"
            f"请保持这份好奇心，在探索中不断成长。"
        ]
        return random.sample(templates, min(count, len(templates)))

    def _perf_desc(self, performance: str) -> str:
        if not performance:
            return "良好"
        p = performance.lower()
        if "优秀" in p or "excellent" in p or "积极" in p:
            return "非常优秀"
        if "良好" in p or "good" in p:
            return "良好"
        if "一般" in p or "普通" in p:
            return "一般"
        if "待" in p or "需" in p or "差" in p:
            return "有待提高"
        return "良好"

    def _history_desc(self, history: List[Dict]) -> str:
        if not history:
            return "该生学习基础扎实"
        scores = [h.get('score', 0) for h in history if isinstance(h, dict) and 'score' in h]
        if not scores:
            return "学习状态持续稳定"
        avg = sum(scores) / len(scores)
        if avg >= 90:
            return f"成绩一直保持在优秀水平（平均{avg:.1f}分）"
        if avg >= 80:
            return f"成绩处于良好水平（平均{avg:.1f}分）"
        if avg >= 70:
            return f"成绩中等，有较大提升空间（平均{avg:.1f}分）"
        return f"基础有待加强，需要更多练习（平均{avg:.1f}分）"

    def _call_bailian_feedback(self, student_info: Dict, learning_history: List[Dict],
                               classroom_performance: str, count: int) -> List[str]:
        try:
            import requests
            prompt = f"""请为学生"{student_info.get('name', '')}"生成{count}条个性化课堂反馈文案。
学生信息：{json.dumps(student_info, ensure_ascii=False)}
过往学习记录：{json.dumps(learning_history, ensure_ascii=False)}
当前课堂表现：{classroom_performance}

要求：
1. 每条反馈100-200字，风格亲切专业
2. 结合历史数据给出针对性评价
3. 包含肯定、建议、鼓励三部分
4. 输出为JSON数组格式，每个元素是一条反馈"""

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "qwen-max",
                "input": {
                    "messages": [
                        {"role": "system", "content": "你是一名资深的K12教育专家，擅长撰写个性化课堂反馈。"},
                        {"role": "user", "content": prompt}
                    ]
                },
                "parameters": {"temperature": 0.8}
            }
            url = self.endpoint or "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            content = data.get('output', {}).get('choices', [{}])[0].get('message', {}).get('content', '')
            try:
                result = json.loads(content)
                if isinstance(result, list):
                    return result[:count]
            except Exception:
                pass
            return [content.strip()] * count
        except Exception as e:
            return self._mock_generate_feedback(student_info, learning_history,
                                                classroom_performance, count)

    def analyze_paper_questions(self, questions_text: str) -> List[Dict]:
        if self._use_mock:
            return self._mock_analyze_paper(questions_text)
        return self._call_bailian_paper(questions_text)

    def _mock_analyze_paper(self, questions_text: str) -> List[Dict]:
        knowledge_points = ["一元二次方程", "函数图像", "几何证明", "概率统计",
                            "三角函数", "向量运算", "导数应用", "立体几何"]
        mistakes = ["计算错误", "概念混淆", "审题不清", "公式记错",
                    "步骤遗漏", "单位错误", "逻辑不严谨"]

        questions = []
        lines = questions_text.strip().split('\n')
        for i, line in enumerate(lines[:20], 1):
            if line.strip():
                questions.append({
                    "question_no": str(i),
                    "content": line.strip()[:100],
                    "score": random.choice([5, 8, 10, 12, 15]),
                    "knowledge_point": random.choice(knowledge_points),
                    "difficulty": round(random.uniform(0.3, 0.9), 2),
                    "common_mistakes": random.choice(mistakes)
                })
        if not questions:
            for i in range(1, 11):
                questions.append({
                    "question_no": str(i),
                    "content": f"第{i}题：示例题目内容",
                    "score": random.choice([5, 8, 10, 12, 15]),
                    "knowledge_point": random.choice(knowledge_points),
                    "difficulty": round(random.uniform(0.3, 0.9), 2),
                    "common_mistakes": random.choice(mistakes)
                })
        return questions

    def _call_bailian_paper(self, questions_text: str) -> List[Dict]:
        try:
            import requests
            prompt = f"""请分析以下试卷题目，为每道题标注考点、难度系数（0-1）和易错点。

题目内容：
{questions_text}

请输出JSON数组，每个元素包含：question_no(题号), content(题目内容), score(分值),
knowledge_point(考点), difficulty(难度系数0-1), common_mistakes(易错点)"""

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "qwen-max",
                "input": {
                    "messages": [
                        {"role": "system", "content": "你是一名资深的K12教研专家，擅长试卷分析。"},
                        {"role": "user", "content": prompt}
                    ]
                },
                "parameters": {"temperature": 0.3}
            }
            url = self.endpoint or "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            content = data.get('output', {}).get('choices', [{}])[0].get('message', {}).get('content', '')
            try:
                result = json.loads(content)
                if isinstance(result, list):
                    return result
            except Exception:
                pass
            return self._mock_analyze_paper(questions_text)
        except Exception as e:
            return self._mock_analyze_paper(questions_text)

    def generate_learning_report(self, student_info: Dict, scores_data: List[Dict]) -> Dict:
        if self._use_mock:
            return self._mock_learning_report(student_info, scores_data)
        return self._call_bailian_report(student_info, scores_data)

    def _mock_learning_report(self, student_info: Dict, scores_data: List[Dict]) -> Dict:
        student_name = student_info.get('name', '该生')
        subjects = {}
        for s in scores_data:
            subj = s.get('subject', '')
            if subj and subj not in subjects:
                subjects[subj] = []
            if subj:
                subjects[subj].append(s.get('score', 0))

        avg_scores = {subj: (sum(sc) / len(sc) if sc else 0) for subj, sc in subjects.items()}
        weak_subjects = [s for s, a in avg_scores.items() if a < 70]
        strong_subjects = [s for s, a in avg_scores.items() if a >= 90]

        return {
            "summary": f"{student_name}同学总体学习情况{'优秀' if sum(avg_scores.values())/max(len(avg_scores),1) >= 85 else '良好'}，"
                       f"各科成绩{'较为均衡' if abs(max(avg_scores.values()) - min(avg_scores.values())) < 15 else '存在一定波动'}。",
            "strengths": f"优势学科：{'、'.join(strong_subjects) if strong_subjects else '暂无明显优势学科'}，"
                         f"建议继续保持并适当加深难度。",
            "weaknesses": f"薄弱学科：{'、'.join(weak_subjects) if weak_subjects else '暂无明显薄弱学科'}，"
                          f"需要加强基础训练和针对性练习。",
            "suggestions": [
                "制定每周学习计划，合理分配各科学习时间",
                "建立错题本，定期复习易错知识点",
                "积极参与课堂讨论，提高思维活跃度",
                "注重知识总结，形成系统化的知识体系"
            ],
            "trend": "成绩整体呈上升趋势，继续保持良好的学习状态。"
        }

    def _call_bailian_report(self, student_info: Dict, scores_data: List[Dict]) -> Dict:
        try:
            import requests
            prompt = f"""请为以下学生生成学情分析报告：
学生信息：{json.dumps(student_info, ensure_ascii=False)}
成绩数据：{json.dumps(scores_data, ensure_ascii=False)}

输出JSON格式，包含：summary(总体评价), strengths(优势分析), weaknesses(薄弱点分析),
suggestions(学习建议数组), trend(成绩趋势分析)"""

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "qwen-max",
                "input": {
                    "messages": [
                        {"role": "system", "content": "你是一名资深的K12教育分析师。"},
                        {"role": "user", "content": prompt}
                    ]
                },
                "parameters": {"temperature": 0.5}
            }
            url = self.endpoint or "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            content = data.get('output', {}).get('choices', [{}])[0].get('message', {}).get('content', '')
            try:
                return json.loads(content)
            except Exception:
                return self._mock_learning_report(student_info, scores_data)
        except Exception as e:
            return self._mock_learning_report(student_info, scores_data)
