import os
import json
import time
import pandas as pd
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed

# ===========================================================================
# 1. CẤU HÌNH API OPENROUTER & FILE
# ===========================================================================
OPENROUTER_API_KEY = "YOU API"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

INPUT_FILE = "ket_qua_scp_v3.xlsx"
OUTPUT_FILE = "bang_diem_scp_v3.xlsx"
JUDGE_MODEL = "openai/gpt-4o-mini"
MAX_WORKERS = 10  # Chấm điểm song song 10 câu/lượt

client = OpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=OPENROUTER_API_KEY
)

# ===========================================================================
# 2. PROMPT GIÁM KHẢO CHẤM ĐIỂM RAGAS (4 TIÊU CHÍ)
# ===========================================================================
EVAL_PROMPT = """Bạn là Chuyên gia Đánh giá Hệ thống RAG (RAGAS Evaluator).
Hãy chấm điểm câu trả lời của AI dựa trên 4 tiêu chí chuẩn quốc tế (thang điểm từ 0.0 đến 1.0):

1. **faithfulness** (Chống ảo giác): Câu trả lời có căn cứ 100% từ Context không? (1.0 = Hoàn toàn căn cứ từ context, 0.0 = Bịa đặt/Ảo giác).
2. **answer_relevancy** (Mức độ bám sát): Câu trả lời có đúng trọng tâm câu hỏi không? (1.0 = Đúng trọng tâm, 0.0 = Lan man/Lạc đề).
3. **context_precision** (Độ chính xác dữ liệu): Context cào về có chứa thông tin đúng câu hỏi không? (1.0 = Rất chính xác, 0.0 = Dữ liệu rác).
4. **context_recall** (Độ đầy đủ dữ liệu): Context cào về có đủ ý để trả lời trọn vẹn câu hỏi không? (1.0 = Đầy đủ, 0.0 = Thiếu thông tin).

--- DỮ LIỆU CẦN ĐÁNH GIÁ ---
- CÂU HỎI (Question): {question}
- TẬP DỮ LIỆU CÀO VỀ (Contexts): {contexts}
- CÂU TRẢ LỜI CỦA AI (Answer): {answer}

--- YÊU CẦU ĐẦU RA ---
Trả về kết quả duy nhất ở định dạng JSON chuẩn (không thêm văn bản khác):
{{\"faithfulness\": 1.0, \"answer_relevancy\": 1.0, \"context_precision\": 1.0, \"context_recall\": 1.0}}"""

def evaluate_row(idx, question, contexts, answer):
    prompt = EVAL_PROMPT.format(
        question=str(question),
        contexts=str(contexts),
        answer=str(answer)
    )
    
    try:
        response = client.chat.completions.create(
            model=JUDGE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        res_text = response.choices[0].message.content.strip()
        scores = json.loads(res_text)
        return idx, scores.get("faithfulness", 0.0), scores.get("answer_relevancy", 0.0), scores.get("context_precision", 0.0), scores.get("context_recall", 0.0)
    except Exception as e:
        return idx, 0.0, 0.0, 0.0, 0.0

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ KHÔNG THẤY FILE '{INPUT_FILE}'. Vui lòng chạy 'python run_scp_v3.py' trước!")
        return

    print(f"📂 Đang đọc dữ liệu từ '{INPUT_FILE}'...")
    df = pd.read_excel(INPUT_FILE)
    total = len(df)
    
    print(f"⚖️ ĐẮT ĐẦU CHẤM ĐIỂM RAGAS CHO {total} CÂU (CHẠY SONG SONG {MAX_WORKERS} LUỒNG)...")
    start_time = time.time()

    df['faithfulness'] = 0.0
    df['answer_relevancy'] = 0.0
    df['context_precision'] = 0.0
    df['context_recall'] = 0.0

    tasks = []
    for idx, row in df.iterrows():
        tasks.append((idx, row['question'], row.get('contexts', ''), row.get('answer', '')))

    done = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(evaluate_row, idx, q, c, a): idx 
            for idx, q, c, a in tasks
        }

        for future in as_completed(futures):
            idx, f_score, a_score, cp_score, cr_score = future.result()
            df.at[idx, 'faithfulness'] = f_score
            df.at[idx, 'answer_relevancy'] = a_score
            df.at[idx, 'context_precision'] = cp_score
            df.at[idx, 'context_recall'] = cr_score
            
            done += 1
            if done % 20 == 0 or done == total:
                print(f"✅ Đã chấm xong [{done}/{total}] câu...")

    # Tính điểm trung bình %
    avg_f = df['faithfulness'].mean() * 100
    avg_a = df['answer_relevancy'].mean() * 100
    avg_cp = df['context_precision'].mean() * 100
    avg_cr = df['context_recall'].mean() * 100

    print("\n" + "=" * 60)
    print("📊 BẢNG TỔNG HỢP ĐIỂM SỐ ĐÁNH GIÁ CỦA SCP V3 (RAGAS METRICS)")
    print("=" * 60)
    print(f" • Faithfulness (Chống ảo giác)     : {avg_f:.2f}%")
    print(f" • Answer Relevancy (Bám sát câu hỏi): {avg_a:.2f}%")
    print(f" • Context Precision (Chính xác context): {avg_cp:.2f}%")
    print(f" • Context Recall (Đầy đủ context)   : {avg_cr:.2f}%")
    print("=" * 60)

    df.to_excel(OUTPUT_FILE, index=False)
    elapsed = time.time() - start_time
    print(f"\n💾 Bảng điểm chi tiết đã lưu tại: {OUTPUT_FILE}")
    print(f"⏱️ Hoàn tất trong: {elapsed/60:.2f} phút!")

if __name__ == "__main__":
    main()