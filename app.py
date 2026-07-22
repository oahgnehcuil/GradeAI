import os
import time
import streamlit as st

from file_handler import FileHandler
from grading_engine import GradingEngine

# ==================== 網頁頁面設定 ====================
st.set_page_config(page_title="AI 智慧考卷批改系統", layout="wide", page_icon="📝")
st.title("📝 AI 智慧考卷批改系統")

col1, col2 = st.columns(2)
with col1:
    st.subheader("📌 考試題目與評分標準設定")
    exam_question = st.text_area("1. 請輸入考試題目內容：", height=150, placeholder="例如：\nQ1. 請證明切爾諾夫界限...")
    rubric_and_answer = st.text_area("2. 請輸入參考答案與評分標準：", height=350, placeholder="例如：\n### Q1 評分標準...")

with col2:
    st.subheader("📂 學生資料與輸出設定")
    st.markdown("**1. 請輸入學生原始總資料夾的絕對路徑：**")
    root_dir = st.text_input("學生總資料夾路徑：", value="", placeholder="例如：./GradeAI/學生考卷", label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("**2. 設定統一輸出資料夾名稱：**")
    output_dir_name = st.text_input("請輸入輸出資料夾名稱：", value="批改結果PDF總表")
    
    st.markdown("---")
    st.markdown("**3. 執行優化設定：**")
    skip_processed = st.checkbox("如果批改紀錄 (.pdf) 已存在，跳過該學生 (中斷續傳)", value=True)

st.markdown("---")

# ==================== 核心調度邏輯 ====================
if st.button("🚀 開始批次辨識與批改流水線", type="primary", use_container_width=True):
    if not exam_question.strip() or not rubric_and_answer.strip() or not root_dir.strip() or not output_dir_name.strip():
        st.warning("⚠️ 請檢查所有欄位是否皆已填寫（包含學生資料夾路徑）。")
    else:
        try:
            engine = GradingEngine()
            subdirs = FileHandler.get_student_directories(root_dir)
            
            if not subdirs:
                st.warning(f"⚠️ 在該路徑下找不到任何學生子資料夾。")
            else:
                st.success(f"📂 成功找到 {len(subdirs)} 個學生的資料夾，開始流水線處理...")
                progress_bar = st.progress(0)
                status_text = st.empty()
                log_container = st.expander("詳細執行日誌 (Log Stream)", expanded=True)
                
                for index, student_id in enumerate(subdirs):
                    status_text.text(f"⏳ 正在處理學生 ({index+1}/{len(subdirs)}): {student_id}")
                    
                    status, student_folder, output_tex_path, image_files = FileHandler.check_and_prepare_pipeline(
                        root_dir, output_dir_name, student_id, skip_processed
                    )
                    
                    if status == "SKIP":
                        log_container.write(f"⏭️ [跳過] 學號 {student_id} 的 PDF 批改檔已存在。")
                        progress_bar.progress((index + 1) / len(subdirs))
                        continue
                        
                    student_answer_text = ""
                    
                    if status == "EMPTY":
                        log_container.write(f"⚠️ [空資料夾] 學號 {student_id} 內無照片，將以「未作答」形式送交 AI 評分。")
                        student_answer_text = "（⚠️ 系統提示：該學生資料夾為空，未提交任何作答圖片內容。）"
                    else:
                        log_container.write(f"📸 [OCR] 正在辨識學號 {student_id} 的照片...")
                        try:
                            base64_list = [FileHandler.encode_image_to_base64(img) for img in image_files]
                            student_answer_text = engine.run_ocr(base64_list)
                        except Exception as e:
                            log_container.write(f"  ❌ [OCR 失敗] 學號 {student_id} 原因：{e}")
                            continue

                    log_container.write(f"📝 [批改] 正在依據標準批改學號 {student_id} 的考卷...")
                    try:
                        grade_result = engine.grade_answer(
                            student_id=student_id,
                            student_answer=student_answer_text,
                            exam_question=exam_question,
                            rubric=rubric_and_answer
                        )
                        
                        # 🚀 【核心修改】：直接在這裡將結果包裝成完整的 LaTeX 文件格式
                        combined_content = rf"""\documentclass[12pt, a4paper]{{article}}
\usepackage{{xeCJK}}
\usepackage{{amsmath, amsfonts, amssymb}}
\usepackage{{geometry}}
\usepackage{{xcolor}}
\usepackage[most]{{tcolorbox}}

\geometry{{margin=2cm}}
\setCJKmainfont{{PingFang TC}}[AutoFakeBold=true, FallbackFonts={{Microsoft JhengHei}}]

\title{{\textbf{{考卷自動批改報告}}}}
\author{{學號：{student_id}}}
\date{{\today}}

\begin{{document}}
\maketitle

\section*{{一、學生作答內容辨識}}
{student_answer_text}

\section*{{二、AI 老師批改回饋}}
{grade_result}

\end{{document}}
"""
                        # 1. 寫入 .tex 檔
                        FileHandler.write_text_file(output_tex_path, combined_content)
                        log_container.write(f"  --> 📄 成功生成 LaTeX 檔：`{student_id}_完整批改紀錄.tex`")
                        
                        # 2. 呼叫編譯產生 PDF
                        pdf_success = FileHandler.compile_tex_to_pdf(output_tex_path)
                        if pdf_success:
                            log_container.write(f"  --> 🎉 ✅ 成功編譯出 PDF：`{student_id}_完整批改紀錄.pdf`")
                        else:
                            log_container.write(f"  --> ⚠️ `.tex` 已建立，但 `xelatex` 自動編譯成 PDF 失敗（請確認電腦是否有安裝 xelatex）。")
                            
                        time.sleep(1)
                    except Exception as e:
                        log_container.write(f"  ❌ [批改 失敗] 學號 {student_id} 原因：{e}")
                    
                    progress_bar.progress((index + 1) / len(subdirs))
                
                status_text.text("🎉 所有考卷處理程序結束！")
                st.balloons()
        except Exception as e:
            st.error(f"💥 系統錯誤: {e}")