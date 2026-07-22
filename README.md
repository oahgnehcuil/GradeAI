# 🎓 GradeAI

GradeAI is a Python and Streamlit-based intelligent tool designed for grade analysis, automated evaluation, and batch submission grading. It offers a clean, user-friendly interactive web interface for effortless data processing and instant insights.

---

## 🚀 Quick Start

Launch the application directly from your terminal with a single command:

```bash
streamlit run app.py
```

Once executed, the Web UI will automatically open in your browser (default at `http://localhost:8501`).

---

## 💡 Key Features & Usage

### 1. Interactive Mode
* **Enter Data**: Fill in individual parameters or test inputs step-by-step into the corresponding input fields.
* **Analyze & Review**: Submit your inputs to view real-time grading, suggestions, and feedback directly on screen.

### 2. Batch Grading Mode 
For batch grading, organize your submissions root directory into student subfolders where each folder contains image scans of a student's answer sheets:

#### 📁 Directory Structure
```text
question/
├── b14902997/
│   ├── paper1.png
│   ├── paper2.png
│   └── ...
├── b14902998/
│   ├── paper1.png
│   └── paper2.png
└── b14902999/
    ├── paper1.png
    └── paper2.png
```

#### 🔄 Workflow
1. Select **Batch Grading Mode** in the Streamlit UI.
2. Enter or select the path to your target question folder (e.g., `./question/`).
3. GradeAI will automatically scan all student directories (e.g., `b14902997`, `b14902998`), process every answer sheet (`paper1.png`, `paper2.png`, etc.), and generate a consolidated evaluation report.

### 3. Export Reports (.tex & .pdf)
GradeAI supports exporting generated reports into publication-quality LaTeX documents and PDFs:
* **Download LaTeX Source (`.tex`)**: Export raw `.tex` files for custom editing or integration into your academic workflows.
* **Convert & Download PDF (`.pdf`)**: Generate and download compiled PDF reports directly from the UI with a single click.

> **Note for PDF Generation**: Ensure you have a working TeX distribution (e.g., `xelatex` / `pdflatex`) installed on your system if you plan to compile PDF reports locally:
> ```bash
> # macOS (MacTeX)
> brew install --cask mactex
>
> # Ubuntu/Debian
> sudo apt-get install texlive-full

---

## 🛠️ Install Dependencies

Make sure you have Python 3.8+ installed before running the app.

```bash
pip install -r requirements.txt
```

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to open an issue or submit a pull request.