import os
import sys
import base64

# 強制跳過 Pydantic 掃描
os.environ["PYDANTIC_DISABLE_PLUGINS"] = "1"

print("【系統提示】正在初始化 OpenAI Client...")
from openai import OpenAI

# 填入你的 Gemini API Key
client = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.environ.get("GCP_API_KEY")  # 換成你的 Gemini Key
)

def encode_image(image_path):
    """將圖片轉換為 Base64 字串"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def batch_process_students(root_dir):
    """批次處理所有學生資料夾"""
    if not os.path.exists(root_dir):
        print(f"❌ 錯誤：找不到總資料夾「{root_dir}」，請確認路徑。")
        return

    # 取得總資料夾底下的所有子項目
    subdirs = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]
    
    print(f"📂 找到 {len(subdirs)} 个學生的資料夾，開始執行自動化辨識...\n")

    for student_id in subdirs:
        student_folder = os.path.join(root_dir, student_id)
        output_txt_path = os.path.join(student_folder, f"{student_id}.txt")
        
        # 如果已經處理過，就跳過（方便中斷後續傳）
        if os.path.exists(output_txt_path):
            print(f"⏭️  學號 {student_id} 的 .txt 已存在，跳過。")
            continue

        # 找出資料夾內所有的 .png 或 .jpg 照片
        valid_extensions = ('.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG')
        image_files = [f for f in os.listdir(student_folder) if f.endswith(valid_extensions)]
        
        if not image_files:
            print(f"⚠️  學號 {student_id} 的資料夾內沒有照片。")
            continue

        print(f"🚀 正在處理學號 {student_id} (發現 {len(image_files)} 張照片)...")
        
        # 建立要送給 API 的 content 內容
        content_list = [
            {
                "type": "text", 
                "text": "請幫我辨識這些圖片中的所有文字。如果裡面包含數學公式，請將數學公式轉換為標準的 LaTeX 格式輸出。"
            }
        ]
        
        # 批次將一到兩張照片編碼並加入 content
        for img_name in image_files:
            img_path = os.path.join(student_folder, img_name)
            try:
                base64_image = encode_image(img_path)
                content_list.append({
                    "type": "image_url", 
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                })
            except Exception as e:
                print(f"  ❌ 讀取圖片 {img_name} 失敗: {e}")

        # 呼叫 API 取得單次 Response
        try:
            response = client.chat.completions.create(
                model="gemini-2.5-flash", 
                messages=[{"role": "user", "content": content_list}]
            )
            result_text = response.choices[0].message.content
            
            # 將結果寫入 學號.txt
            with open(output_txt_path, "w", encoding="utf-8") as f:
                f.write(result_text)
            
            print(f"  --> ✅ 成功生成 {student_id}.txt")
            
        except Exception as e:
            print(f"  ❌ 呼叫 API 失敗，學號 {student_id} 處理失敗。原因：\n{e}")

    print("\n🎉 所有資料夾處理完畢！")

# ==================== 執行區域 ====================
if __name__ == "__main__":
    # 請把這裡換成你存放所有學生學號資料夾的「總資料夾路徑」
    # 例如你的桌面上有一個名為 "student_homeworks" 的資料夾
    target_root_directory = "./" 
    
    batch_process_students(target_root_directory)