import requests
import json
import re
import time

class CodeExecutionSystem:
    def __init__(self, client):
        """Khởi tạo hệ thống chạy mã - chỉ hỗ trợ ngôn ngữ phổ biến"""
        self.client = client
        
        # Chỉ giữ lại các ngôn ngữ phổ biến và ổn định
        self.supported_languages = {
            "Python": {"piston": "python", "version": "*"},
            "JavaScript": {"piston": "javascript", "version": "*"},
            "Java": {"piston": "java", "version": "*"},
            "C": {"piston": "c", "version": "*"},
            "C++": {"piston": "cpp", "version": "*"},
            "C#": {"piston": "csharp", "version": "*"},
            "Go": {"piston": "go", "version": "*"},
            "Ruby": {"piston": "ruby", "version": "*"},
            "PHP": {"piston": "php", "version": "*"},
            "Rust": {"piston": "rust", "version": "*"},
            "TypeScript": {"piston": "typescript", "version": "*"},
            "Kotlin": {"piston": "kotlin", "version": "*"}
        }
    
    def execute_code(self, code, language, stdin=""):
        """Chạy code sử dụng Piston API"""
        if language not in self.supported_languages:
            return {
                "success": False,
                "error": f"Ngôn ngữ '{language}' không được hỗ trợ.\n\nCác ngôn ngữ hỗ trợ: {', '.join(self.supported_languages.keys())}"
            }
        
        # Chuẩn bị code
        prepared_code = self.prepare_code_for_execution(code, language)
        
        # Thử Piston API trước
        result = self.execute_with_piston(prepared_code, language, stdin)
        
        # Nếu Piston thất bại, thử AI simulation cho một số ngôn ngữ
        if not result["success"] and language in ["Python", "JavaScript", "Ruby"]:
            print(f"Piston failed, trying AI simulation for {language}")
            return self.simple_code_simulation(prepared_code, language)
        
        return result
    
    def execute_with_piston(self, code, language, stdin=""):
        """Piston API - Miễn phí và ổn định"""
        lang_config = self.supported_languages[language]
        
        url = "https://emkc.org/api/v2/piston/execute"
        
        payload = {
            "language": lang_config["piston"],
            "version": lang_config["version"],
            "files": [{
                "content": code
            }],
            "stdin": stdin,
            "args": [],
            "compile_timeout": 10000,
            "run_timeout": 3000
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                
                # Kiểm tra compile output
                compile_output = result.get("compile")
                if compile_output:
                    compile_code = compile_output.get("code", 0)
                    compile_stderr = compile_output.get("stderr", "")
                    compile_output_text = compile_output.get("output", "")
                    
                    if compile_code != 0 and (compile_stderr or compile_output_text):
                        error = compile_stderr or compile_output_text
                        return {
                            "success": False,
                            "error": f"Lỗi biên dịch:\n{error}"
                        }
                
                # Lấy run output
                run = result.get("run")
                if run:
                    run_code = run.get("code", 0)
                    stdout = run.get("stdout", "")
                    stderr = run.get("stderr", "")
                    output = run.get("output", "")
                    
                    # Ưu tiên output, sau đó stdout
                    final_output = output or stdout
                    
                    # Nếu có lỗi runtime
                    if run_code != 0 and stderr and not final_output:
                        return {
                            "success": False,
                            "error": f"Lỗi runtime:\n{stderr}"
                        }
                    
                    # Nếu không có output
                    if not final_output and not stderr:
                        final_output = "(Không có output)"
                    
                    # Thêm stderr nếu có
                    if stderr and final_output:
                        final_output += f"\n\n[Stderr]:\n{stderr}"
                    
                    return {
                        "success": True,
                        "output": final_output,
                        "execution_time": f"{run.get('cpu_time', 0) / 1000:.3f}" if run.get('cpu_time') else "N/A",
                        "memory": f"{run.get('memory', 0) / 1024:.1f}" if run.get('memory') else "N/A"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Không có output từ Piston API"
                    }
            else:
                # Parse error message
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", response.text)
                except:
                    error_msg = response.text[:200]
                
                return {
                    "success": False,
                    "error": f"Lỗi Piston API ({response.status_code}): {error_msg}"
                }
                
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Timeout: Code chạy quá lâu (>15 giây)"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Không thể kết nối đến Piston API. Vui lòng kiểm tra kết nối internet."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Lỗi: {str(e)}"
            }
    
    def simple_code_simulation(self, code, language):
        """AI simulation cho Python/JavaScript khi API fail"""
        if language not in ["Python", "JavaScript", "Ruby"]:
            return {"success": False, "error": "AI simulation chỉ hỗ trợ Python, JavaScript và Ruby"}
        
        prompt = f"""Execute this {language} code and return ONLY the output:

```{language}
{code}
```

Rules:
1. Return ONLY what would be printed to console
2. No explanations or markdown
3. If error occurs, return the error message
4. Be accurate with the output format"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini-2025-04-14",
                messages=[
                    {"role": "system", "content": f"You are a {language} interpreter. Return only the exact output."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=500
            )
            
            output = response.choices[0].message.content.strip()
            
            return {
                "success": True,
                "output": output + f"\n\n[AI Simulated - API không khả dụng]",
                "execution_time": "Simulated",
                "memory": "N/A"
            }
        except Exception as e:
            return {"success": False, "error": f"AI simulation error: {str(e)}"}
    
    def prepare_code_for_execution(self, code, language):
        """Chuẩn bị code cho từng ngôn ngữ"""
        # Loại bỏ BOM nếu có
        code = code.replace('\ufeff', '')
        
        if language == "Java":
            # Java cần class và main method
            if "class " not in code:
                code = f"""public class Main {{
    public static void main(String[] args) {{
        {code}
    }}
}}"""
            elif "public static void main" not in code:
                # Nếu có class nhưng không có main
                class_match = re.search(r'class\s+(\w+)', code)
                if class_match:
                    class_name = class_match.group(1)
                    # Đổi tên class thành Main nếu cần
                    if class_name != "Main":
                        code = code.replace(f"class {class_name}", "class Main")
                        code = code.replace(f"public class {class_name}", "public class Main")
        
        elif language == "C":
            if "#include" not in code and "main" not in code:
                code = f"""#include <stdio.h>

int main() {{
    {code}
    return 0;
}}"""
        
        elif language == "C++":
            if "#include" not in code and "main" not in code:
                code = f"""#include <iostream>
using namespace std;

int main() {{
    {code}
    return 0;
}}"""
        
        elif language == "C#":
            if "using System;" not in code and "class " not in code:
                code = f"""using System;

class Program {{
    static void Main() {{
        {code}
    }}
}}"""
        
        elif language == "Go":
            if "package main" not in code:
                code = f"""package main
import "fmt"

func main() {{
    {code}
}}"""
        
        elif language == "Rust":
            if "fn main()" not in code:
                code = f"""fn main() {{
    {code}
}}"""
        
        elif language == "Kotlin":
            # Kotlin cũng cần main function
            if "fun main" not in code:
                code = f"""fun main() {{
    {code}
}}"""
        
        elif language == "TypeScript":
            # TypeScript cần console.log để có output
            if "console.log" not in code and "console.error" not in code:
                # Nếu có return statement, wrap và log nó
                if "return" in code:
                    code = f"""
const result = (() => {{
    {code}
}})();
console.log(result);"""
        
        return code
    
    def get_file_extension(self, language):
        """Lấy file extension cho ngôn ngữ"""
        extensions = {
            "Python": ".py",
            "JavaScript": ".js",
            "Java": ".java",
            "C": ".c",
            "C++": ".cpp",
            "C#": ".cs",
            "Go": ".go",
            "Ruby": ".rb",
            "PHP": ".php",
            "Rust": ".rs",
            "TypeScript": ".ts",
            "Kotlin": ".kt"
        }
        return extensions.get(language, ".txt")
    
    def get_supported_languages(self):
        """Lấy danh sách ngôn ngữ được hỗ trợ"""
        return sorted(list(self.supported_languages.keys()))
    
    def fix_code(self, code, language, error_message):
        """AI sửa lỗi code"""
        prompt = f"""Sửa lỗi trong code {language} sau:

```{language}
{code}
```

Lỗi: {error_message}

Trả về code đã sửa trong block ```{language} và giải thích ngắn gọn."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini-2025-04-14",
                messages=[
                    {"role": "system", "content": f"Bạn là chuyên gia {language}, giúp sửa lỗi code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            ai_response = response.choices[0].message.content
            
            # Trích xuất code đã sửa
            code_pattern = rf"```(?:{language.lower()}|{language})?(.+?)```"
            code_match = re.search(code_pattern, ai_response, re.DOTALL | re.IGNORECASE)
            
            if code_match:
                fixed_code = code_match.group(1).strip()
                return {
                    "success": True,
                    "fixed_code": fixed_code,
                    "explanation": ai_response
                }
            
            return {
                "success": False,
                "error": "Không thể trích xuất code đã sửa"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Lỗi AI: {str(e)}"}
    
    def generate_code_test_cases(self, code, language, num_cases=3):
        """Tạo test cases cho code"""
        prompt = f"""Tạo {num_cases} test cases cho code {language} sau:

```{language}
{code}
```

Trả về format JSON:
{{
  "test_cases": [
    {{
      "input": "input data",
      "expected_output": "expected output",
      "description": "mô tả test case"
    }}
  ]
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini-2025-04-14",
                messages=[
                    {"role": "system", "content": f"Bạn là test engineer cho {language}. Chỉ trả về JSON hợp lệ."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=800
            )
            
            ai_response = response.choices[0].message.content
            
            # Trích xuất JSON
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
            if json_match:
                test_data = json.loads(json_match.group(1))
                return {"success": True, "test_cases": test_data.get("test_cases", [])}
            
            # Thử parse trực tiếp
            try:
                # Loại bỏ text không phải JSON
                json_start = ai_response.find("{")
                json_end = ai_response.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = ai_response[json_start:json_end]
                    test_data = json.loads(json_str)
                    return {"success": True, "test_cases": test_data.get("test_cases", [])}
            except:
                pass
            
            # Fallback
            return {
                "success": True,
                "test_cases": [{
                    "input": "",
                    "expected_output": "Hello, World!",
                    "description": "Test cơ bản"
                }]
            }
            
        except Exception as e:
            return {"success": False, "error": f"Lỗi tạo test: {str(e)}"}
    
    def analyze_code_quality(self, code, language):
        """Phân tích chất lượng code"""
        prompt = f"""Phân tích chất lượng code {language} sau:

```{language}
{code}
```

Đánh giá theo thang điểm 1-10 cho:
1. Độ chính xác (Correctness)
2. Hiệu suất (Performance)
3. Khả năng bảo trì (Maintainability)
4. Phong cách code (Style)
5. Xử lý lỗi (Error handling)

Đưa ra nhận xét chi tiết và gợi ý cải thiện."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini-2025-04-14",
                messages=[
                    {"role": "system", "content": f"Bạn là code reviewer chuyên nghiệp cho {language}."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=800
            )
            
            return {
                "success": True,
                "analysis": response.choices[0].message.content
            }
        except Exception as e:
            return {"success": False, "error": f"Lỗi phân tích: {str(e)}"}