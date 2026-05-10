import streamlit as st
import pandas as pd
import random
import os
import time

# --- CẤU HÌNH GIAO DIỆN MOBILE ---
st.set_page_config(page_title="Tagalog Master", page_icon="🇵🇭", layout="centered")

st.markdown("""
    <style>
    /* Làm nút bấm to và dễ chạm trên điện thoại */
    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        font-size: 18px !important;
        font-weight: bold;
        margin-bottom: 10px;
        border: 2px solid #4CAF50;
    }
    /* Tùy chỉnh thanh tiến độ màu xanh lá */
    .stProgress > div > div > div > div { background-color: #4CAF50; }
    /* Chỉnh cỡ chữ câu hỏi */
    .question-box { font-size: 22px; font-weight: 600; color: #1E3A8A; background: #E0F2FE; padding: 20px; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. HÀM TẢI DỮ LIỆU ---
@st.cache_data
def load_data():
    files = ["sach_Tagalog_02.xlsx", "sach_Tagalog_03.xlsx", "sach_Tagalog_04.xlsx"]
    all_rows = []
    for f in files:
        if os.path.exists(f):
            try:
                xl = pd.ExcelFile(f)
                book_name = f.split('_')[-1].split('.')[0] # Lấy "02", "03"...
                for sheet in xl.sheet_names:
                    if "Mục lục" in sheet or "Sheet" in sheet: continue
                    df = pd.read_excel(f, sheet_name=sheet, engine='openpyxl')
                    if df.shape[1] >= 3:
                        df = df.iloc[:, [1, 2]]
                        df.columns = ['VN', 'TG']
                        df = df.dropna(subset=['TG'])
                        df['VN'] = df['VN'].ffill()
                        df['Lesson'] = f"Sách {book_name} - {sheet}"
                        all_rows.append(df)
            except: continue
    return pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()

df_main = load_data()

# --- 2. KHỞI TẠO TRẠNG THÁI ---
if 'current_idx' not in st.session_state: st.session_state.current_idx = 0
if 'user_answer' not in st.session_state: st.session_state.user_answer = []
if 'start_time' not in st.session_state: st.session_state.start_time = time.time()
if 'lesson_pool' not in st.session_state: st.session_state.lesson_pool = []

# --- 3. SIDEBAR CHỌN BÀI ---
st.sidebar.header("📚 Lựa chọn bài học")
lessons = sorted(df_main['Lesson'].unique())
selected = st.sidebar.selectbox("Chọn bài:", lessons)

if 'last_selected' not in st.session_state or st.session_state.last_selected != selected:
    st.session_state.lesson_pool = df_main[df_main['Lesson'] == selected].to_dict('records')
    random.shuffle(st.session_state.lesson_pool)
    st.session_state.current_idx = 0
    st.session_state.last_selected = selected
    st.session_state.user_answer = []
    st.session_state.new_q = True

# --- 4. LOGIC CHÍNH ---
pool = st.session_state.lesson_pool
if st.session_state.current_idx < len(pool):
    item = pool[st.session_state.current_idx]
    
    # THANH TIẾN ĐỘ
    progress = (st.session_state.current_idx) / len(pool)
    st.progress(progress)
    st.caption(f"Tiến độ: {st.session_state.current_idx}/{len(pool)} câu")

    # HIỂN THỊ CÂU HỎI
    st.markdown(f'<div class="question-box">{item["VN"]}</div>', unsafe_allow_html=True)
    
    # CÂU ĐANG GHÉP
    st.write("---")
    ans_text = " ".join(st.session_state.user_answer)
    st.subheader(f"👉 {ans_text if ans_text else '...'}")

    # TẠO WORD BANK
    if st.session_state.new_q:
        target = str(item['TG']).replace('!', '').replace('?', '').replace('.', '').replace(',', '').replace('"', '')
        words = target.split()
        distractors = random.sample(" ".join(df_main['TG'].astype(str)).split(), 2)
        pool_words = list(set(words + distractors))
        random.shuffle(pool_words)
        st.session_state.words = pool_words
        st.session_state.start_time = time.time()
        st.session_state.new_q = False

    # HIỂN THỊ NÚT CHỌN TỪ (2 cột cho điện thoại dễ bấm)
    cols = st.columns(2)
    for i, w in enumerate(st.session_state.words):
        if cols[i % 2].button(w, key=f"btn_{i}"):
            st.session_state.user_answer.append(w)
            st.rerun()

    # NÚT ĐIỀU KHIỂN
    c1, c2 = st.columns(2)
    if c1.button("🔙 Xóa từ cuối", use_container_width=True):
        if st.session_state.user_answer: st.session_state.user_answer.pop(); st.rerun()
    if c2.button("🔄 Làm lại câu", use_container_width=True):
        st.session_state.user_answer = []; st.rerun()

    # KIỂM TRA TỰ ĐỘNG
    current_user_ans = " ".join(st.session_state.user_answer).lower().strip()
    target_clean = str(item['TG']).lower().replace('!', '').replace('?', '').replace('.', '').replace(',', '').replace('"', '').strip()
    
    if current_user_ans == target_clean:
        elapsed = time.time() - st.session_state.start_time
        st.success(f"Chính xác! (Phản xạ: {elapsed:.2f}s)")
        st.balloons()
        time.sleep(1) # Chờ 1 giây rồi tự nhảy câu
        st.session_state.current_idx += 1
        st.session_state.user_answer = []
        st.session_state.new_q = True
        st.rerun()
else:
    st.success("🎉 Bạn đã hoàn thành bài học này!")
    if st.button("Học lại từ đầu"):
        st.session_state.current_idx = 0
        st.rerun()