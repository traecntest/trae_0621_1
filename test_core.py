import sys
import os
import tempfile
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import DatabaseManager
from app.db.dao import ClassDAO, StudentDAO
from app.services.llm_service import BailianService
from app.services.feedback_service import FeedbackService
from app.services.grade_service import GradeService
from app.services.paper_service import PaperService
from app.utils.test_data_generator import TestDataGenerator


def test_database():
    print("=" * 50)
    print("[1/6] 测试数据库层...")

    tmp_db = tempfile.mktemp(suffix='.db')
    DatabaseManager.set_db_path(tmp_db)

    db = DatabaseManager()
    db.init_tables()
    print("  ✓ 数据库初始化成功")

    class_dao = ClassDAO()
    cid = class_dao.create("测试班级", "高一", "数学", "张老师")
    assert cid > 0, "班级创建失败"
    print(f"  ✓ 创建班级成功 (ID={cid})")

    classes = class_dao.get_all()
    assert len(classes) >= 1, "查询班级失败"
    print("  ✓ 查询班级列表成功")

    student_dao = StudentDAO()
    sid = student_dao.create(cid, "测试学生", "男", "2010-01-01",
                             "STU001", "家长", "13800138000", "测试备注")
    assert sid > 0, "学生创建失败"
    print(f"  ✓ 创建学生成功 (ID={sid})")

    students = student_dao.get_by_class(cid)
    assert len(students) >= 1
    print("  ✓ 查询学生列表成功")

    os.remove(tmp_db)
    print("  ✓ 数据库层测试通过")


def test_llm_service():
    print("=" * 50)
    print("[2/6] 测试大模型服务（Mock模式）...")

    llm = BailianService()

    student = {"name": "张三", "gender": "男"}
    history = [
        {"subject": "数学", "score": 85},
        {"subject": "语文", "score": 92}
    ]
    feedbacks = llm.generate_feedback(student, history, "良好", 5)
    assert isinstance(feedbacks, list) and len(feedbacks) == 5
    print(f"  ✓ 生成课堂反馈 {len(feedbacks)} 条")

    questions = llm.analyze_paper_questions("1. 题目一\n2. 题目二")
    assert isinstance(questions, list) and len(questions) > 0
    print(f"  ✓ 分析试卷题目 {len(questions)} 道")

    report = llm.generate_learning_report(student, history)
    assert isinstance(report, dict) and "summary" in report
    print("  ✓ 生成学情报告成功")

    print("  ✓ 大模型服务测试通过")


def test_feedback_service():
    print("=" * 50)
    print("[3/6] 测试课堂反馈服务...")

    tmp_db = tempfile.mktemp(suffix='.db')
    DatabaseManager.set_db_path(tmp_db)
    db = DatabaseManager()
    db.init_tables()

    service = FeedbackService()
    class_dao = ClassDAO()
    student_dao = StudentDAO()

    cid = class_dao.create("反馈测试班", "高一", "数学", "王老师")
    sids = []
    for i in range(5):
        sids.append(student_dao.create(cid, f"学生{i+1}", "男"))

    students = service.get_students_by_class(cid)
    assert len(students) == 5
    print(f"  ✓ 加载班级学生 {len(students)} 人")

    results = service.generate_feedbacks(sids, cid, "良好", 3)
    assert len(results) == 5
    for sid, fbs in results.items():
        assert len(fbs) == 3
    print(f"  ✓ 批量生成反馈成功，共 {len(results)} 人 × 3 条")

    fid = service.save_feedback(sids[0], cid, "测试反馈内容")
    assert fid > 0
    print(f"  ✓ 保存单条反馈成功 (ID={fid})")

    history = service.get_student_feedbacks(sids[0])
    assert len(history) >= 1
    print("  ✓ 查询历史反馈成功")

    os.remove(tmp_db)
    print("  ✓ 课堂反馈服务测试通过")


def test_grade_service():
    print("=" * 50)
    print("[4/6] 测试成绩分析服务...")

    tmp_db = tempfile.mktemp(suffix='.db')
    DatabaseManager.set_db_path(tmp_db)
    db = DatabaseManager()
    db.init_tables()

    service = GradeService()
    class_dao = ClassDAO()
    student_dao = StudentDAO()

    cid = class_dao.create("成绩测试班", "高二", "全科", "李老师")
    sids = []
    for i in range(10):
        sids.append(student_dao.create(cid, f"学生{i+1}", random.choice(["男", "女"])))

    exam_name = "期中考试"
    from app.db.dao import ExamDAO, ExamScoreDAO
    exam_dao = ExamDAO()
    score_dao = ExamScoreDAO()
    eid = exam_dao.create(cid, exam_name, "2024-06-01", "数学,语文,英语")

    subjects = ["数学", "语文", "英语"]
    scores = []
    for sid in sids:
        for subj in subjects:
            scores.append({
                "exam_id": eid,
                "student_id": sid,
                "subject": subj,
                "score": float(random.randint(50, 100))
            })
    score_dao.batch_create(scores)
    print(f"  ✓ 创建考试数据：{len(sids)} 学生 × {len(subjects)} 学科")

    stats = service.calculate_statistics(eid)
    assert "_rankings" in stats and len(stats["_rankings"]) == 10
    for subj in subjects:
        assert subj in stats
        assert "avg" in stats[subj]
    print("  ✓ 计算成绩统计成功")

    weak = service.detect_weak_students(cid, 70)
    assert isinstance(weak, list)
    print(f"  ✓ 识别薄弱学生：{len(weak)} 人")

    report = service.generate_student_report(sids[0])
    assert isinstance(report, dict) and "summary" in report
    print("  ✓ 生成学情报告成功")

    trend = service.get_student_trend_data(sids[0], "数学")
    assert isinstance(trend, dict)
    print("  ✓ 获取成绩趋势数据成功")

    os.remove(tmp_db)
    print("  ✓ 成绩分析服务测试通过")


def test_paper_service():
    print("=" * 50)
    print("[5/6] 测试试卷分析服务...")

    tmp_db = tempfile.mktemp(suffix='.db')
    DatabaseManager.set_db_path(tmp_db)
    db = DatabaseManager()
    db.init_tables()

    service = PaperService()
    class_dao = ClassDAO()
    student_dao = StudentDAO()

    cid = class_dao.create("试卷测试班", "高三", "数学", "赵老师")
    sids = []
    for i in range(5):
        sids.append(student_dao.create(cid, f"学生{i+1}"))

    q_text = "1. 解方程 x²-5x+6=0\n2. 求 sin30°+cos60°\n3. 证明勾股定理"
    result = service.analyze_paper_from_text(q_text, "单元测试", "数学", cid)
    assert result["paper_id"] > 0
    assert result["question_count"] >= 3
    print(f"  ✓ 分析试卷成功，识别 {result['question_count']} 道题目")

    from app.db.dao import PaperQuestionDAO, PaperAnswerDAO
    q_dao = PaperQuestionDAO()
    a_dao = PaperAnswerDAO()
    questions = q_dao.get_by_paper(result["paper_id"])
    for sid in sids:
        for q in questions:
            a_dao.create(q["id"], sid, random.randint(0, 1), "",
                         q["score"] if random.random() > 0.35 else 0)
    print("  ✓ 生成答题数据成功")

    error_dist = service.get_error_distribution(result["paper_id"])
    assert isinstance(error_dist, list) and len(error_dist) > 0
    print(f"  ✓ 获取错题分布成功，共 {len(error_dist)} 道题统计")

    outline = service.generate_review_outline(result["paper_id"])
    assert isinstance(outline, dict) and "outline" in outline
    print(f"  ✓ 生成讲评提纲成功，共 {len(outline['outline'])} 个章节")

    os.remove(tmp_db)
    print("  ✓ 试卷分析服务测试通过")


def test_data_generator():
    print("=" * 50)
    print("[6/6] 测试数据生成器...")

    tmp_db = tempfile.mktemp(suffix='.db')
    DatabaseManager.set_db_path(tmp_db)
    db = DatabaseManager()
    db.init_tables()

    gen = TestDataGenerator()
    result = gen.generate_all(
        class_count=2,
        students_per_class=8,
        exams_per_class=2,
        feedbacks_per_student=2,
        papers_per_class=1
    )
    assert len(result["classes"]) == 2
    assert result["total_students"] == 16
    assert result["total_exams"] == 4
    assert result["total_papers"] == 2
    print(f"  ✓ 生成测试数据：")
    print(f"    - 班级：{len(result['classes'])} 个")
    print(f"    - 学生：{result['total_students']} 人")
    print(f"    - 考试：{result['total_exams']} 场")
    print(f"    - 试卷：{result['total_papers']} 份")

    os.remove(tmp_db)
    print("  ✓ 测试数据生成器测试通过")


if __name__ == "__main__":
    print("\n🎓 K12教育AI工作台 - 核心模块测试")
    print("=" * 50)

    try:
        test_database()
        test_llm_service()
        test_feedback_service()
        test_grade_service()
        test_paper_service()
        test_data_generator()

        print("\n" + "=" * 50)
        print("🎉 所有核心模块测试通过！")
        print("   现在可以运行 'python main.py' 启动桌面应用")
        print("=" * 50)
    except AssertionError as e:
        print(f"\n❌ 测试断言失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试出现异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
