import sqlite3
import pandas as pd
import os
from datetime import datetime
import hashlib
import json

class UserDataManager:
    def __init__(self, db_path="quiz_app_data.db"):
        """Khởi tạo quản lý dữ liệu người dùng với đường dẫn đến database"""
        self.db_path = db_path
        self.create_tables_if_not_exist()
    
    def create_tables_if_not_exist(self):
        """Tạo các bảng cần thiết nếu chưa tồn tại"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Bảng users - lưu thông tin người dùng
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
        ''')
        
        # Bảng user_preferences - lưu các tùy chọn của người dùng
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            preference_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            preferred_languages TEXT,
            preferred_topics TEXT,
            difficulty_level TEXT DEFAULT 'beginner',
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # Bảng quiz_history - lưu lịch sử làm bài quiz
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_history (
            quiz_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            language TEXT NOT NULL,
            topic TEXT NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            duration_seconds INTEGER,
            quiz_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            difficulty_level TEXT,
            questions_data TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # Bảng question_responses - lưu câu trả lời chi tiết
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS question_responses (
            response_id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            question_index INTEGER,
            question_text TEXT,
            user_answer TEXT,
            correct_answer TEXT,
            is_correct BOOLEAN,
            response_time_seconds INTEGER,
            FOREIGN KEY (quiz_id) REFERENCES quiz_history (quiz_id)
        )
        ''')
        
        # Bảng learning_path - lưu lộ trình học
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_path (
            path_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            suggested_topics TEXT,
            proficiency_levels TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def register_user(self, username, password):
        """Đăng ký người dùng mới"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Hash mật khẩu
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Thêm người dùng mới
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
            
            user_id = cursor.lastrowid
            
            # Tạo preferences mặc định
            cursor.execute(
                "INSERT INTO user_preferences (user_id, preferred_languages, preferred_topics) VALUES (?, ?, ?)",
                (user_id, json.dumps(["Python"]), json.dumps(["Cơ bản"]))
            )
            
            # Tạo learning path mặc định
            cursor.execute(
                "INSERT INTO learning_path (user_id, suggested_topics, proficiency_levels) VALUES (?, ?, ?)",
                (user_id, json.dumps(["Python cơ bản"]), json.dumps({"Python": "beginner"}))
            )
            
            conn.commit()
            conn.close()
            return {"success": True, "user_id": user_id}
        except sqlite3.IntegrityError:
            return {"success": False, "error": "Tên người dùng đã tồn tại"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def login_user(self, username, password):
        """Đăng nhập người dùng"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Hash mật khẩu
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Kiểm tra thông tin đăng nhập
            cursor.execute(
                "SELECT user_id FROM users WHERE username = ? AND password_hash = ?",
                (username, password_hash)
            )
            
            result = cursor.fetchone()
            
            if result:
                user_id = result[0]
                # Cập nhật thời gian đăng nhập cuối
                cursor.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (user_id,)
                )
                conn.commit()
                conn.close()
                return {"success": True, "user_id": user_id}
            else:
                conn.close()
                return {"success": False, "error": "Tên đăng nhập hoặc mật khẩu không đúng"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def save_quiz_result(self, user_id, language, topic, score, total_questions, 
                         duration_seconds, questions_data, user_answers, difficulty_level="beginner"):
        """Lưu kết quả bài kiểm tra"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Lưu thông tin quiz
            cursor.execute(
                """INSERT INTO quiz_history 
                   (user_id, language, topic, score, total_questions, duration_seconds, difficulty_level, questions_data) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, language, topic, score, total_questions, duration_seconds, 
                 difficulty_level, json.dumps(questions_data))
            )
            
            quiz_id = cursor.lastrowid
            
            # Lưu chi tiết từng câu trả lời
            for i, question in enumerate(questions_data):
                is_correct = user_answers[i] == question['correct_answer']
                # Ở đây, bạn có thể thêm response_time_seconds nếu bạn muốn theo dõi thời gian trả lời cho từng câu
                cursor.execute(
                    """INSERT INTO question_responses 
                       (quiz_id, question_index, question_text, user_answer, correct_answer, is_correct, response_time_seconds) 
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (quiz_id, i, question['question'], user_answers[i], question['correct_answer'], 
                     is_correct, 0)  # response_time_seconds có thể cập nhật sau
                )
            
            conn.commit()
            
            # Cập nhật lộ trình học dựa trên kết quả
            self.update_learning_path(user_id, language, topic, score, total_questions)
            
            conn.close()
            return {"success": True, "quiz_id": quiz_id}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_learning_path(self, user_id, language, topic, score, total_questions):
        """Cập nhật lộ trình học dựa trên kết quả bài kiểm tra"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Lấy thông tin lộ trình hiện tại
            cursor.execute(
                "SELECT suggested_topics, proficiency_levels FROM learning_path WHERE user_id = ?",
                (user_id,)
            )
            
            result = cursor.fetchone()
            
            if result:
                suggested_topics = json.loads(result[0])
                proficiency_levels = json.loads(result[1])
                
                # Tính toán mức độ thành thạo mới
                score_percentage = (score / total_questions) * 100
                
                if language in proficiency_levels:
                    current_level = proficiency_levels[language]
                    
                    # Cập nhật mức độ thành thạo
                    if current_level == "beginner" and score_percentage >= 80:
                        proficiency_levels[language] = "intermediate"
                    elif current_level == "intermediate" and score_percentage >= 80:
                        proficiency_levels[language] = "advanced"
                else:
                    # Khởi tạo mức độ thành thạo cho ngôn ngữ mới
                    if score_percentage >= 80:
                        proficiency_levels[language] = "intermediate"
                    else:
                        proficiency_levels[language] = "beginner"
                
                # Cập nhật đề xuất chủ đề
                if score_percentage < 60:
                    # Nếu điểm số thấp, đề xuất ôn tập lại chủ đề hiện tại
                    if f"{language} - {topic} (Ôn tập)" not in suggested_topics:
                        suggested_topics.append(f"{language} - {topic} (Ôn tập)")
                elif score_percentage >= 80 and proficiency_levels[language] == "intermediate":
                    # Nếu điểm cao và ở mức trung cấp, đề xuất các chủ đề nâng cao
                    advanced_topics = {
                        "Python": ["OOP", "Advanced Functions", "Decorators", "Generators"],
                        "JavaScript": ["Closures", "Promises", "Async/Await", "Functional Programming"],
                        "Java": ["Multithreading", "Collections", "Generics", "Design Patterns"]
                    }
                    
                    if language in advanced_topics:
                        for adv_topic in advanced_topics[language]:
                            if f"{language} - {adv_topic}" not in suggested_topics:
                                suggested_topics.append(f"{language} - {adv_topic}")
                
                # Cập nhật lộ trình học
                cursor.execute(
                    """UPDATE learning_path 
                       SET suggested_topics = ?, proficiency_levels = ?, last_updated = CURRENT_TIMESTAMP 
                       WHERE user_id = ?""",
                    (json.dumps(suggested_topics), json.dumps(proficiency_levels), user_id)
                )
                
                conn.commit()
            
            conn.close()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_user_quiz_history(self, user_id):
        """Lấy lịch sử làm bài quiz của người dùng"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Chuyển đổi kết quả truy vấn thành DataFrame
            query = f"""
            SELECT quiz_id, language, topic, score, total_questions, 
                   duration_seconds, quiz_date, difficulty_level
            FROM quiz_history
            WHERE user_id = {user_id}
            ORDER BY quiz_date DESC
            """
            
            history_df = pd.read_sql_query(query, conn)
            conn.close()
            
            return {"success": True, "history": history_df.to_dict(orient='records')}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_user_statistics(self, user_id):
        """Lấy thống kê tổng quan của người dùng"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Số lượng bài kiểm tra đã làm
            cursor.execute(
                "SELECT COUNT(*) FROM quiz_history WHERE user_id = ?",
                (user_id,)
            )
            total_quizzes = cursor.fetchone()[0]
            
            # Tổng số câu hỏi đã trả lời
            cursor.execute(
                "SELECT SUM(total_questions), SUM(score) FROM quiz_history WHERE user_id = ?",
                (user_id,)
            )
            result = cursor.fetchone()
            total_questions = result[0] if result[0] else 0
            total_correct = result[1] if result[1] else 0
            
            # Tính tỷ lệ chính xác
            accuracy = (total_correct / total_questions) * 100 if total_questions > 0 else 0
            
            # Thống kê theo ngôn ngữ
            cursor.execute(
                """
                SELECT language, AVG(score * 100.0 / total_questions) as avg_score, COUNT(*) as count
                FROM quiz_history
                WHERE user_id = ?
                GROUP BY language
                """,
                (user_id,)
            )
            language_stats = []
            for row in cursor.fetchall():
                language_stats.append({
                    "language": row[0],
                    "average_score": row[1],
                    "quiz_count": row[2]
                })
            
            # Thống kê theo chủ đề
            cursor.execute(
                """
                SELECT topic, AVG(score * 100.0 / total_questions) as avg_score, COUNT(*) as count
                FROM quiz_history
                WHERE user_id = ?
                GROUP BY topic
                """,
                (user_id,)
            )
            topic_stats = []
            for row in cursor.fetchall():
                topic_stats.append({
                    "topic": row[0],
                    "average_score": row[1],
                    "quiz_count": row[2]
                })
            
            # Lấy thông tin lộ trình học
            cursor.execute(
                "SELECT suggested_topics, proficiency_levels FROM learning_path WHERE user_id = ?",
                (user_id,)
            )
            
            learning_path_result = cursor.fetchone()
            suggested_topics = json.loads(learning_path_result[0]) if learning_path_result else []
            proficiency_levels = json.loads(learning_path_result[1]) if learning_path_result else {}
            
            conn.close()
            
            return {
                "success": True,
                "statistics": {
                    "total_quizzes": total_quizzes,
                    "total_questions": total_questions,
                    "total_correct": total_correct,
                    "accuracy": accuracy,
                    "language_stats": language_stats,
                    "topic_stats": topic_stats,
                    "suggested_topics": suggested_topics,
                    "proficiency_levels": proficiency_levels
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_user_preferences(self, user_id, preferred_languages=None, preferred_topics=None, difficulty_level=None):
        """Cập nhật tùy chọn của người dùng"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Lấy tùy chọn hiện tại
            cursor.execute(
                "SELECT preferred_languages, preferred_topics, difficulty_level FROM user_preferences WHERE user_id = ?",
                (user_id,)
            )
            
            result = cursor.fetchone()
            
            if result:
                current_languages = json.loads(result[0])
                current_topics = json.loads(result[1])
                current_difficulty = result[2]
                
                # Cập nhật nếu có thay đổi
                if preferred_languages is not None:
                    current_languages = preferred_languages
                
                if preferred_topics is not None:
                    current_topics = preferred_topics
                
                if difficulty_level is not None:
                    current_difficulty = difficulty_level
                
                # Lưu thay đổi
                cursor.execute(
                    """UPDATE user_preferences 
                       SET preferred_languages = ?, preferred_topics = ?, difficulty_level = ?, last_updated = CURRENT_TIMESTAMP 
                       WHERE user_id = ?""",
                    (json.dumps(current_languages), json.dumps(current_topics), current_difficulty, user_id)
                )
            else:
                # Nếu chưa có preferences, tạo mới
                cursor.execute(
                    """INSERT INTO user_preferences 
                       (user_id, preferred_languages, preferred_topics, difficulty_level) 
                       VALUES (?, ?, ?, ?)""",
                    (user_id, 
                     json.dumps(preferred_languages if preferred_languages else ["Python"]), 
                     json.dumps(preferred_topics if preferred_topics else ["Cơ bản"]), 
                     difficulty_level if difficulty_level else "beginner")
                )
            
            conn.commit()
            conn.close()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_user_preferences(self, user_id):
        """Lấy tùy chọn của người dùng"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT preferred_languages, preferred_topics, difficulty_level FROM user_preferences WHERE user_id = ?",
                (user_id,)
            )
            
            result = cursor.fetchone()
            
            if result:
                preferences = {
                    "preferred_languages": json.loads(result[0]),
                    "preferred_topics": json.loads(result[1]),
                    "difficulty_level": result[2]
                }
                
                conn.close()
                return {"success": True, "preferences": preferences}
            else:
                conn.close()
                return {"success": False, "error": "Không tìm thấy tùy chọn người dùng"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_learning_path(self, user_id):
        """Lấy lộ trình học của người dùng"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT suggested_topics, proficiency_levels, last_updated FROM learning_path WHERE user_id = ?",
                (user_id,)
            )
            
            result = cursor.fetchone()
            
            if result:
                learning_path = {
                    "suggested_topics": json.loads(result[0]),
                    "proficiency_levels": json.loads(result[1]),
                    "last_updated": result[2]
                }
                
                conn.close()
                return {"success": True, "learning_path": learning_path}
            else:
                conn.close()
                return {"success": False, "error": "Không tìm thấy lộ trình học"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_question_performance(self, user_id, language=None, topic=None):
        """Lấy thông tin hiệu suất trả lời câu hỏi theo ngôn ngữ/chủ đề"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Xây dựng câu truy vấn
            query = f"""
            SELECT qr.question_text, 
                   SUM(qr.is_correct) AS correct_count,
                   COUNT(*) AS total_attempts,
                   (SUM(qr.is_correct) * 100.0 / COUNT(*)) AS accuracy
            FROM question_responses qr
            JOIN quiz_history qh ON qr.quiz_id = qh.quiz_id
            WHERE qh.user_id = {user_id}
            """
            
            params = []
            if language:
                query += " AND qh.language = ?"
                params.append(language)
            
            if topic:
                query += " AND qh.topic = ?"
                params.append(topic)
            
            query += " GROUP BY qr.question_text ORDER BY accuracy ASC"
            
            # Chuyển đổi kết quả truy vấn thành DataFrame
            performance_df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            return {"success": True, "performance": performance_df.to_dict(orient='records')}
        except Exception as e:
            return {"success": False, "error": str(e)}