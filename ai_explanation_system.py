class AIExplanationSystem:
    def __init__(self, client, adaptive_learning_system):
        """Khởi tạo hệ thống giải thích AI"""
        self.client = client
        self.adaptive_learning_system = adaptive_learning_system
    
    def get_explanation(self, language, topic, question, user_answer, correct_answer, is_correct):
        """Lấy giải thích chi tiết từ hệ thống học tập thích ứng"""
        return self.adaptive_learning_system.generate_explanation(
            language, topic, question, user_answer, correct_answer, is_correct
        )
    
    def get_hint(self, question, choices):
        """Lấy gợi ý từ hệ thống học tập thích ứng"""
        return self.adaptive_learning_system.generate_hint(question, choices)
    
    def generate_follow_up_question(self, language, topic, question, is_correct):
        """Tạo câu hỏi tiếp theo dựa trên câu trả lời của người dùng"""
        direction = "khó hơn" if is_correct else "dễ hơn và liên quan"
        
        prompt = f"""Dựa trên câu hỏi sau về {language} liên quan đến chủ đề {topic}:
        
        {question}
        
        Hãy tạo một câu hỏi mở {direction} để giúp người dùng {"củng cố kiến thức nâng cao" if is_correct else "hiểu rõ hơn về khái niệm cơ bản"}. 
        Câu hỏi nên mở rộng hiểu biết của họ và không chỉ là trắc nghiệm."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini-2025-04-14",
                messages=[
                    {"role": "system", "content": "Bạn là một giáo viên lập trình giỏi, chuyên đưa ra các câu hỏi thách thức để mở rộng hiểu biết của học sinh."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens= 500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Lỗi khi tạo câu hỏi tiếp theo: {e}")
            return "Không thể tạo câu hỏi tiếp theo. Vui lòng thử lại sau."
    
    def generate_code_review(self, language, code_snippet):
        """Phân tích và đưa ra nhận xét về đoạn mã của người dùng"""
        prompt = f"""Hãy phân tích đoạn mã {language} sau đây và đưa ra nhận xét chi tiết:
        
        ```{language}
        {code_snippet}
        ```
        
        Nhận xét nên bao gồm:
        1. Đoạn mã có hoạt động đúng không?
        2. Có vấn đề về hiệu suất, bảo mật, hoặc khả năng bảo trì không?
        3. Cách cải thiện mã (nếu có)
        4. Các thực hành tốt liên quan
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini-2025-04-14",
                messages=[
                    {"role": "system", "content": f"Bạn là một chuyên gia đánh giá mã {language}, giỏi về phát hiện vấn đề và đưa ra gợi ý cải thiện."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Lỗi khi tạo nhận xét mã: {e}")
            return "Không thể phân tích mã. Vui lòng thử lại sau."
    
    def get_concept_explanation(self, language, concept):
        """Cung cấp giải thích chi tiết về một khái niệm lập trình"""
        prompt = f"""Hãy giải thích chi tiết về khái niệm "{concept}" trong ngôn ngữ lập trình {language}.
        
        Giải thích nên bao gồm:
        1. Định nghĩa và mục đích
        2. Cú pháp và cách sử dụng
        3. Ví dụ minh họa
        4. Các trường hợp sử dụng phổ biến
        5. Các lỗi thường gặp và cách tránh
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini-2025-04-14",
                messages=[
                    {"role": "system", "content": "Bạn là một giáo viên lập trình giàu kinh nghiệm, giỏi về giải thích các khái niệm phức tạp một cách đơn giản."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Lỗi khi tạo giải thích khái niệm: {e}")
            return "Không thể giải thích khái niệm. Vui lòng thử lại sau."