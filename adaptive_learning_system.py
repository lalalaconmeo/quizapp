import json
from openai import OpenAI

class AdaptiveLearningSystem:
    def __init__(self, client, user_data_manager):
        """Khởi tạo hệ thống học tập thích ứng"""
        self.client = client
        self.user_data_manager = user_data_manager
        
        # Định nghĩa các cấp độ khó
        self.difficulty_levels = ["beginner", "intermediate", "advanced", "expert"]
        
        # Định nghĩa các chủ đề theo ngôn ngữ và độ khó
        self.topic_map = {
            "Python": {
                "beginner": ["Cú pháp cơ bản", "Biến và kiểu dữ liệu", "Câu lệnh điều kiện", "Vòng lặp", "Hàm cơ bản"],
                "intermediate": ["Hàm nâng cao", "List Comprehension", "Xử lý ngoại lệ", "File I/O", "Modules và Packages", "OOP cơ bản"],
                "advanced": ["OOP nâng cao", "Decorators", "Generators", "Context Managers", "Multithreading", "Multiprocessing", "Regular Expressions"],
                "expert": ["Metaprogramming", "Design Patterns", "Asynchronous Programming", "Memory Management", "Performance Optimization"]
            },
            "JavaScript": {
                "beginner": ["Cú pháp cơ bản", "Biến và kiểu dữ liệu", "Câu lệnh điều kiện", "Vòng lặp", "Hàm cơ bản"],
                "intermediate": ["Hàm nâng cao", "Closures", "DOM Manipulation", "Event Handling", "JSON", "AJAX"],
                "advanced": ["Promises", "Async/Await", "ES6+ Features", "Functional Programming", "Prototypes", "Modules"],
                "expert": ["Design Patterns", "Performance Optimization", "Memory Leaks", "Web Components", "WebGL", "Service Workers"]
            },
            "Java": {
                "beginner": ["Cú pháp cơ bản", "Biến và kiểu dữ liệu", "Câu lệnh điều kiện", "Vòng lặp", "Phương thức"],
                "intermediate": ["OOP", "Inheritance", "Polymorphism", "Interfaces", "Exceptions", "Collections"],
                "advanced": ["Generics", "Multithreading", "I/O Streams", "JDBC", "Annotations", "Lambda Expressions"],
                "expert": ["Design Patterns", "Reflection", "Concurrency", "Memory Management", "JVM Internals", "Performance Tuning"]
            }
        }
    
    def generate_questions_with_difficulty(self, language, topic, difficulty, num_questions=10):
        """Tạo câu hỏi với độ khó cụ thể"""
        difficulty_prompts = {
            "beginner": "các câu hỏi cơ bản, đơn giản, tập trung vào kiến thức nền tảng",
            "intermediate": "các câu hỏi mức trung bình, yêu cầu hiểu biết tốt về ngôn ngữ và chủ đề",
            "advanced": "các câu hỏi nâng cao, có độ phức tạp cao, bao gồm một số đoạn mã để phân tích và hiểu khái niệm chi tiết",
            "expert": "các câu hỏi cực kỳ khó, phức tạp, có thể bao gồm nhiều đoạn mã, trường hợp đặc biệt và các khái niệm chuyên sâu"
        }
        
        # Thêm độ phức tạp vào prompt dựa trên mức độ
        prompt_addition = difficulty_prompts.get(difficulty, difficulty_prompts["beginner"])
        
        # Điều chỉnh prompt dựa trên độ khó
        prompt = f"""Hãy tạo {num_questions} câu hỏi trắc nghiệm bằng tiếng Việt về ngôn ngữ lập trình {language}, 
        tập trung vào chủ đề {topic}. Yêu cầu tạo {prompt_addition}.
        
        """
        
        # Thêm yêu cầu code snippet cho mức intermediate trở lên
        if difficulty != "beginner":
            prompt += """Hãy thêm đoạn mã (code snippet) vào ít nhất 50% câu hỏi. Đoạn mã phải được định dạng rõ ràng. Độ khó 2 năm kinh nghiệm IT
            """
        
        # Thêm yêu cầu câu hỏi nhiều phần cho mức advanced và expert
        if difficulty in ["advanced", "expert"]:
            prompt += """Ít nhất 30% câu hỏi phải là câu hỏi nhiều phần (multi-part questions), 
            yêu cầu hiểu biết về nhiều khái niệm để trả lời chính xác. Độ khó cỡ 5 năm kinh nghiệm IT
            """
        
        # Định dạng JSON
        prompt += """Định dạng JSON như sau:
        {
            "questions": [
                {
                    "question": "Nội dung câu hỏi?",
                    "choices": [
                        "A. Đáp án A",
                        "B. Đáp án B", 
                        "C. Đáp án C",
                        "D. Đáp án D"
                    ],
                    "correct_answer": "A. Đáp án A",
                    "explanation": "Giải thích tại sao đây là đáp án đúng",
                    "difficulty": "%s"
                }
            ]
        }""" % difficulty

        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini-2025-04-14",
                messages=[
                    {"role": "system", "content": "Bạn là chuyên gia tạo câu hỏi trắc nghiệm về lập trình bằng tiếng Việt với các mức độ khó khác nhau."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )

            quiz_data = json.loads(response.choices[0].message.content)
            return quiz_data['questions']
        except Exception as e:
            print(f"Lỗi khi tạo câu hỏi: {e}")
            return []
    
    def calculate_user_performance(self, user_id, language, recent_quizzes=5):
        """Tính toán hiệu suất gần đây của người dùng"""
        user_history = self.user_data_manager.get_user_quiz_history(user_id)
        
        if not user_history["success"]:
            return {"avg_score": 0, "difficulty_level": "beginner"}
        
        # Lọc quiz theo ngôn ngữ và sắp xếp theo thời gian
        language_quizzes = [q for q in user_history["history"] if q["language"] == language]
        language_quizzes = sorted(language_quizzes, key=lambda x: x["quiz_date"], reverse=True)[:recent_quizzes]
        
        if not language_quizzes:
            return {"avg_score": 0, "difficulty_level": "beginner"}
        
        # Tính điểm trung bình
        total_score_percent = sum(q["score"] * 100 / q["total_questions"] for q in language_quizzes)
        avg_score = total_score_percent / len(language_quizzes)
        
        # Xác định mức độ khó dựa trên điểm số trung bình
        difficulty_level = "beginner"
        if avg_score >= 85:
            difficulty_level = "expert"
        elif avg_score >= 70:
            difficulty_level = "advanced"
        elif avg_score >= 50:
            difficulty_level = "intermediate"
        
        return {"avg_score": avg_score, "difficulty_level": difficulty_level}
    
    def determine_next_difficulty(self, user_id, language, current_difficulty, score, total_questions):
        """Xác định độ khó tiếp theo dựa trên kết quả bài kiểm tra hiện tại"""
        score_percent = (score / total_questions) * 100
        
        # Lấy chỉ số hiện tại trong danh sách độ khó
        current_index = self.difficulty_levels.index(current_difficulty)
        
        # Quyết định tăng/giảm độ khó
        if score_percent >= 80 and current_index < len(self.difficulty_levels) - 1:
            # Nếu điểm cao, tăng độ khó
            return self.difficulty_levels[current_index + 1]
        elif score_percent < 40 and current_index > 0:
            # Nếu điểm thấp, giảm độ khó
            return self.difficulty_levels[current_index - 1]
        else:
            # Giữ nguyên độ khó
            return current_difficulty
    
    def generate_personalized_quiz(self, user_id, language, topic=None):
        """Tạo bài kiểm tra được cá nhân hóa dựa trên hiệu suất người dùng"""
        # Lấy thông tin người dùng
        user_prefs = self.user_data_manager.get_user_preferences(user_id)
        
        if not user_prefs["success"]:
            # Nếu không có thông tin, bắt đầu ở mức beginner
            difficulty = "beginner"
        else:
            difficulty = user_prefs["preferences"]["difficulty_level"]
        
        # Nếu không chỉ định chủ đề, chọn chủ đề phù hợp
        if not topic:
            # Lấy lộ trình học
            learning_path = self.user_data_manager.get_learning_path(user_id)
            
            if learning_path["success"] and learning_path["learning_path"]["suggested_topics"]:
                # Chọn chủ đề đầu tiên từ các đề xuất
                suggested = learning_path["learning_path"]["suggested_topics"][0]
                if language in suggested:
                    topic = suggested.split(" - ")[1].split(" (")[0]  # Trích xuất chủ đề từ chuỗi đề xuất
            
            # Nếu vẫn không có chủ đề, chọn chủ đề ngẫu nhiên phù hợp với độ khó
            if not topic and language in self.topic_map and difficulty in self.topic_map[language]:
                import random
                topic = random.choice(self.topic_map[language][difficulty])
        
        # Tính toán hiệu suất gần đây để điều chỉnh độ khó
        performance = self.calculate_user_performance(user_id, language)
        suggested_difficulty = performance["difficulty_level"]
        
        # Nếu hiệu suất cao hơn mức hiện tại, điều chỉnh
        if self.difficulty_levels.index(suggested_difficulty) > self.difficulty_levels.index(difficulty):
            difficulty = suggested_difficulty
        
        # Tạo quiz với độ khó phù hợp
        questions = self.generate_questions_with_difficulty(language, topic, difficulty)
        
        return {
            "questions": questions,
            "language": language,
            "topic": topic,
            "difficulty": difficulty
        }
    
    def suggest_learning_path(self, user_id):
        """Đề xuất lộ trình học dựa trên hiệu suất"""
        # Lấy thống kê hiệu suất người dùng
        stats = self.user_data_manager.get_user_statistics(user_id)
        
        if not stats["success"]:
            return {"success": False, "error": "Không thể lấy thống kê người dùng"}
        
        statistics = stats["statistics"]
        
        # Tìm các chủ đề yếu nhất
        weak_topics = []
        for topic_stat in statistics["topic_stats"]:
            if topic_stat["average_score"] < 60:
                weak_topics.append(topic_stat["topic"])
        
        # Tìm ngôn ngữ mạnh nhất
        strongest_language = None
        highest_score = 0
        for lang_stat in statistics["language_stats"]:
            if lang_stat["average_score"] > highest_score:
                highest_score = lang_stat["average_score"]
                strongest_language = lang_stat["language"]
        
        # Tạo đề xuất cá nhân hóa
        suggestions = []
        proficiency_levels = statistics["proficiency_levels"]
        
        # Đề xuất ôn tập các chủ đề yếu
        for topic in weak_topics:
            suggestions.append(f"Ôn tập lại {topic} để cải thiện hiểu biết")
        
        # Đề xuất chủ đề nâng cao cho ngôn ngữ mạnh nhất
        if strongest_language:
            current_level = proficiency_levels.get(strongest_language, "beginner")
            next_level_index = min(self.difficulty_levels.index(current_level) + 1, len(self.difficulty_levels) - 1)
            next_level = self.difficulty_levels[next_level_index]
            
            if next_level in self.topic_map.get(strongest_language, {}):
                next_topics = self.topic_map[strongest_language][next_level]
                if next_topics:
                    suggestions.append(f"Học {strongest_language} ở mức {next_level} với các chủ đề: {', '.join(next_topics[:3])}")
        
        # Đề xuất thử thách
        if highest_score > 80:
            suggestions.append("Thử thách bản thân với các bài tập dự án thực tế để vận dụng kiến thức")
        
        return {
            "success": True,
            "suggestions": suggestions,
            "weak_topics": weak_topics,
            "strongest_language": strongest_language,
            "proficiency_levels": proficiency_levels
        }
    
    def generate_explanation(self, language, topic, question, user_answer, correct_answer, is_correct):
        """Tạo giải thích chi tiết cho câu trả lời của người dùng"""
        prompt = f"""Hãy cung cấp giải thích chi tiết về câu hỏi sau đây về {language} liên quan đến {topic}:
        
        Câu hỏi: {question}
        
        Đáp án người dùng: {user_answer}
        Đáp án đúng: {correct_answer}
        
        {"Người dùng đã trả lời đúng. Hãy cung cấp giải thích sâu hơn và các kiến thức bổ sung liên quan." 
          if is_correct else 
          "Người dùng đã trả lời sai. Hãy giải thích tại sao đáp án của họ không đúng và tại sao đáp án đúng lại là chính xác."}
        
        Hãy cung cấp:
        1. Giải thích chi tiết
        2. Ví dụ minh họa (nếu phù hợp)
        3. Gợi ý để hiểu khái niệm tốt hơn
        4. Nguồn tài liệu để tìm hiểu thêm (nếu có)"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini-2025-04-14",
                messages=[
                    {"role": "system", "content": "Bạn là một giáo viên lập trình giỏi, chuyên giúp học sinh hiểu sâu các khái niệm."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Lỗi khi tạo giải thích: {e}")
            return "Không thể tạo giải thích chi tiết. Vui lòng thử lại sau."
    
    def generate_hint(self, question, choices):
        """Tạo gợi ý học thuật cho câu hỏi hiện tại"""
        prompt = f"""Hãy đưa ra một gợi ý học thuật ngắn gọn, rõ ràng cho câu hỏi sau đây:

        Câu hỏi: {question}

        HƯỚNG DẪN QUAN TRỌNG:
        1. TUYỆT ĐỐI KHÔNG tiết lộ hoặc ngụ ý về đáp án đúng
        2. Giữ gợi ý DƯỚI 100 từ và tối đa 2 câu
        3. Đưa ra gợi ý về khái niệm hoặc kỹ thuật liên quan, không phải đáp án
        4. Không đề cập đến bất kỳ lựa chọn cụ thể nào trong các phương án
        5. Viết gợi ý theo phong cách giáo viên định hướng chứ không cung cấp đáp án
        """
    
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini-2025-04-14",
                messages=[
                    {"role": "system", "content": "Bạn là một giáo sư lập trình giỏi, chuyên cung cấp gợi ý hữu ích nhưng KHÔNG BAO GIỜ tiết lộ đáp án. Gợi ý của bạn phải rất ngắn gọn và không tiết lộ đáp án."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=150
            )
        
            hint = response.choices[0].message.content
            # Cắt bớt nếu quá dài
            if len(hint) > 1500:
                hint = hint[:1470] + "..."
            
            return hint
        except Exception as e:
            print(f"Lỗi khi tạo gợi ý: {e}")
            return "Hãy nhớ lại các khái niệm cơ bản về chủ đề này."