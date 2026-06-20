import os
import io
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np
from ..db.dao import ClassDAO, StudentDAO, ExamDAO, ExamScoreDAO
from .llm_service import BailianService


class GradeService:
    def __init__(self):
        self.class_dao = ClassDAO()
        self.student_dao = StudentDAO()
        self.exam_dao = ExamDAO()
        self.score_dao = ExamScoreDAO()
        self.llm = BailianService()

    def set_llm_config(self, api_key: str, endpoint: str = ""):
        self.llm.set_config(api_key, endpoint)

    def parse_excel(self, file_path: str) -> Dict:
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ['.xlsx', '.xls', '.csv']:
            raise ValueError("不支持的文件格式，请上传Excel或CSV文件")

        if ext == '.csv':
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        df = df.dropna(how='all')
        df.columns = [str(c).strip() for c in df.columns]

        name_col = self._find_name_column(df)
        subject_cols = self._find_subject_columns(df, name_col)

        result = {
            "raw_dataframe": df,
            "name_column": name_col,
            "subject_columns": subject_cols,
            "student_count": len(df),
            "preview": df.head(10).to_dict('records')
        }
        return result

    def _find_name_column(self, df: pd.DataFrame) -> str:
        keywords = ['姓名', '名字', '学生', 'name', '学生姓名']
        for col in df.columns:
            cl = str(col).lower()
            for kw in keywords:
                if kw.lower() in cl:
                    return col
        for col in df.columns:
            if df[col].dtype == 'object':
                sample = df[col].dropna().astype(str).head(5)
                if all(len(s) <= 10 for s in sample) and any('\u4e00' <= s <= '\u9fff' for s in sample if s):
                    return col
        return df.columns[0]

    def _find_subject_columns(self, df: pd.DataFrame, exclude_col: str) -> List[str]:
        subjects = []
        for col in df.columns:
            if col == exclude_col:
                continue
            if pd.api.types.is_numeric_dtype(df[col]):
                subjects.append(col)
            else:
                try:
                    pd.to_numeric(df[col], errors='raise')
                    subjects.append(col)
                except Exception:
                    pass
        return subjects

    def import_scores(self, class_id: int, exam_name: str, parsed_data: Dict,
                      exam_date: str = None, name_mapping: Dict = None) -> Tuple[int, int]:
        df = parsed_data["raw_dataframe"]
        name_col = parsed_data["name_column"]
        subject_cols = parsed_data["subject_columns"]

        exam_id = self.exam_dao.create(
            class_id=class_id,
            name=exam_name,
            exam_date=exam_date,
            subjects=",".join(subject_cols)
        )

        students = self.student_dao.get_by_class(class_id)
        student_map = {s['name']: s['id'] for s in students}
        if name_mapping:
            for excel_name, db_name in name_mapping.items():
                if db_name in student_map:
                    student_map[excel_name] = student_map[db_name]

        scores_to_insert = []
        imported_count = 0

        for _, row in df.iterrows():
            student_name = str(row[name_col]).strip()
            if not student_name or student_name.lower() == 'nan':
                continue

            student_id = student_map.get(student_name)
            if student_id is None:
                student_id = self.student_dao.create(
                    class_id=class_id,
                    name=student_name
                )
                student_map[student_name] = student_id

            for subject in subject_cols:
                try:
                    score = float(row[subject])
                    if 0 <= score <= 150:
                        scores_to_insert.append({
                            'exam_id': exam_id,
                            'student_id': student_id,
                            'subject': subject,
                            'score': score,
                            'full_score': 100 if score <= 100 else 150
                        })
                        imported_count += 1
                except (ValueError, TypeError):
                    continue

        if scores_to_insert:
            self.score_dao.batch_create(scores_to_insert)

        return exam_id, imported_count

    def get_exam_list(self, class_id: int) -> List[Dict]:
        return self.exam_dao.get_by_class(class_id)

    def get_exam_scores(self, exam_id: int) -> List[Dict]:
        return self.score_dao.get_by_exam(exam_id)

    def calculate_statistics(self, exam_id: int) -> Dict:
        scores = self.score_dao.get_by_exam(exam_id)
        if not scores:
            return {}

        subject_stats = {}
        student_totals = {}

        for s in scores:
            subj = s['subject']
            sid = s['student_id']
            score = s['score']

            if subj not in subject_stats:
                subject_stats[subj] = []
            subject_stats[subj].append(score)

            if sid not in student_totals:
                student_totals[sid] = {'name': s['student_name'], 'total': 0, 'count': 0}
            student_totals[sid]['total'] += score
            student_totals[sid]['count'] += 1

        result = {}
        for subj, vals in subject_stats.items():
            arr = np.array(vals)
            result[subj] = {
                'count': len(arr),
                'avg': round(float(np.mean(arr)), 2),
                'max': round(float(np.max(arr)), 2),
                'min': round(float(np.min(arr)), 2),
                'std': round(float(np.std(arr)), 2),
                'pass_count': int(np.sum(arr >= 60)),
                'pass_rate': round(float(np.sum(arr >= 60) / len(arr) * 100), 1),
                'excellent_count': int(np.sum(arr >= 90)),
                'excellent_rate': round(float(np.sum(arr >= 90) / len(arr) * 100), 1),
                'scores': vals
            }

        ranked_students = sorted(
            [{'student_id': sid, 'name': d['name'],
              'total': round(d['total'], 2),
              'avg': round(d['total'] / d['count'], 2) if d['count'] > 0 else 0}
             for sid, d in student_totals.items()],
            key=lambda x: x['total'], reverse=True
        )
        for i, s in enumerate(ranked_students):
            s['rank'] = i + 1

        result['_rankings'] = ranked_students
        return result

    def get_student_trend_data(self, student_id: int, subject: str = None) -> Dict:
        if subject:
            records = self.score_dao.get_student_subject_scores(student_id, subject)
            return {
                'subject': subject,
                'dates': [r.get('exam_date', r.get('exam_name', '')) for r in records],
                'scores': [r['score'] for r in records]
            }
        else:
            all_scores = self.score_dao.get_by_student(student_id)
            subjects = {}
            for s in all_scores:
                subj = s['subject']
                if subj not in subjects:
                    subjects[subj] = {'dates': [], 'scores': []}
                subjects[subj]['dates'].append(s.get('exam_date', s.get('exam_name', '')))
                subjects[subj]['scores'].append(s['score'])
            return subjects

    def detect_weak_students(self, class_id: int, threshold: float = 60.0) -> List[Dict]:
        exams = self.exam_dao.get_by_class(class_id)
        if not exams:
            return []
        latest_exam = exams[0]
        stats = self.calculate_statistics(latest_exam['id'])
        if '_rankings' not in stats:
            return []

        weak_students = []
        for s in stats['_rankings']:
            if s['avg'] < threshold:
                student_info = self.student_dao.get_by_id(s['student_id'])
                scores_data = self.score_dao.get_by_student(s['student_id'])
                report = self.llm.generate_learning_report(student_info or {}, scores_data)
                weak_students.append({
                    'student_id': s['student_id'],
                    'name': s['name'],
                    'avg_score': s['avg'],
                    'total_score': s['total'],
                    'rank': s['rank'],
                    'report': report
                })
        return weak_students

    def generate_student_report(self, student_id: int) -> Dict:
        student_info = self.student_dao.get_by_id(student_id)
        scores_data = self.score_dao.get_by_student(student_id)
        return self.llm.generate_learning_report(student_info or {}, scores_data)
