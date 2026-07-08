import os
import base64

class FileHandler:
    @staticmethod
    def get_student_directories(root_dir: str) -> list:
        """獲取總資料夾底下的所有學生子資料夾名稱"""
        if not os.path.exists(root_dir):
            raise FileNotFoundError(f"找不到總資料夾路徑: {root_dir}")
        return [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]

    @staticmethod
    def get_image_files(student_folder: str) -> list:
        """獲取學生資料夾內的所有合法照片路徑"""
        valid_extensions = ('.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG')
        if not os.path.exists(student_folder):
            return []
        files = [f for f in os.listdir(student_folder) if f.endswith(valid_extensions)]
        return [os.path.join(student_folder, f) for f in files]

    @staticmethod
    def encode_image_to_base64(image_path: str) -> str:
        """將單張圖片檔案編碼為 Base64 字串"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    @staticmethod
    def write_text_file(file_path: str, content: str):
        """將內容寫入指定的文字檔"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    @classmethod
    def check_and_prepare_pipeline(cls, root_dir: str, output_dir_name: str, student_id: str, skip_processed: bool):
        """
        [核心修改] 處理所有檔案邏輯：
        1. 自動創立平行的輸出資料夾
        2. 檢查重複（中斷續傳）
        3. 處理空資料夾（返回空字串與狀態）
        """
        parent_dir = os.path.dirname(os.path.abspath(root_dir))
        target_output_dir = os.path.join(parent_dir, output_dir_name)
        
        # 1. 自動創立資料夾
        os.makedirs(target_output_dir, exist_ok=True)
        
        student_folder = os.path.join(root_dir, student_id)
        output_txt_path = os.path.join(target_output_dir, f"{student_id}_完整批改紀錄.txt")
        
        # 2. 檢查重複
        if skip_processed and os.path.exists(output_txt_path):
            return "SKIP", student_folder, output_txt_path, None

        # 3. 獲取圖片
        image_files = cls.get_image_files(student_folder)
        
        # 如果是空資料夾，返回 EMPTY 狀態，並且將圖片列表設為 None
        if not image_files:
            return "EMPTY", student_folder, output_txt_path, []
            
        return "RUN", student_folder, output_txt_path, image_files