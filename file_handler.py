import os
import base64
import subprocess

class FileHandler:
    @staticmethod
    def get_student_directories(root_dir: str) -> list:
        if not os.path.exists(root_dir):
            raise FileNotFoundError(f"找不到總資料夾路徑: {root_dir}")
        return [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]

    @staticmethod
    def get_image_files(student_folder: str) -> list:
        valid_extensions = ('.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG')
        if not os.path.exists(student_folder):
            return []
        files = [f for f in os.listdir(student_folder) if f.endswith(valid_extensions)]
        return [os.path.join(student_folder, f) for f in files]

    @staticmethod
    def encode_image_to_base64(image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    @staticmethod
    def write_text_file(file_path: str, content: str):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    # 🚀 【新增】自動呼叫 xelatex 將 .tex 轉成 .pdf
    @classmethod
    def compile_tex_to_pdf(cls, tex_path: str) -> bool:
        output_dir = os.path.dirname(tex_path)
        try:
            cmd = [
                "xelatex",
                "-interaction=nonstopmode",
                f"-output-directory={output_dir}",
                tex_path
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
            
            pdf_path = tex_path.replace(".tex", ".pdf")
            if os.path.exists(pdf_path):
                # 清理中間產生的 .aux, .log 檔案
                for ext in ['.aux', '.log', '.out']:
                    temp_file = tex_path.replace(".tex", ext)
                    if os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except Exception:
                            pass
                return True
            return False
        except Exception as e:
            print(f"PDF 編譯失敗: {e}")
            return False

    # 🚀 【修改】副檔名改為檢查 .pdf，並準備 .tex 路徑
    @classmethod
    def check_and_prepare_pipeline(cls, root_dir: str, output_dir_name: str, student_id: str, skip_processed: bool):
        parent_dir = os.path.dirname(os.path.abspath(root_dir))
        target_output_dir = os.path.join(parent_dir, output_dir_name)
        os.makedirs(target_output_dir, exist_ok=True)
        
        student_folder = os.path.join(root_dir, student_id)
        output_tex_path = os.path.join(target_output_dir, f"{student_id}_完整批改紀錄.tex")
        output_pdf_path = os.path.join(target_output_dir, f"{student_id}_完整批改紀錄.pdf")
        
        # 判斷是否已經有產出 PDF 檔
        if skip_processed and os.path.exists(output_pdf_path):
            return "SKIP", student_folder, output_tex_path, None

        image_files = cls.get_image_files(student_folder)
        if not image_files:
            return "EMPTY", student_folder, output_tex_path, []
            
        return "RUN", student_folder, output_tex_path, image_files