import streamlit as st
from openai import OpenAI
import json
import time
from datetime import datetime, timedelta
from gtts import gTTS
import os
import pygame
import threading
from streamlit_lottie import st_lottie
import requests
import random
import pandas as pd
import matplotlib.pyplot as plt
import hashlib
import re
import base64
from io import StringIO, BytesIO
import sys

# Import các lớp từ module khác
from user_data_manager import UserDataManager
from adaptive_learning_system import AdaptiveLearningSystem
from ai_explanation_system import AIExplanationSystem
from code_execution_system import CodeExecutionSystem

# Khởi tạo OpenAI client
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY"))

# Khởi tạo các hệ thống
user_data_manager = UserDataManager()
adaptive_learning_system = AdaptiveLearningSystem(client, user_data_manager)
ai_explanation_system = AIExplanationSystem(client, adaptive_learning_system)
code_execution_system = CodeExecutionSystem(client)

def load_lottieurl(url):
    """Tải animation từ URL"""
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Khởi tạo pygame mixer cho audio
try:
    pygame.mixer.init(frequency=44100)
except Exception as e:
    print(f"Không thể khởi tạo pygame mixer: {e}")

class AdvancedProgrammingQuizApp:
    def __init__(self):
        """Khởi tạo ứng dụng quiz lập trình nâng cao"""
        # Dọn dẹp các file tạm từ lần chạy trước
        temp_dir = "temp_audio"
        if os.path.exists(temp_dir):
            try:
                for file in os.listdir(temp_dir):
                    if file.endswith(".mp3"):
                        os.remove(os.path.join(temp_dir, file))
            except:
                pass
        else:
            os.makedirs(temp_dir)
            
        # Khởi tạo trạng thái phiên
        if 'questions' not in st.session_state:
            st.session_state.questions = []
        if 'current_question' not in st.session_state:
            st.session_state.current_question = 0
        if 'quiz_started' not in st.session_state:
            st.session_state.quiz_started = False
        if 'score' not in st.session_state:
            st.session_state.score = 0
        if 'start_time' not in st.session_state:
            st.session_state.start_time = None
        if 'fifty_fifty_used' not in st.session_state:
            st.session_state.fifty_fifty_used = False
        if 'current_choices' not in st.session_state:
            st.session_state.current_choices = None
        if 'has_answered' not in st.session_state:
            st.session_state.has_answered = False
        if 'user_answers' not in st.session_state:
            st.session_state.user_answers = []
        if 'last_language' not in st.session_state:
            st.session_state.last_language = ""
        if 'last_topic' not in st.session_state:
            st.session_state.last_topic = ""
        if 'show_results' not in st.session_state:
            st.session_state.show_results = False
        if 'is_speaking' not in st.session_state:
            st.session_state.is_speaking = False
        if 'question_read' not in st.session_state:
            st.session_state.question_read = False
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False
        if 'user_id' not in st.session_state:
            st.session_state.user_id = None
        if 'current_difficulty' not in st.session_state:
            st.session_state.current_difficulty = "beginner"
        if 'hint_used' not in st.session_state:
            st.session_state.hint_used = False
        if 'current_hint' not in st.session_state:
            st.session_state.current_hint = None
        if 'code_editor_content' not in st.session_state:
            st.session_state.code_editor_content = ""
        if 'code_execution_result' not in st.session_state:
            st.session_state.code_execution_result = None
        if 'debug_message' not in st.session_state:
            st.session_state.debug_message = None
        if 'debug_audio_error' not in st.session_state:
            st.session_state.debug_audio_error = None
        if 'debug_tts_error' not in st.session_state:
            st.session_state.debug_tts_error = None

    def speak_text(self, text, block=True):
        """Đọc văn bản bằng Google TTS với phương pháp đồng bộ cho Streamlit"""
        if st.session_state.is_speaking:
            return

        # Tạo thư mục temp nếu chưa tồn tại
        temp_dir = "temp_audio"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        st.session_state.is_speaking = True
    
        try:
            # Tạo file âm thanh với gTTS
            temp_file = os.path.join(temp_dir, f"audio_{int(time.time())}.mp3")
            tts = gTTS(text=text, lang='vi', slow=False)
            tts.save(temp_file)
        
            # Kiểm tra nếu quiz vẫn đang hoạt động
            if not st.session_state.quiz_started:
                try:
                    os.remove(temp_file)
                except:
                    pass
                st.session_state.is_speaking = False
                return
            
            # Đảm bảo mixer được khởi tạo
            try:
                if pygame.mixer.get_init() is None:
                    pygame.mixer.init(frequency=44100)
            
                # Phát âm thanh
                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.play()
            
                # Đợi phát xong nếu yêu cầu
                if block:
                    while pygame.mixer.music.get_busy() and st.session_state.quiz_started:
                        time.sleep(0.1)
                
                    # Dọn dẹp sau khi phát xong
                    try:
                        pygame.mixer.music.stop()
                        os.remove(temp_file)
                    except:
                        pass
            except Exception as audio_error:
                st.session_state.debug_audio_error = str(audio_error)
    
        except Exception as e:
            st.session_state.debug_tts_error = str(e)
    
        finally:
            # Đặt lại trạng thái is_speaking nếu đã phát xong (chế độ đồng bộ)
            if block:
                st.session_state.is_speaking = False

    def read_question_and_choices(self, question):
        """Đọc câu hỏi và lựa chọn theo cách đồng bộ"""
        if not st.session_state.question_read and st.session_state.quiz_started:
            try:
                # Định dạng văn bản câu hỏi trước
                question_text = question['question']
            
                # Loại bỏ code snippets
                if "```" in question_text:
                    parts = question_text.split("```")
                    question_text = parts[0]
                    if len(parts) > 2:
                        question_text += " " + " ".join(parts[2:])
            
                # Tạo văn bản đầy đủ với khoảng dừng thích hợp
                full_text = f"Câu hỏi: {question_text}. "
                full_text += "Các lựa chọn: "
            
                for choice in question['choices']:
                    # Loại bỏ code trong lựa chọn
                    choice_text = choice
                    if "```" in choice:
                        choice_parts = choice.split("```")
                        choice_text = choice_parts[0]
                        if len(choice_parts) > 2:
                            choice_text += choice_parts[2]
                
                    full_text += f"{choice_text}. "
            
                # Đọc văn bản theo cách đồng bộ
                self.speak_text(full_text, block=True)
            
                # Đánh dấu câu hỏi đã được đọc
                st.session_state.question_read = True
            
            except Exception as e:
                # Lưu lỗi vào session state thay vì hiển thị trực tiếp
                st.session_state.debug_tts_error = str(e)

    def generate_programming_mcq(self, language, topic):
        """Tạo câu hỏi trắc nghiệm theo ngôn ngữ và chủ đề"""
        if st.session_state.logged_in:
            # Sử dụng hệ thống học tập thích ứng cho người dùng đã đăng nhập
            quiz_data = adaptive_learning_system.generate_personalized_quiz(
                st.session_state.user_id, language, topic
            )
            st.session_state.current_difficulty = quiz_data["difficulty"]
            
            # Check if questions were successfully generated
            if not quiz_data["questions"]:
                st.error("Không thể tạo câu hỏi. Vui lòng thử lại với độ khó khác.")
                return []
            
            # Validate và sửa câu hỏi
            quiz_data["questions"] = self.validate_and_fix_questions(quiz_data["questions"])
                
            return quiz_data["questions"]
        else:
            # Sử dụng phương thức với độ khó đã chọn cho người dùng chưa đăng nhập
            return self.generate_programming_mcq_with_difficulty(language, topic, st.session_state.current_difficulty)

    def validate_and_fix_questions(self, questions):
        """Kiểm tra và sửa các câu hỏi để đảm bảo đúng định dạng trắc nghiệm"""
        for question in questions:
            # Kiểm tra nếu câu hỏi yêu cầu viết code
            if any(phrase in question['question'].lower() for phrase in 
                ["viết đoạn", "viết code", "viết mã", "hãy viết", "coding", "code để", "viết một", "viết chương trình"]):
                # Định dạng lại thành câu hỏi "đâu là code"
                question['question'] = question['question'].replace("Viết", "Đâu là").replace("viết", "đâu là")
                question['question'] = question['question'].replace("Hãy code", "Đâu là code đúng").replace("hãy code", "đâu là code đúng")
                if not any(word in question['question'].lower() for word in ["đâu là", "chọn", "nào là"]):
                    question['question'] = "Đâu là đoạn mã đúng để " + question['question']
                
                # Kiểm tra xem đáp án có phải là kết quả (số) trong khi câu hỏi yêu cầu code hay không
                if "đoạn mã" in question['question'].lower() or "đoạn code" in question['question'].lower():
                    numeric_answers = True
                    for choice in question['choices']:
                        # Lấy chỉ phần văn bản (không phải mã code)
                        choice_text = choice.split("```")[0] if "```" in choice else choice
                        
                        # Kiểm tra xem đáp án có chứa code hay không
                        if any(code_keyword in choice.lower() for code_keyword in ["for ", "while ", "if ", "def ", "class ", "import ", "=", ">"]):
                            numeric_answers = False
                            break
                    
                    # Nếu các đáp án là số nhưng câu hỏi yêu cầu code, thay đổi câu hỏi
                    if numeric_answers:
                        question['question'] = question['question'].replace("Đâu là đoạn mã", "Kết quả của đoạn mã")
                        question['question'] = question['question'].replace("đoạn code", "đoạn mã")
                        question['question'] = question['question'].replace("Đâu là mã", "Kết quả của mã")
            
            # Đảm bảo câu hỏi có 4 lựa chọn
            if len(question['choices']) != 4:
                while len(question['choices']) < 4:
                    new_choice = f"{'ABCD'[len(question['choices'])]}. Không có đáp án nào ở trên là đúng"
                    question['choices'].append(new_choice)
            
            # Đảm bảo câu trả lời đúng nằm trong các lựa chọn
            if question['correct_answer'] not in question['choices']:
                # Nếu câu trả lời đúng không nằm trong các lựa chọn, thêm nó vào
                question['choices'][3] = question['correct_answer']
            
        return questions

    def generate_programming_mcq_with_difficulty(self, language, topic, difficulty="beginner"):
        """Tạo câu hỏi trắc nghiệm theo ngôn ngữ, chủ đề và độ khó"""
        # Điều chỉnh prompt dựa trên độ khó
        difficulty_prompts = {
            "beginner": "các câu hỏi cơ bản, đơn giản, tập trung vào kiến thức nền tảng, phù hợp người mới học lập trình",
            "intermediate": "các câu hỏi mức trung bình, yêu cầu hiểu biết tốt về ngôn ngữ và chủ đề, phù hợp lập trình viên 1 năm kinh nghiệm",
            "advanced": "các câu hỏi nâng cao, có độ phức tạp cao, bao gồm một số đoạn mã để phân tích và hiểu khái niệm chi tiết, phù hợp lập trình viên 2 tới 5 năm kinh nghiệm",
            "expert": "các câu hỏi cực kỳ khó, phức tạp, có thể bao gồm nhiều đoạn mã, trường hợp đặc biệt và các khái niệm chuyên sâu, phù hợp các lập trình viên lão luyện hơn 5 năm kinh nghiệm"
        }
        
        # Thêm độ phức tạp vào prompt dựa trên mức độ
        prompt_addition = difficulty_prompts.get(difficulty, difficulty_prompts["beginner"])
        
        prompt = f"""Hãy tạo 10 câu hỏi trắc nghiệm bằng tiếng Việt về ngôn ngữ lập trình {language}, 
        tập trung vào chủ đề {topic}. 
        Yêu cầu tạo {prompt_addition}.
        
        QUY TẮC QUAN TRỌNG (PHẢI TUÂN THỦ NGHIÊM NGẶT):
        1. TẤT CẢ câu hỏi PHẢI HOÀN TOÀN là dạng trắc nghiệm với bốn đáp án cụ thể, người dùng CHỈ CHỌN một trong các đáp án có sẵn.
        2. TUYỆT ĐỐI KHÔNG tạo câu hỏi dạng "Viết đoạn code để...", "Hãy viết code...", "Coding...", hoặc bất kỳ câu hỏi nào yêu cầu người dùng nhập mã.
        3. Với câu hỏi về code, LUÔN dùng dạng câu như:
           - "Đâu là đoạn mã đúng để..." (các đáp án phải là code, KHÔNG phải kết quả hoặc số)
           - "Đoạn mã nào thực hiện..." (các đáp án phải là code, KHÔNG phải kết quả hoặc số)
           - "Kết quả của đoạn mã sau là gì..." (các đáp án là giá trị kết quả, không phải code)
           - "Đâu là lỗi trong đoạn mã sau..." (các đáp án mô tả lỗi, không phải code hoàn chỉnh)
        4. LUÔN đảm bảo loại câu hỏi và loại đáp án phù hợp với nhau:
           - Nếu hỏi "Đâu là đoạn mã..." thì đáp án PHẢI là các đoạn mã, không phải kết quả.
           - Nếu hỏi "Kết quả của..." thì đáp án PHẢI là kết quả, không phải đoạn mã.
        5. Đảm bảo mỗi đáp án là HOÀN CHỈNH và ĐỦ để trả lời câu hỏi, không yêu cầu thêm thông tin từ người dùng.
        6. Với câu hỏi về code, HÃY LUÔN cung cấp các đoạn mã ĐẦY ĐỦ trong các đáp án, không để người dùng phải viết thêm hoặc sửa code.
        7. KHÔNG được tạo câu hỏi yêu cầu người dùng hoàn thiện đoạn mã còn thiếu.
        8. MỖI ĐÁP ÁN phải khác biệt rõ ràng và chỉ 1 đáp án đúng.
        """
        
        # Thêm yêu cầu code snippet cho mức intermediate trở lên
        if difficulty != "beginner":
            prompt += """Hãy thêm đoạn mã (code snippet) vào ít nhất 50% câu hỏi. Đoạn mã phải được định dạng rõ ràng.
            """
        
        # Thêm yêu cầu câu hỏi nhiều phần cho mức advanced và expert
        if difficulty in ["advanced", "expert"]:
            prompt += """Ít nhất 30% câu hỏi phải là câu hỏi nhiều phần (multi-part questions), 
            yêu cầu hiểu biết về nhiều khái niệm để trả lời chính xác.
            """
        
        prompt += """Mỗi câu hỏi phải có 4 đáp án A, B, C, D.
        Định dạng JSON như sau:
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
            response = client.chat.completions.create(
                model="gpt-4.1-mini-2025-04-14",
                messages=[
                    {"role": "system", "content": "Bạn là chuyên gia tạo câu hỏi trắc nghiệm về lập trình bằng tiếng Việt với các mức độ khó khác nhau."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )

            response_content = response.choices[0].message.content
            
            try:
                quiz_data = json.loads(response_content)
                
                # Validate the response structure
                if 'questions' not in quiz_data or not quiz_data['questions']:
                    st.error("API trả về cấu trúc không hợp lệ hoặc không có câu hỏi")
                    # Create a default question if needed
                    return [{
                        "question": f"Đâu là cách đúng để thực hiện vòng lặp trong {language}?",
                        "choices": [
                            "A. Sử dụng vòng lặp for", 
                            "B. Sử dụng vòng lặp while",
                            "C. Sử dụng vòng lặp do-while",
                            "D. Tất cả đều đúng"
                        ],
                        "correct_answer": "D. Tất cả đều đúng",
                        "explanation": "Đây là câu hỏi mẫu vì hệ thống không thể tạo câu hỏi. Vui lòng thử lại với độ khó khác.",
                        "difficulty": difficulty
                    }]
                
                # Validate và sửa câu hỏi
                validated_questions = self.validate_and_fix_questions(quiz_data['questions'])
                
                return validated_questions
                
            except json.JSONDecodeError:
                st.error("Không thể parse JSON từ phản hồi của API")
                st.error(f"Phản hồi: {response_content[:500]}...")
                # Create a default question
                return [{
                    "question": f"Đâu là cách đúng để thực hiện vòng lặp trong {language}?",
                    "choices": [
                        "A. Sử dụng vòng lặp for", 
                        "B. Sử dụng vòng lặp while",
                        "C. Sử dụng vòng lặp do-while",
                        "D. Tất cả đều đúng"
                    ],
                    "correct_answer": "D. Tất cả đều đúng",
                    "explanation": "Đây là câu hỏi mẫu vì hệ thống không thể tạo câu hỏi. Vui lòng thử lại với độ khó khác.",
                    "difficulty": difficulty
                }]
        except Exception as e:
            st.error(f"Lỗi khi tạo câu hỏi: {e}")
            # Create a default question
            return [{
                "question": f"Đâu là cách đúng để thực hiện vòng lặp trong {language}?",
                "choices": [
                    "A. Sử dụng vòng lặp for", 
                    "B. Sử dụng vòng lặp while",
                    "C. Sử dụng vòng lặp do-while",
                    "D. Tất cả đều đúng"
                ],
                "correct_answer": "D. Tất cả đều đúng",
                "explanation": "Đây là câu hỏi mẫu vì hệ thống không thể tạo câu hỏi. Vui lòng thử lại với độ khó khác.",
                "difficulty": difficulty
            }]

    def use_fifty_fifty(self, question):
        """Sử dụng trợ giúp 50:50"""
        correct_answer = question['correct_answer']
        wrong_answers = [choice for choice in question['choices'] if choice != correct_answer]
        wrong_answers_to_remove = random.sample(wrong_answers, 2)
        remaining_answers = [correct_answer] + [ans for ans in wrong_answers if ans not in wrong_answers_to_remove]
        return sorted(remaining_answers)

    def get_hint(self, question):
        """Lấy gợi ý cho câu hỏi hiện tại"""
        choices_text = "\n".join(question['choices'])
        hint = ai_explanation_system.get_hint(question['question'], choices_text)
        st.session_state.current_hint = hint
        st.session_state.hint_used = True
        return hint

    def handle_answer(self, choice, current_q):
        """Xử lý khi người dùng trả lời câu hỏi với cải thiện xử lý audio"""
        st.session_state.has_answered = True
        st.session_state.user_answers[st.session_state.current_question] = choice
    
        # Dừng âm thanh đang phát một cách an toàn
        try:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
        except:
            pass
            
        is_correct = choice == current_q['correct_answer']
    
        # Tạo container riêng cho phản hồi đúng/sai
        feedback_container = st.empty()
    
        with feedback_container.container():
            if is_correct:
                st.success("🎉 Chính xác!")
                audio_text = "Chúc mừng! Đáp án chính xác!"
                try:
                    st_lottie(load_lottieurl("https://assets5.lottiefiles.com/private_files/lf30_WdTEui.json"), height=200)
                except Exception as lottie_error:
                    st.warning(f"Không hiển thị được animation: {lottie_error}")
                st.session_state.score += 1
            else:
                st.error("❌ Chưa chính xác!")
                audio_text = f"Rất tiếc! Đáp án chưa chính xác. Đáp án đúng là {current_q['correct_answer']}"
                try:
                    st_lottie(load_lottieurl("https://assets5.lottiefiles.com/private_files/lf30_GjhcdO.json"), height=200)
                except Exception as lottie_error:
                    st.warning(f"Không hiển thị được animation: {lottie_error}")
    
            # Phát âm thanh phản hồi đồng bộ (không dùng threading)
            self.speak_text(audio_text, block=True)
        
            # Hiển thị giải thích từ AI dựa trên câu trả lời trong container riêng
            explanation_container = st.container()
            with explanation_container:
                if st.session_state.logged_in:
                    enhanced_explanation = ai_explanation_system.get_explanation(
                        st.session_state.last_language, 
                        st.session_state.last_topic,
                        current_q['question'],
                        choice,
                        current_q['correct_answer'],
                        is_correct
                    )
                    st.markdown(f"""
                    <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px;'>
                        <h4>💡 Giải thích chi tiết:</h4>
                        <p>{enhanced_explanation}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px;'>
                        <h4>💡 Giải thích:</h4>
                        <p>{current_q['explanation']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Nếu người dùng đã đăng nhập, cung cấp câu hỏi mở thêm trong container riêng
            if st.session_state.logged_in:
                followup_container = st.container()
                with followup_container:
                    follow_up = ai_explanation_system.generate_follow_up_question(
                        st.session_state.last_language,
                        st.session_state.last_topic,
                        current_q['question'],
                        is_correct
                    )
                    st.markdown(f"""
                    <div style='background-color: #e8f5e9; padding: 20px; border-radius: 10px; margin-top: 15px;'>
                        <h4>🧩 Câu hỏi mở rộng:</h4>
                        <p>{follow_up}</p>
                    </div>
                    """, unsafe_allow_html=True)

    def reset_quiz_state(self):
        """Đặt lại trạng thái quiz và dừng audio đúng cách"""
        # Đánh dấu quiz không còn hoạt động
        st.session_state.quiz_started = False
    
        # Dừng âm thanh đang phát một cách an toàn
        try:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
        except Exception as e:
            pass
    
        # Reset trạng thái speaking
        st.session_state.is_speaking = False
    
        # Reset các trạng thái khác
        keys_to_reset = [
            'questions', 'current_question', 'score',
            'start_time', 'fifty_fifty_used', 'current_choices',
            'has_answered', 'user_answers', 'show_results', 'question_read',
            'hint_used', 'current_hint'
        ]   
    
        for key in keys_to_reset:
            if key in st.session_state:
                if key in ['questions', 'user_answers']:
                    st.session_state[key] = []
                elif key in ['current_question', 'score']:
                    st.session_state[key] = 0
                elif key in ['fifty_fifty_used', 'has_answered', 'show_results', 'question_read', 'hint_used']:
                    st.session_state[key] = False
                elif key in ['start_time', 'current_choices', 'current_hint']:
                    st.session_state[key] = None

    def save_quiz_results(self):
        """Lưu kết quả quiz cho người dùng đã đăng nhập"""
        if st.session_state.logged_in and st.session_state.show_results:
            # Tính thời gian làm bài
            end_time = datetime.now()
            duration_seconds = int((end_time - st.session_state.start_time).total_seconds())
            
            # Lưu kết quả vào cơ sở dữ liệu
            result = user_data_manager.save_quiz_result(
                st.session_state.user_id,
                st.session_state.last_language,
                st.session_state.last_topic,
                st.session_state.score,
                len(st.session_state.questions),
                duration_seconds,
                st.session_state.questions,
                st.session_state.user_answers,
                st.session_state.current_difficulty
            )
            
            if not result["success"]:
                st.warning(f"Không thể lưu kết quả: {result['error']}")

    def render_auth_interface(self):
        """Hiển thị giao diện đăng nhập/đăng ký"""
        st.markdown("""
        <style>
        .auth-container {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .auth-title {
            color: #2C3E50;
            font-size: 24px;
            margin-bottom: 15px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        auth_tab1, auth_tab2 = st.tabs(["Đăng nhập", "Đăng ký"])
        
        with auth_tab1:
            st.markdown("<div class='auth-title'>Đăng nhập</div>", unsafe_allow_html=True)
            username = st.text_input("Tên đăng nhập:", key="login_username")
            password = st.text_input("Mật khẩu:", type="password", key="login_password")
            
            if st.button("Đăng nhập", key="login_button"):
                if username and password:
                    result = user_data_manager.login_user(username, password)
                    if result["success"]:
                        st.session_state.logged_in = True
                        st.session_state.user_id = result["user_id"]
                        st.success("Đăng nhập thành công!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(result["error"])
                else:
                    st.warning("Vui lòng nhập tên đăng nhập và mật khẩu")
        
        with auth_tab2:
            st.markdown("<div class='auth-title'>Đăng ký</div>", unsafe_allow_html=True)
            new_username = st.text_input("Tên đăng nhập:", key="register_username")
            new_password = st.text_input("Mật khẩu:", type="password", key="register_password")
            confirm_password = st.text_input("Xác nhận mật khẩu:", type="password", key="confirm_password")
            
            if st.button("Đăng ký", key="register_button"):
                if new_username and new_password:
                    if new_password != confirm_password:
                        st.error("Mật khẩu xác nhận không khớp")
                    else:
                        result = user_data_manager.register_user(new_username, new_password)
                        if result["success"]:
                            st.success("Đăng ký thành công! Bạn có thể đăng nhập ngay bây giờ.")
                        else:
                            st.error(result["error"])
                else:
                    st.warning("Vui lòng nhập tên đăng nhập và mật khẩu")

    def render_user_dashboard(self):
        """Hiển thị bảng điều khiển người dùng"""
        st.markdown("""
        <style>
        .dashboard-container {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .dashboard-title {
            color: #2C3E50;
            font-size: 24px;
            margin-bottom: 15px;
        }
        .stat-card {
            background-color: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 10px;
        }
        .stat-value {
            font-size: 36px;
            font-weight: bold;
            color: #3498DB;
        }
        .stat-label {
            font-size: 14px;
            color: #7F8C8D;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Lấy thống kê người dùng
        stats_result = user_data_manager.get_user_statistics(st.session_state.user_id)
        
        if stats_result["success"]:
            stats = stats_result["statistics"]
            
            st.markdown("<div class='dashboard-title'>Bảng Điều Khiển Người Dùng</div>", unsafe_allow_html=True)
            
            # Hiển thị các chỉ số chính
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div class='stat-card'>
                    <div class='stat-value'>{stats['total_quizzes']}</div>
                    <div class='stat-label'>Tổng số bài kiểm tra</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class='stat-card'>
                    <div class='stat-value'>{stats['total_questions']}</div>
                    <div class='stat-label'>Tổng số câu hỏi</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class='stat-card'>
                    <div class='stat-value'>{stats['accuracy']:.1f}%</div>
                    <div class='stat-label'>Tỷ lệ chính xác</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Hiển thị biểu đồ thống kê
            dash_tab1, dash_tab2, dash_tab3 = st.tabs(["Thống kê theo ngôn ngữ", "Lộ trình học", "Lịch sử bài kiểm tra"])
            
            with dash_tab1:
                if stats['language_stats']:
                    # Tạo biểu đồ cho thống kê ngôn ngữ
                    fig, ax = plt.subplots(figsize=(10, 6))
                    languages = [stat['language'] for stat in stats['language_stats']]
                    scores = [stat['average_score'] for stat in stats['language_stats']]
                    counts = [stat['quiz_count'] for stat in stats['language_stats']]
                    
                    bars = ax.bar(languages, scores, color='skyblue')
                    
                    # Thêm nhãn số lượng bài kiểm tra
                    for i, bar in enumerate(bars):
                        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                               f'{counts[i]} bài', ha='center', va='bottom')
                    
                    ax.set_xlabel('Ngôn ngữ lập trình')
                    ax.set_ylabel('Điểm trung bình (%)')
                    ax.set_title('Hiệu suất theo ngôn ngữ lập trình')
                    ax.set_ylim(0, 110)  # Đảm bảo có đủ không gian cho nhãn
                    
                    st.pyplot(fig)
                else:
                    st.info("Chưa có đủ dữ liệu để hiển thị thống kê theo ngôn ngữ")
            
            with dash_tab2:
                st.subheader("Lộ trình học đề xuất")
                
                if 'suggested_topics' in stats and stats['suggested_topics']:
                    for i, topic in enumerate(stats['suggested_topics']):
                        st.markdown(f"""
                        <div style='background-color: white; padding: 15px; border-radius: 8px; 
                                    box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 10px;'>
                            <h3>{i+1}. {topic}</h3>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Hoàn thành một số bài kiểm tra để nhận lộ trình học được cá nhân hóa")
                
                st.subheader("Mức độ thành thạo hiện tại")
                
                if 'proficiency_levels' in stats and stats['proficiency_levels']:
                    for language, level in stats['proficiency_levels'].items():
                        level_color = {
                            "beginner": "#e8f5e9",  # Light green
                            "intermediate": "#bbdefb",  # Light blue
                            "advanced": "#d1c4e9",  # Light purple
                            "expert": "#ffecb3"  # Light amber
                        }.get(level, "#f0f2f6")
                        
                        st.markdown(f"""
                        <div style='background-color: {level_color}; padding: 15px; border-radius: 8px; 
                                    box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 10px;'>
                            <h3>{language}: {level.capitalize()}</h3>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Chưa có dữ liệu về mức độ thành thạo")
            
            with dash_tab3:
                st.subheader("Lịch sử bài kiểm tra")
                
                # Lấy lịch sử làm bài quiz
                history_result = user_data_manager.get_user_quiz_history(st.session_state.user_id)
                
                if history_result["success"] and history_result["history"]:
                    history = history_result["history"]
                    
                    # Tạo dataframe từ lịch sử
                    df = pd.DataFrame(history)
                    
                    # Thêm cột hiển thị điểm dưới dạng phần trăm
                    df['score_percent'] = (df['score'] * 100 / df['total_questions']).round(1)
                    
                    # Định dạng lại cột thời gian
                    df['formatted_date'] = pd.to_datetime(df['quiz_date']).dt.strftime('%d/%m/%Y %H:%M')
                    
                    # Chọn và sắp xếp lại các cột để hiển thị
                    display_df = df[['formatted_date', 'language', 'topic', 'score', 'total_questions', 'score_percent', 'difficulty_level']]
                    display_df.columns = ['Thời gian', 'Ngôn ngữ', 'Chủ đề', 'Điểm', 'Tổng số câu', 'Tỷ lệ đúng (%)', 'Độ khó']
                    
                    # Hiển thị bảng
                    st.dataframe(display_df, use_container_width=True)
                    
                    # Hiển thị biểu đồ tiến độ
                    st.subheader("Tiến độ theo thời gian")
                    
                    # Sắp xếp lại theo thời gian
                    df = df.sort_values('quiz_date')
                    
                    # Tạo biểu đồ
                    fig, ax = plt.subplots(figsize=(10, 6))
                    ax.plot(range(len(df)), df['score_percent'], marker='o', linestyle='-', color='#3498DB')
                    
                    # Thêm nhãn
                    ax.set_xlabel('Số thứ tự bài kiểm tra')
                    ax.set_ylabel('Tỷ lệ đúng (%)')
                    ax.set_title('Tiến độ học tập theo thời gian')
                    ax.grid(True, linestyle='--', alpha=0.7)
                    
                    # Hiển thị thông tin khi di chuột qua
                    for i, row in enumerate(df.itertuples()):
                        ax.annotate(f"{row.language}: {row.topic}\n{row.score}/{row.total_questions}",
                                   xy=(i, row.score_percent),
                                   xytext=(0, 10),
                                   textcoords='offset points',
                                   ha='center',
                                   va='bottom',
                                   bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),visible=False)
                    
                    st.pyplot(fig)
                else:
                    st.info("Chưa có lịch sử bài kiểm tra")
            
            # Thêm nút đăng xuất
            if st.button("Đăng xuất"):
                for key in ['logged_in', 'user_id']:
                    st.session_state[key] = None if key == 'user_id' else False
                st.rerun()
        else:
            st.error(f"Không thể tải thông tin người dùng: {stats_result['error']}")
            if st.button("Thử lại"):
                st.rerun()

    def render_preferences(self):
        """Hiển thị giao diện tùy chọn"""
        st.subheader("Tùy chọn người dùng")
        
        # Lấy các tùy chọn hiện tại của người dùng nếu đã đăng nhập
        if st.session_state.logged_in:
            prefs_result = user_data_manager.get_user_preferences(st.session_state.user_id)
            if prefs_result["success"]:
                current_prefs = prefs_result["preferences"]
                default_languages = current_prefs["preferred_languages"]
                default_topics = current_prefs["preferred_topics"]
                default_difficulty = current_prefs["difficulty_level"]
            else:
                default_languages = ["Python"]
                default_topics = ["Cơ bản"]
                default_difficulty = "beginner"
        else:
            default_languages = ["Python"]
            default_topics = ["Cơ bản"]
            default_difficulty = st.session_state.current_difficulty
        
        # Ngôn ngữ lập trình
        selected_language = st.selectbox(
            "Chọn ngôn ngữ lập trình:",
            ["Python", "JavaScript", "Java", "C++", "C#"],
            index=["Python", "JavaScript", "Java", "C++", "C#"].index(default_languages[0]) if default_languages else 0
        )
        
        # Chủ đề
        topic_options = {
            "Python": ["Cú pháp cơ bản", "Biến và kiểu dữ liệu", "Câu lệnh điều kiện", "Vòng lặp", "Hàm", "OOP", "Modules", "File I/O", "Exceptions"],
            "JavaScript": ["Cú pháp cơ bản", "Biến và kiểu dữ liệu", "Câu lệnh điều kiện", "Vòng lặp", "Hàm", "DOM", "Events", "AJAX", "ES6+"],
            "Java": ["Cú pháp cơ bản", "Biến và kiểu dữ liệu", "Câu lệnh điều kiện", "Vòng lặp", "Phương thức", "OOP", "Collections", "Exceptions"],
            "C++": ["Cú pháp cơ bản", "Biến và kiểu dữ liệu", "Câu lệnh điều kiện", "Vòng lặp", "Hàm", "OOP", "Templates", "STL", "Memory Management"],
            "C#": ["Cú pháp cơ bản", "Biến và kiểu dữ liệu", "Câu lệnh điều kiện", "Vòng lặp", "Phương thức", "OOP", "LINQ", "Async/Await"]
        }
        
        selected_topic = st.selectbox(
            "Chọn chủ đề:",
            topic_options.get(selected_language, ["Cơ bản"]),
            index=0
        )
        
        # Độ khó (hiển thị CHO TẤT CẢ người dùng - ĐÃ SỬA Ở ĐÂY)
        difficulty_options = ["beginner", "intermediate", "advanced", "expert"]
        difficulty_labels = ["Cơ bản", "Trung cấp", "Nâng cao", "Chuyên gia"]
        
        try:
            difficulty_index = difficulty_options.index(default_difficulty) if default_difficulty in difficulty_options else 0
        except ValueError:
            difficulty_index = 0
        
        selected_difficulty_label = st.selectbox(
            "Chọn độ khó:",
            difficulty_labels,
            index=difficulty_index,
            key="difficulty_select"
        )
        selected_difficulty = difficulty_options[difficulty_labels.index(selected_difficulty_label)]
        st.session_state.current_difficulty = selected_difficulty
        
        # Nút bắt đầu quiz
        start_col1, start_col2 = st.columns([1, 3])
        with start_col1:
            if st.button("Bắt đầu Quiz", key="start_quiz"):
                questions = self.generate_programming_mcq(selected_language, selected_topic)
                
                # Check if questions were successfully generated
                if not questions:
                    st.error("Không thể tạo câu hỏi. Vui lòng thử lại với độ khó khác.")
                    return
                    
                st.session_state.questions = questions
                st.session_state.current_question = 0
                st.session_state.quiz_started = True
                st.session_state.score = 0
                st.session_state.start_time = datetime.now()
                st.session_state.fifty_fifty_used = False
                st.session_state.user_answers = [None] * len(questions)
                st.session_state.has_answered = False
                st.session_state.last_language = selected_language
                st.session_state.last_topic = selected_topic
                st.session_state.show_results = False
                st.session_state.question_read = False
                st.session_state.hint_used = False
                st.session_state.current_hint = None
                st.rerun()
        
        # Cập nhật tùy chọn nếu đã đăng nhập
        if st.session_state.logged_in:
            with start_col2:
                if st.button("Lưu tùy chọn", key="save_prefs"):
                    result = user_data_manager.update_user_preferences(
                        st.session_state.user_id,
                        [selected_language],
                        [selected_topic],
                        selected_difficulty  # Sử dụng độ khó đã chọn
                    )
                    if result["success"]:
                        st.success("Đã lưu tùy chọn người dùng!")
                    else:
                        st.error(f"Không thể lưu tùy chọn: {result['error']}")

    def render_quiz_interface(self):
        """Hiển thị giao diện làm quiz"""
        if not st.session_state.quiz_started:
            return
        
        # Check if questions list is empty
        if not st.session_state.questions:
            st.error("Không thể tạo câu hỏi. Vui lòng thử lại với độ khó khác.")
            if st.button("Quay lại"):
                self.reset_quiz_state()
                st.rerun()
            return
        
        # Hiển thị thông tin quiz
        st.markdown(f"""
        <div style='background-color: #f0f9ff; padding: 10px; border-radius: 8px; margin-bottom: 20px;'>
            <h3>Quiz: {st.session_state.last_language} - {st.session_state.last_topic}</h3>
            <p>Câu hỏi {st.session_state.current_question + 1}/{len(st.session_state.questions)} | Điểm: {st.session_state.score}</p>
            <p>Độ khó: {st.session_state.current_difficulty.capitalize()}</p>
        </div>
        """, unsafe_allow_html=True)
        
        current_q = st.session_state.questions[st.session_state.current_question]
        
        # Hiển thị câu hỏi
        question_text = current_q['question']
        
        # Kiểm tra xem câu hỏi có chứa đoạn code không
        if "```" in question_text:
            parts = question_text.split("```")
            if len(parts) >= 3:  # Có ít nhất một code block
                st.markdown(f"### {parts[0]}")
                st.code(parts[1], language=st.session_state.last_language.lower())
                if parts[2]:  # Nếu có phần văn bản sau code
                    st.markdown(parts[2])
            else:
                st.markdown(f"### {question_text}")
        else:
            st.markdown(f"### {question_text}")
        
        # Đọc câu hỏi và lựa chọn
        self.read_question_and_choices(current_q)
        
        # Hiển thị các lựa chọn
        if st.session_state.fifty_fifty_used and st.session_state.current_choices:
            choices = st.session_state.current_choices
        else:
            choices = current_q['choices']
        
        # Container cho các lựa chọn
        choice_container = st.container()
        choice_cols = choice_container.columns(2)
        
        for i, choice in enumerate(choices):
            with choice_cols[i % 2]:
                # Kiểm tra xem lựa chọn có chứa đoạn code không
                if "```" in choice:
                    parts = choice.split("```")
                    if len(parts) >= 3:  # Có ít nhất một code block
                        choice_prefix = parts[0]  # Lấy phần prefix (A. B. C. D.)
                        choice_code = parts[1]  # Lấy phần code
                        
                        # Hiển thị phần prefix
                        st.markdown(f"**{choice_prefix.strip()}**")
                        
                        # Hiển thị phần code
                        st.code(choice_code, language=st.session_state.last_language.lower())
                        
                        # Phần văn bản sau code (nếu có)
                        if parts[2]:
                            st.markdown(parts[2])
                        
                        # Nút chọn đáp án
                        if st.button(
                            f"Chọn {choice_prefix.strip()}",
                            key=f"choice_{i}",
                            disabled=st.session_state.has_answered
                        ):
                            self.handle_answer(choice, current_q)
                    else:
                        # Nếu không parse được đúng, hiển thị nguyên văn
                        if st.button(
                            choice,
                            key=f"choice_{i}",
                            disabled=st.session_state.has_answered,
                            use_container_width=True
                        ):
                            self.handle_answer(choice, current_q)
                else:
                    # Nếu không có code, hiển thị bình thường
                    if st.button(
                        choice,
                        key=f"choice_{i}",
                        disabled=st.session_state.has_answered,
                        use_container_width=True
                    ):
                        self.handle_answer(choice, current_q)
        
        # Hiển thị gợi ý nếu được yêu cầu
        if st.session_state.hint_used and st.session_state.current_hint:
            hint_container = st.container()
            with hint_container:
                st.info(f"💡 Gợi ý: {st.session_state.current_hint}")
        
        # Cột chứa các nút điều hướng và trợ giúp
        nav_container = st.container()
        help_cols = nav_container.columns([1, 1, 1, 1])
        
        # Nút 50:50
        with help_cols[0]:
            if st.button(
                "50:50", 
                key="fifty_fifty",
                disabled=st.session_state.fifty_fifty_used or st.session_state.has_answered,
                use_container_width=True
            ):
                st.session_state.current_choices = self.use_fifty_fifty(current_q)
                st.session_state.fifty_fifty_used = True
                st.rerun()
        
        # Nút gợi ý
        with help_cols[1]:
            if st.button(
                "Gợi ý", 
                key="hint_button",
                disabled=st.session_state.hint_used or st.session_state.has_answered,
                use_container_width=True
            ):
                self.get_hint(current_q)
                st.rerun()
        
        # Nút câu hỏi trước
        with help_cols[2]:
            if st.button(
                "Câu trước", 
                key="prev_question",
                disabled=st.session_state.current_question == 0,
                use_container_width=True
            ):
                # Đặt lại trạng thái cho câu hỏi mới
                st.session_state.current_question -= 1
                st.session_state.has_answered = st.session_state.user_answers[st.session_state.current_question] is not None
                st.session_state.fifty_fifty_used = False
                st.session_state.current_choices = None
                st.session_state.question_read = False
                st.session_state.hint_used = False
                st.session_state.current_hint = None
                st.rerun()
        
        # Nút câu hỏi tiếp theo hoặc kết thúc
        with help_cols[3]:
            if st.session_state.current_question < len(st.session_state.questions) - 1:
                if st.button(
                    "Câu tiếp", 
                    key="next_question",
                    disabled=not st.session_state.has_answered,
                    use_container_width=True
                ):
                    # Đặt lại trạng thái cho câu hỏi mới
                    st.session_state.current_question += 1
                    st.session_state.has_answered = st.session_state.user_answers[st.session_state.current_question] is not None
                    st.session_state.fifty_fifty_used = False
                    st.session_state.current_choices = None
                    st.session_state.question_read = False
                    st.session_state.hint_used = False
                    st.session_state.current_hint = None
                    st.rerun()
            else:
                if st.button(
                    "Kết thúc", 
                    key="finish_quiz",
                    disabled=not st.session_state.has_answered,
                    use_container_width=True
                ):
                    st.session_state.show_results = True
                    self.save_quiz_results()
                    st.rerun()
        
        # Các nút bổ sung
        extra_buttons = st.container()
        extra_cols = extra_buttons.columns([1, 1])
        
        # Nút đọc lại câu hỏi
        with extra_cols[0]:
            if st.button("Đọc lại câu hỏi", key="read_again"):
                st.session_state.question_read = False
                self.read_question_and_choices(current_q)
        
        # Nút hủy bài kiểm tra
        with extra_cols[1]:
            if st.button("Hủy bài kiểm tra", key="cancel_quiz"):
                self.reset_quiz_state()
                st.rerun()

    def render_results(self):
        """Hiển thị kết quả bài kiểm tra"""
        if not st.session_state.show_results:
            return
        
        # Tính toán thời gian làm bài
        end_time = datetime.now()
        duration = end_time - st.session_state.start_time
        duration_minutes = duration.seconds // 60
        duration_seconds = duration.seconds % 60
        
        # Hiển thị thống kê tổng quan
        st.markdown(f"""
        <div style='background-color: #e8f5e9; padding: 20px; border-radius: 10px; margin-bottom: 30px; text-align: center;'>
            <h2>Kết quả bài kiểm tra</h2>
            <h3>{st.session_state.last_language} - {st.session_state.last_topic}</h3>
            <p style='font-size: 24px;'>Điểm số: {st.session_state.score}/{len(st.session_state.questions)}</p>
            <p>Tỷ lệ chính xác: {(st.session_state.score / len(st.session_state.questions) * 100):.1f}%</p>
            <p>Thời gian làm bài: {duration_minutes} phút {duration_seconds} giây</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Hiển thị chi tiết từng câu hỏi
        st.subheader("Chi tiết câu trả lời:")
        
        for i, question in enumerate(st.session_state.questions):
            user_answer = st.session_state.user_answers[i]
            is_correct = user_answer == question['correct_answer']
            
            color = "#e8f5e9" if is_correct else "#fbe9e7"
            icon = "✅" if is_correct else "❌"
            
            # Container cho từng câu hỏi
            question_container = st.container()
            with question_container:
                st.markdown(f"""
                <div style='background-color: {color}; padding: 15px; border-radius: 8px; margin-bottom: 20px;'>
                    <h4>Câu hỏi {i+1}: {question['question']}</h4>
                """, unsafe_allow_html=True)
                
                # Kiểm tra nếu câu hỏi có chứa code
                if "```" in question['question']:
                    parts = question['question'].split("```")
                    if len(parts) >= 3:
                        st.code(parts[1], language=st.session_state.last_language.lower())
                
                # Hiển thị đáp án
                st.markdown(f"""
                    <p><strong>Đáp án của bạn:</strong> {user_answer or 'Chưa trả lời'} {icon}</p>
                    <p><strong>Đáp án đúng:</strong> {question['correct_answer']}</p>
                """, unsafe_allow_html=True)
                
                # Kiểm tra nếu đáp án có chứa code
                if user_answer and "```" in user_answer:
                    parts = user_answer.split("```")
                    if len(parts) >= 3:
                        st.code(parts[1], language=st.session_state.last_language.lower())
                
                if "```" in question['correct_answer']:
                    parts = question['correct_answer'].split("```")
                    if len(parts) >= 3:
                        st.code(parts[1], language=st.session_state.last_language.lower())
                
                # Hiển thị giải thích
                st.markdown(f"<p><strong>Giải thích:</strong> {question['explanation']}</p></div>", unsafe_allow_html=True)
        
        # Phân tích và đề xuất cải thiện
        if st.session_state.logged_in:
            st.subheader("Phân tích và đề xuất:")
            
            # Lấy lộ trình học
            learning_path = adaptive_learning_system.suggest_learning_path(st.session_state.user_id)
            
            if learning_path["success"]:
                # Hiển thị các đề xuất
                if learning_path["suggestions"]:
                    for i, suggestion in enumerate(learning_path["suggestions"]):
                        st.info(f"💡 Đề xuất {i+1}: {suggestion}")
            
            # Nếu điểm số thấp, đề xuất các chủ đề cần ôn tập
            score_percent = st.session_state.score / len(st.session_state.questions) * 100
            if score_percent < 60:
                st.warning(f"Bạn nên ôn tập lại chủ đề {st.session_state.last_topic} trước khi tiếp tục học các chủ đề nâng cao hơn.")
            elif score_percent >= 80:
                st.success("Bạn đã nắm vững chủ đề này và sẵn sàng học các chủ đề nâng cao hơn!")
        
        # Các nút điều hướng
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Làm lại bài kiểm tra", key="retry_quiz"):
                # ĐÃ SỬA ĐỔI: Quay về màn hình chọn tùy chọn thay vì tự tạo bài kiểm tra mới
                self.reset_quiz_state()
                st.rerun()
        
        with col2:
            if st.button("Quay lại trang chính", key="back_to_home"):
                self.reset_quiz_state()
                st.rerun()

    def render_code_practice(self):
        """Hiển thị giao diện thực hành viết mã"""
        st.subheader("Thực hành viết mã")
        
        # Chọn ngôn ngữ
        language_options = code_execution_system.get_supported_languages()
        selected_language = st.selectbox(
            "Chọn ngôn ngữ lập trình:",
            language_options,
            key="code_language"
        )
        
        # Editor mã
        st.session_state.code_editor_content = st.text_area(
            "Nhập mã của bạn:",
            value=st.session_state.code_editor_content,
            height=300,
            key="code_editor"
        )
        
        # Nhập đầu vào
        input_data = st.text_area(
            "Đầu vào (nếu cần):",
            height=100,
            key="input_data"
        )
        
        # Các tùy chọn
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Chạy mã", key="run_code"):
                if st.session_state.code_editor_content:
                    # Thực thi mã
                    result = code_execution_system.execute_code(
                        st.session_state.code_editor_content,
                        selected_language,
                        input_data
                    )
                    
                    st.session_state.code_execution_result = result
                    st.rerun()
                else:
                    st.warning("Vui lòng nhập mã trước khi chạy!")
        
        with col2:
            if st.button("Phân tích mã", key="analyze_code"):
                if st.session_state.code_editor_content:
                    # Phân tích chất lượng mã
                    result = code_execution_system.analyze_code_quality(
                        st.session_state.code_editor_content,
                        selected_language
                    )
                    
                    if result["success"]:
                        st.markdown(f"""
                        <div style='background-color: #f0f9ff; padding: 20px; border-radius: 10px; margin-top: 20px;'>
                            <h4>Phân tích chất lượng mã:</h4>
                            <p>{result["analysis"]}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error(f"Không thể phân tích mã: {result['error']}")
                else:
                    st.warning("Vui lòng nhập mã trước khi phân tích!")
        
        with col3:
            if st.button("Tạo test cases", key="generate_test_cases"):
                if st.session_state.code_editor_content:
                    # Tạo các trường hợp kiểm thử
                    result = code_execution_system.generate_code_test_cases(
                        st.session_state.code_editor_content,
                        selected_language
                    )
                    
                    # Trong phần hiển thị test cases
                    if result["success"]:
                        st.markdown(f"""
                        <div style='background-color: #f0f9ff; padding: 20px; border-radius: 10px; margin-top: 20px;'>
                            <h4>Test Cases:</h4>
                        </div>
                        """, unsafe_allow_html=True)
    
                        for i, test_case in enumerate(result["test_cases"]):
                            st.markdown(f"""
                            <div style='background-color: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 10px;'>
                                <h5>Test Case {i+1}:</h5>
                                <p><strong>Input:</strong> <pre>{test_case.get('input', 'N/A')}</pre></p>
                                <p><strong>Expected Output:</strong> <pre>{test_case.get('expected_output', 'N/A')}</pre></p>
                                <p><strong>Description:</strong> {test_case.get('description', 'Không có mô tả')}</p>
                            </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.error(f"Không thể tạo test cases: {result.get('error', 'Lỗi không xác định')}")
                        
        # Hiển thị kết quả thực thi
        if st.session_state.code_execution_result:
            result = st.session_state.code_execution_result
            
            if result["success"]:
                st.markdown(f"""
                <div style='background-color: #e8f5e9; padding: 20px; border-radius: 10px; margin-top: 20px;'>
                    <h4>✅ Kết quả thực thi:</h4>
                    <pre>{result["output"]}</pre>
                    <p><strong>Thời gian thực thi:</strong> {result.get("execution_time", "N/A")} s</p>
                    <p><strong>Bộ nhớ sử dụng:</strong> {result.get("memory", "N/A")} KB</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='background-color: #fbe9e7; padding: 20px; border-radius: 10px; margin-top: 20px;'>
                    <h4>❌ Lỗi khi thực thi mã:</h4>
                    <pre>{result["error"]}</pre>
                </div>
                """, unsafe_allow_html=True)
                
                # Gợi ý sửa lỗi
                if st.button("Gợi ý sửa lỗi", key="fix_error"):
                    fix_result = code_execution_system.fix_code(
                        st.session_state.code_editor_content,
                        selected_language,
                        result["error"]
                    )
                    
                    if fix_result["success"] and fix_result["fixed_code"]:
                        st.markdown(f"""
                        <div style='background-color: #e8f5e9; padding: 20px; border-radius: 10px; margin-top: 20px;'>
                            <h4>💡 Gợi ý sửa lỗi:</h4>
                            <p>{fix_result["explanation"]}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("Áp dụng sửa lỗi", key="apply_fix"):
                            st.session_state.code_editor_content = fix_result["fixed_code"]
                            st.rerun()
                    else:
                        st.error(f"Không thể gợi ý sửa lỗi: {fix_result.get('error', 'Không xác định')}")

    def run(self):
        """Chạy ứng dụng"""
        # Thiết lập giao diện
        st.set_page_config(
            page_title="Cùng Học Lập Trình",
            page_icon="🧩",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Thiết lập tiêu đề
        st.title("📚 Cùng Học Lập Trình Nha")
        st.markdown("---")
        
        # Hiển thị đăng nhập/đăng ký nếu chưa đăng nhập
        if not st.session_state.logged_in:
            self.render_auth_interface()
        
        # Hiển thị bảng điều khiển người dùng nếu đã đăng nhập
        if st.session_state.logged_in:
            self.render_user_dashboard()
        
        # Tạo các tab chức năng
        if not st.session_state.quiz_started and not st.session_state.show_results:
            tab1, tab2 = st.tabs(["Làm bài kiểm tra", "Thực hành viết mã"])
            
            with tab1:
                self.render_preferences()
            
            with tab2:
                self.render_code_practice()
        
        # Hiển thị giao diện quiz nếu đã bắt đầu
        if st.session_state.quiz_started and not st.session_state.show_results:
            self.render_quiz_interface()
        
        # Hiển thị kết quả nếu đã hoàn thành
        if st.session_state.show_results:
            self.render_results()

    def text_to_speech_html(self, text):
        """Tạo HTML có thể phát âm thanh sử dụng gTTS và base64"""
        try:
            # Tạo âm thanh
            tts = gTTS(text=text, lang='vi', slow=False)
            mp3_bytes = BytesIO()
            tts.write_to_fp(mp3_bytes)
            mp3_bytes.seek(0)
            
            # Chuyển đổi sang base64
            b64 = base64.b64encode(mp3_bytes.read()).decode()
            
            # Tạo HTML với thẻ audio
            html = f"""
            <audio autoplay>
              <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
              Trình duyệt của bạn không hỗ trợ thẻ audio.
            </audio>
            """
            return html
        except Exception as e:
            return f"<p style='display:none'>Lỗi TTS: {str(e)}</p>"

    def create_default_questions(self, language, topic):
        """Tạo câu hỏi mặc định khi không thể tạo câu hỏi từ API"""
        return [{
            "question": f"Đâu là cách đúng để thực hiện vòng lặp trong {language}?",
            "choices": [
                "A. Sử dụng vòng lặp for", 
                "B. Sử dụng vòng lặp while",
                "C. Sử dụng vòng lặp do-while",
                "D. Tất cả đều đúng"
            ],
            "correct_answer": "D. Tất cả đều đúng",
            "explanation": "Đây là câu hỏi mẫu vì hệ thống không thể tạo câu hỏi. Vui lòng thử lại với độ khó khác.",
            "difficulty": st.session_state.current_difficulty
        }]
# Khởi tạo và chạy ứng dụng
if __name__ == "__main__":
    app = AdvancedProgrammingQuizApp()
    app.run()