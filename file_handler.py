import os
import base64

class FileHandler:
    @staticmethod
    def get_student_directories(root_dir: str) -> list:
        """獲取總資料夾底下的所有學生子資料夾名稱"""
        if not os.path.exists(root_dir):
            raise FileNotFoundError(f"找不到總資料夾路徑: {root_dir}")
        
        # 只篩選出真正的資料夾目錄
        return [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]

    @staticmethod
    def get_image_files(student_folder: str) -> list:
        """獲取學生資料夾內的所有合法照片路徑"""
        valid_extensions = ('.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG')
        files = [f for f in os.listdir(student_folder) if f.endswith(valid_extensions)]
        # 回傳完整路徑列表
        return [os.path.join(student_folder, f) for f in files]

    @staticmethod
    def encode_image_to_base64(image_path: str) -> str:
        """將單張圖片檔案編碼為 Base64 字串"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    @staticmethod
    def read_text_file(file_path: str) -> str:
        """讀取文字檔內容"""
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    @staticmethod
    def write_text_file(file_path: str, content: str):
        """將內容寫入指定的文字檔"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    @classmethod
    def prepare_student_paths(cls, root_dir: str, student_id: str):
        """
        快速生成某個學生的資料夾路徑、OCR文字檔路徑與批改結果檔路徑
        """
        student_folder = os.path.join(root_dir, student_id)
        ocr_txt_path = os.path.join(student_folder, f"{student_id}.txt")
        grade_txt_path = os.path.join(student_folder, f"{student_id}_批改結果.txt")
        return student_folder, ocr_txt_path, grade_txt_path