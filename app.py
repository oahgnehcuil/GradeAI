import os
import time
import streamlit as st

from file_handler import FileHandler
from grading_engine import GradingEngine

# ==================== 網頁頁面設定 ====================
st.set_page_config(page_title="AI 智慧考卷批改系統", layout="wide", page_icon="📝")
st.title("📝 AI 智慧考卷批改系統")
st.caption("請輸入考卷設定與學生資料夾路徑，系統將自動執行 OCR 辨識與 AI 批改。")

# ==================== 主頁面佈局：兩欄式輸入 ====================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📌 考試題目與評分標準設定")
    exam_question = st.text_area("1. 請輸入考試題目內容：", height=150, placeholder="例如：\nQ1. 請證明切爾諾夫界限 (Chernoff Bound)...")
    rubric_and_answer = st.text_area("2. 請輸入參考答案與評分標準：", height=350, placeholder="例如：\n### Q1 評分標準 (10分)\n- 定義隨機變數得 2 分...")

with col2:
    st.subheader("📂 學生資料處理設定")
    root_dir = st.text_input("請輸入伺服器/電腦上的「總資料夾路徑」：", value="./")
    
    # 優化選項
    skip_ocr = st.checkbox("如果 `{學號}.txt` 已存在，跳過文字辨識 (加速處理)", value=True)
    skip_grade = st.checkbox("如果 `_批改結果.txt` 已存在，跳過批改 (中斷續傳)", value=True)

st.markdown("---")

# ==================== 按鈕觸發與核心調度邏輯 ====================
if st.button("🚀 開始批次辨識與批改流水線", type="primary", use_container_width=True):
    if not exam_question.strip() or not rubric_and_answer.strip():
        st.warning("⚠️ 請填寫題目與評分標準再執行。")
    else:
        try:
            # 1. 掃描資料夾
            subdirs = FileHandler.get_student_directories(root_dir)
            
            if not subdirs:
                st.warning(f"⚠️ 在路徑「{root_dir}」下沒有找到任何學生子資料夾。")
            else:
                st.success(f"📂 成功找到 {len(subdirs)} 個學生的資料夾...")
                
                # 2. 初始化 AI 批改引擎（引擎會自己去抓環境變數的 Key，若找不到會報錯）
                engine = GradingEngine()
                
                # 3. 畫面進度與日誌容器
                progress_bar = st.progress(0)
                status_text = st.empty()
                log_container = st.expander("詳細執行日誌 (Log Stream)", expanded=True)
                
                # 4. 開始批次處理
                for index, student_id in enumerate(subdirs):
                    student_folder, ocr_txt_path, grade_txt_path = FileHandler.prepare_student_paths(root_dir, student_id)
                    status_text.text(f"⏳ 正在處理學生 ({index+1}/{len(subdirs)}): {student_id}")
                    
                    # --------- 階段一：圖片轉文字 (OCR) ---------
                    student_answer_text = ""
                    if skip_ocr and os.path.exists(ocr_txt_path):
                        log_container.write(f"⏭️ [OCR] 學號 {student_id} 的文字檔已存在，由本地讀取。")
                        student_answer_text = FileHandler.read_text_file(ocr_txt_path)
                    else:
                        image_files = FileHandler.get_image_files(student_folder)
                        if not image_files:
                            log_container.write(f"⚠️ [OCR] 學號 {student_id} 資料夾內找不到任何照片，跳過。")
                        else:
                            log_container.write(f"📸 [OCR] 正在辨識學號 {student_id} 的照片...")
                            try:
                                base64_list = [FileHandler.encode_image_to_base64(img) for img in image_files]
                                ocr_result = engine.run_ocr(base64_list)
                                student_answer_text = ocr_result
                                FileHandler.write_text_file(ocr_txt_path, ocr_result)
                                log_container.write(f"  --> ✅ 成功生成 `{student_id}.txt`")
                            except Exception as e:
                                log_container.write(f"  ❌ [OCR 失敗] 學號 {student_id} 處理中斷。原因：{e}")
                                continue

                    # --------- 階段二：AI 評分與批改 ---------
                    if not student_answer_text:
                        continue
                        
                    if skip_grade and os.path.exists(grade_txt_path):
                        log_container.write(f"⏭️ [批改] 學號 {student_id} 的批改結果已存在，跳過。")
                    else:
                        log_container.write(f"📝 [批改] 正在依據標準批改學號 {student_id} 的考卷...")
                        try:
                            grade_result = engine.grade_answer(
                                student_id=student_id,
                                student_answer=student_answer_text,
                                exam_question=exam_question,
                                rubric=rubric_and_answer
                            )
                            FileHandler.write_text_file(grade_txt_path, grade_result)
                            log_container.write(f"  --> ✅ 成功生成 `{student_id}_批改結果.txt`")
                            time.sleep(1)
                        except Exception as e:
                            log_container.write(f"  ❌ [批改 失敗] 學號 {student_id} 評分失敗。原因：{e}")
                    
                    progress_bar.progress((index + 1) / len(subdirs))
                
                status_text.text("🎉 所有考卷處理程序結束！")
                st.balloons()
                
        except ValueError as ve:
            st.error(str(ve))  # 專門捕捉缺少 API Key 的錯誤並顯示在畫面上
        except Exception as e:
            st.error(f"💥 系統執行時發生嚴重錯誤: {e}")