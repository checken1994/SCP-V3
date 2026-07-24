import os
import time
import json
import requests
import threading
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

# ===========================================================================
# 1. CẤU HÌNH API KEYS & CHẠY SONG SONG
# ===========================================================================
OPENROUTER_API_KEY = "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"
SERPER_API_KEY = "d921606b7d32371b5225f571b1f76a2e28198ea9"  # 👈 Dán Serper API Key vào đây

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "openai/gpt-4o-mini"

INPUT_FILE = "bo_de_1000_cau_v3-v2.xlsx"
OUTPUT_FILE = "ket_qua_scp_v3.xlsx"
SHEET_NAME = "1000_Cau_Hoi_MultiDomain"

MAX_WORKERS = 8          # Số câu hỏi xử lý song song cùng lúc (Khuyên dùng: 5 - 10 luồng)
SAVE_INTERVAL = 10       # Lưu file tự động sau mỗi 10 câu hoàn thành
NUM_SEARCH_RESULTS = 3   # Lấy 3 kết quả Google hàng đầu

# Khởi tạo OpenAI Client
llm_client = OpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=OPENROUTER_API_KEY,
)

# Lock bảo vệ dữ liệu khi nhiều luồng cùng ghi file
file_lock = threading.Lock()
completed_count = 0


# ===========================================================================
# 2. HÀM GOOGLE SEARCH (SERPER API)
# ===========================================================================
def search_google_serper(query, num_results=NUM_SEARCH_RESULTS):
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": query,
        "gl": "vn",
        "hl": "vi",
        "num": num_results
    })
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }

    contexts = []
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            organic_results = data.get("organic", [])
            for res in organic_results:
                title = res.get("title", "")
                snippet = res.get("snippet", "")
                if snippet:
                    contexts.append(f"[{title}]: {snippet}")
    except Exception as e:
        pass

    if not contexts:
        contexts = ["Không tìm thấy dữ liệu bổ trợ phù hợp từ Internet."]

    return contexts


# ===========================================================================
# 3. HÀM SCP V3 SINH CÂU TRẢ LỜI
# ===========================================================================
def generate_scp_answer(question, contexts):
    context_str = "\n".join([f"- {c}" for c in contexts])
    
    prompt = f"""Bạn là hệ thống AI SCP V3 chuyên nghiệp. Hãy sử dụng các thông tin tham chiếu dưới đây từ Internet để trả lời câu hỏi một cách chính xác, đầy đủ và khách quan nhất.

--- THÔNG TIN THAM CHIẾU TỪ INTERNET (CONTEXTS) ---
{context_str}

--- CÂU HỎI ---
{question}

--- CÂU TRẢ LỜI ---"""

    try:
        response = llm_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Bạn là hệ thống AI trả lời câu hỏi chuẩn xác dựa trên thông tin tìm kiếm thực tế."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Lỗi hệ thống khi tạo câu trả lời: {e}"


# ===========================================================================
# 4. HÀM XỬ LÝ TỪNG CÂU HỎI (WORKER TASK)
# ===========================================================================
def process_single_question(idx, question):
    contexts = search_google_serper(question)
    answer = generate_scp_answer(question, contexts)
    return idx, str(contexts), answer


# ===========================================================================
# 5. TIẾN TRÌNH CHẠY SONG SONG Multi-threading
# ===========================================================================
def main():
    global completed_count

    if SERPER_API_KEY == "YOUR_SERPER_API_KEY_HERE":
        print("❌ LỖI: Vui lòng mở file run_scp_v3.py và dán SERPER_API_KEY vào!")
        return

    print(f"🚀 BẮT ĐẦU CHẠY SONG SONG SCP V3 ({MAX_WORKERS} LUỒNG CÙNG LÚC)")
    print("=" * 65)

    if os.path.exists(OUTPUT_FILE):
        print(f"🔄 Đang khôi phục tiến độ từ '{OUTPUT_FILE}'...")
        df = pd.read_excel(OUTPUT_FILE)
    else:
        print(f"📂 Đang tải bộ đề từ '{INPUT_FILE}'...")
        df = pd.read_excel(INPUT_FILE, sheet_name=SHEET_NAME)

    total_rows = len(df)
    
    # Lọc danh sách các câu chưa làm
    tasks_to_run = []
    for idx, row in df.iterrows():
        question = str(row['question'])
        current_answer = str(row.get('answer', ''))

        if not (current_answer 
                and "Câu trả lời thực tế do SCP V3" not in current_answer 
                and current_answer.strip() != ""):
            tasks_to_run.append((idx, question))

    already_done = total_rows - len(tasks_to_run)
    completed_count = already_done
    print(f"📋 Tổng số: {total_rows} câu | Đã xong: {already_done} câu | Cần chạy: {len(tasks_to_run)} câu\n")

    if not tasks_to_run:
        print("🎉 Tất cả các câu hỏi đã được xử lý xong!")
        return

    start_time = time.time()

    # Thực thi đa luồng với ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(process_single_question, idx, q): idx 
            for idx, q in tasks_to_run
        }

        for future in as_completed(futures):
            idx, contexts_str, answer = future.result()

            # An toàn dữ liệu khi cập nhật DataFrame
            with file_lock:
                df.at[idx, 'contexts'] = contexts_str
                df.at[idx, 'answer'] = answer
                completed_count += 1

                print(f"✅ [{completed_count}/{total_rows}] Đã hoàn thành câu {idx + 1}")

                # Checkpoint tự động
                if completed_count % SAVE_INTERVAL == 0 or completed_count == total_rows:
                    df.to_excel(OUTPUT_FILE, index=False)
                    print(f"💾 [Checkpoint] Đã lưu tiến độ câu {completed_count}/{total_rows}")

    elapsed = time.time() - start_time
    print("\n" + "=" * 65)
    print(f"🎉 TỐC ĐỘ SIÊU TỐC! HOÀN THÀNH TẤT CẢ TRONG {elapsed:.1f} GIÂY ({elapsed/60:.2f} PHÚT)!")
    print(f"📂 File kết quả xuất tại: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()