import os
import sys
import time

# 強制跳過 Pydantic 掃描
os.environ["PYDANTIC_DISABLE_PLUGINS"] = "1"

# 🔥 【黑魔法修正】阻止 httpcore 載入 trio，解決你上一階段卡住的問題
sys.modules['trio'] = None

print("【系統提示】正在初始化 OpenAI Client...")
from openai import OpenAI

# 填入你的 Gemini API Key
client = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.environ.get("GCP_API_KEY")  # 換成你的 Gemini Key
)

# ==================== 批改標準設定 ====================
# 💡 請在這裡輸入這份考卷的題目、正確答案以及評分標準，AI 會嚴格遵循此標準
ANSWER_KEY_AND_RUBRIC = """
### 1. Define an $f$-valid protocol for a binary function $f$ (2 points)

A randomized protocol $\Pi$ for a binary function $f: X \times Y \to \{0,1\}$ is **$f$-valid** if it computes $f$ with a bounded error probability strictly less than $1/2$ for **every** possible input pair. 

Formally, there exists a constant $\gamma > 0$ such that for all inputs $(x, y) \in X \times Y$:
$$\mathbb{P}_{R}[\Pi(x, y, R) \neq f(x, y)] \le 0.5 - \gamma$$
where $R$ represents the shared or private randomness used in the protocol.

---

### 2. Define an $(, \pi)$-valid (deterministic or randomized) protocol for a binary function $f$ with respect to an input distrubution $\pi$ (3 points)

A protocol $\Pi$ is **$(f, \pi)$-valid** with respect to an input distribution $\pi$ over $X \times Y$ if its **average error** over the distribution $\pi$ is strictly less than $1/2$.

Formally, there exists a constant $\gamma > 0$ such that:
$$\mathbb{P}_{(x, y) \sim \pi, R}[\Pi(x, y, R) \neq f(x, y)] \le 0.5 - \gamma$$

> **Key Difference:** An $f$-valid protocol must succeed with high probability on *worst-case* inputs, whereas an $(f, \pi)$-valid protocol only needs to succeed with high probability on *average* when inputs are sampled from the distribution $\pi$.

---

### 3. Let $T_f$ be an $f$-valid randomized protocol for a binary $f$. Prove that its error probability can be reduced from 0.5 - $\Omega(1)$ to O(1/t) by repeatedly and independently executing it for O(logt) rounds and outputting the answer that appears the majority of the time.(10 points)

Let $T_f$ be the given $f$-valid protocol. For any fixed input $(x, y)$, let its error probability be $\epsilon \le 0.5 - \gamma$, where $\gamma = \Omega(1) > 0$ is a constant advantage over random guessing.

We run $T_f$ independently for $N = c \log t$ rounds (where $c$ is a constant to be determined) and output the majority answer.

#### Step 1: Define Random Variables
Let $X_i$ be an indicator random variable for the $i$-th round:
$$X_i = \begin{cases} 1 & \text{if the } i\text{-th round returns an incorrect answer} \\ 0 & \text{if the } i\text{-th round returns the correct answer} \end{cases}$$

Since each execution is independent, $X_1, X_2, \dots, X_N$ are independent Bernoulli trials with a probability of failure $\mathbb{P}(X_i = 1) = \epsilon \le 0.5 - \gamma$.

Let $X = \sum_{i=1}^N X_i$ be the total number of failed rounds. The majority vote will output an incorrect answer if and only if at least half of the rounds fail:
$$\mathbb{P}(\text{Majority Vote Fails}) = \mathbb{P}\left(X \ge \frac{N}{2}\right)$$

#### Step 2: Apply the Chernoff Bound
The expected number of failures is:
$$\mu = \mathbb{E}[X] = N\epsilon \le N(0.5 - \gamma)$$

We want to bound the probability that $X \ge \frac{N}{2}$. Let's express $\frac{N}{2}$ in terms of $\mu$:
$$\frac{N}{2} = N(0.5 - \gamma + \gamma) = \mu + \gamma N = \mu \left(1 + \frac{\gamma}{\epsilon}\right)$$

Using the standard additive form of the Chernoff bound, for independent random variables $X_i \in [0,1]$ with $\mathbb{E}[X] = \mu$:
$$\mathbb{P}(X \ge \mu + \lambda) \le e^{-2\lambda^2 / N}$$

Setting $\lambda = \gamma N$:
$$\mathbb{P}\left(X \ge \frac{N}{2}\right) \le e^{-2(\gamma N)^2 / N} = e^{-2\gamma^2 N}$$

#### Step 3: Determine the Number of Rounds $N$
We want the final error probability to be at most $O(1/t)$. Let's set:
$$e^{-2\gamma^2 N} \le \frac{1}{t}$$

Taking the natural logarithm on both sides:
$$-2\gamma^2 N \le -\ln t \implies N \ge \frac{1}{2\gamma^2} \ln t$$

Since $\gamma = \Omega(1)$ is a constant, the coefficient $\frac{1}{2\gamma^2}$ is also a constant. Thus, we can choose $N = O(\log t)$ rounds to achieve an error probability of $O(1/t)$. $\blacksquare$
"""

def call_gemini_with_retry(system_prompt, user_content, max_retries=5):
    """呼叫 Gemini API 的核心函式，內建自動重試迴圈（防繁忙、防斷線）"""
    delay = 2  # 初始等待秒數
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gemini-2.5-flash", 
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"  ⚠️ API 繁忙或連線失敗 (第 {attempt + 1}/{max_retries} 次嘗試). 原因: {e}")
            if attempt == max_retries - 1:
                # 超過最大重試次數，直接拋出錯誤讓外層處理
                raise e
            print(f"  ⏳ 等待 {delay} 秒後重新嘗試...")
            time.sleep(delay)
            delay *= 2  # 每次失敗等待時間加倍 (2s -> 4s -> 8s -> 16s)

def batch_grade_students(root_dir):
    """批次讀取學生的 .txt 檔案並進行 AI 批改"""
    if not os.path.exists(root_dir):
        print(f"❌ 錯誤：找不到總資料夾「{root_dir}」，請確認路徑。")
        return

    subdirs = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]
    print(f"📂 找到 {len(subdirs)} 個學生的資料夾，開始執行自動化批改...\n")

    for student_id in subdirs:
        student_folder = os.path.join(root_dir, student_id)
        input_txt_path = os.path.join(student_folder, f"{student_id}.txt")
        output_grade_path = os.path.join(student_folder, f"{student_id}_批改結果.txt")
        
        # 1. 檢查是否有需要批改的來源檔
        if not os.path.exists(input_txt_path):
            continue
            
        # 2. 【斷點續傳】如果已經有批改結果，直接跳過！
        # 如果你想「全部重新批改」，只需要把資料夾內的「_批改結果.txt」刪除，或者把這段 if 註解掉
        if os.path.exists(output_grade_path):
            print(f"⏭️  學號 {student_id} 的批改結果已存在，跳過。")
            continue

        print(f"📝 正在批改學號 {student_id} 的考卷...")
        
        try:
            with open(input_txt_path, "r", encoding="utf-8") as f:
                student_answer = f.read()
        except Exception as e:
            print(f"  ❌ 讀取學號 {student_id}.txt 失敗: {e}")
            continue

        # 3. 準備 Prompt
        system_prompt = "你是一位嚴格且公平的老師。請根據提供的「標準答案與評分標準」，對學生的作答內容進行批改，給出每題得分、扣分原因，以及總分。"
        user_content = f"""
{ANSWER_KEY_AND_RUBRIC}

--------------------------------------------------
【學生作答內容 (學號: {student_id})】
{student_answer}
--------------------------------------------------

請依據上述標準進行批改，並用以下格式輸出：
1. 每題得分與詳細評語（指出錯誤在哪裡，若使用 LaTeX 公式請以 $ 包覆）
2. 總分：XX / 總滿分
3. 給學生的鼓勵或建議
"""

        # 4. 呼叫帶有重試機制的 API 函式
        try:
            grade_result = call_gemini_with_retry(system_prompt, user_content, max_retries=5)
            
            # 5. 寫入結果
            with open(output_grade_path, "w", encoding="utf-8") as f:
                f.write(grade_result)
            print(f"  --> ✅ 成功生成 {student_id}_批改結果.txt")
            
            # 💡 為了避免太頻繁呼叫被 API 鎖定，每批改完一個學生，稍微休息 1 秒鐘
            time.sleep(1)
            
        except Exception as e:
            print(f"  ❌ 學號 {student_id} 經過多次重試仍失敗，跳過此學生。")

    print("\n🎉 所有考卷處理程序結束！")

# ==================== 執行區域 ====================
if __name__ == "__main__":
    target_root_directory = "./" 
    batch_grade_students(target_root_directory)