import streamlit as st
import pandas as pd
import random
import os
import time
import streamlit.components.v1 as components

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="Tagalog Instinct Pro", page_icon="⚡", layout="centered")

# --- 2. CSS "ĐẶC TRỊ" KHOẢNG CÁCH VÀ CỠ CHỮ ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');

    /* Font và Nền */
    html, body, [class*="View"] {
        font-family: 'Inter', sans-serif;
        background-color: #F8FAFC !important;
    }

    /* TRIỆT TIÊU KHOẢNG CÁCH GIỮA CÁC CỘT */
    [data-testid="column"] {
        padding: 0px 2px !important;  /* Giảm tối đa padding giữa các ô */
        margin: 0px !important;
    }
    [data-testid="stHorizontalBlock"] {
        gap: 4px !important; /* Thu hẹp khoảng cách giữa các nút */
    }

    /* THẺ CÂU HỎI TIẾNG VIỆT */
    .vn-card {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        font-size: 24px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* CHỮ "CÒN LẠI BAO NHIÊU CÂU" */
    .status-text {
        font-size: 20px;
        color: #EF4444; /* Màu đỏ nổi bật */
        font-weight: 700;
        text-align: center;
        margin-bottom: 5px;
    }

    /* VÙNG KẾT QUẢ CHỮ SIÊU TO */
    .result-box {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 12px;
        border: 3px solid #6366F1;
        min-height: 70px;
        margin: 10px 0px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .result-text {
        color: #1E40AF;
        font-size: 30px; /* Cỡ chữ kết quả rất to */
        font-weight: 900;
        text-align: center;
    }

    /* NÚT BẤM CHỌN TỪ SIÊU TO */
    div.stButton > button {
        width: 100% !important;
        background-color: #FFFFFF !important;
        color: #1F2937 !important;
        border: 2px solid #94A3B8 !important;
        border-radius: 12px !important;
        padding: 18px 5px !important; /* Tăng padding để nút cao hơn */
        font-size: 22px !important;  /* Cỡ chữ trong nút to hơn */
        font-weight: 700 !important;
        box-shadow: 0px 4px 0px #CBD5E1 !important;
        transition: none !important;
    }
    div.stButton > button:active {
        box-shadow: none !important;
        transform: translateY(2px) !important;
    }

    /* Thanh tiến độ */
    .stProgress > div > div > div > div {
        background-color: #10B981 !important;
        height: 14px !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #0F172A !important; }
    [data-testid="stSidebar"] * { color: #F1F5F9 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. HÀM ĐỌC ÂM THANH ---
def speak_tagalog(text):
    if not text: return
    text_clean = text.replace('"', '').replace("'", "")
    js_code = f"""
        <script>
        function speak() {{
            window.speechSynthesis.cancel();
            const utter = new SpeechSynthesisUtterance("{text_clean}");
            const voices = window.speechSynthesis.getVoices();
            const target = voices.find(v => v.lang.includes('tl-PH') || v.lang.includes('fil-PH')) 
                           || voices.find(v => v.name.includes('Google'));
            if (target) utter.voice = target;
            utter.lang = 'tl-PH';
            utter.rate = 0.85;
            window.speechSynthesis.speak(utter);
        }}
        if (window.speechSynthesis.getVoices().length === 0) {{
            window.speechSynthesis.onvoiceschanged = speak;
        }} else {{ speak(); }}
        </script>
    """
    components.html(js_code, height=0)

# --- 4. LOAD DỮ LIỆU ---
@st.cache_data
def load_data():
    files = ["sach_Tagalog_02.xlsx", "sach_Tagalog_03.xlsx", "sach_Tagalog_04.xlsx"]
    all_rows = []
    for f in files:
        if os.path.exists(f):
            try:
                xl = pd.ExcelFile(f)
                book_id = f.split('_')[-1].replace('.xlsx', '')
                for sheet in xl.sheet_names:
                    if any(x in sheet for x in ["Mục lục", "Sheet"]): continue
                    df = pd.read_excel(xl, sheet_name=sheet, engine='openpyxl')
                    if df.shape[1] >= 3:
                        df = df.iloc[:, [1, 2]]
                        df.columns = ['VN', 'TG']
                        df = df.dropna(subset=['TG'])
                        df['VN'] = df['VN'].ffill()
                        df['Lesson_ID'] = f"Sách {book_id} • {sheet}"
                        all_rows.append(df)
            except: continue
    return pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()

df_main = load_data()

# --- 5. QUẢN LÝ TRẠNG THÁI ---
if 'history' not in st.session_state: st.session_state.history = []
if 'lesson_pool' not in st.session_state: st.session_state.lesson_pool = []
if 'user_answer_indices' not in st.session_state: st.session_state.user_answer_indices = []
if 'active_q_text' not in st.session_state: st.session_state.active_q_text = ""

# --- 6. SIDEBAR ---
st.sidebar.markdown("# 🏆 TRÌNH LUYỆN BẢN NĂNG")
lessons = sorted(df_main['Lesson_ID'].unique())

# Hiển thị lịch sử bài đã làm
st.sidebar.subheader("Lịch sử bài học")
for h in st.session_state.history:
    st.sidebar.write(f"✅ {h}")

selected = st.sidebar.selectbox("Chọn bài học:", lessons)

if 'last_selected' not in st.session_state or st.session_state.last_selected != selected:
    filtered = df_main[df_main['Lesson_ID'] == selected].to_dict('records')
    random.shuffle(filtered)
    st.session_state.lesson_pool = filtered
    st.session_state.total_in_lesson = len(filtered)
    st.session_state.last_selected = selected
    st.session_state.active_q_text = ""

# --- 7. LOGIC CHÍNH ---
if st.session_state.lesson_pool:
    item = st.session_state.lesson_pool[0]
    rem = len(st.session_state.lesson_pool)
    total = st.session_state.total_in_lesson
    done = total - rem

    # HIỂN THỊ TIẾN ĐỘ RÕ RÀNG
    st.markdown(f'<p class="status-text">Đã xong: {done}/{total} câu — CÒN LẠI: {rem} CÂU</p>', unsafe_allow_html=True)
    st.progress(done / total)

    # ĐỒNG BỘ CÂU HỎI
    if st.session_state.active_q_text != item['VN']:
        st.session_state.active_q_text = item['VN']
        target = str(item['TG']).replace('!', '').replace('?', '').replace('.', '').replace(',', '').replace('"', '')
        ans_words = target.split()
        distractors = random.sample(" ".join(df_main['TG'].astype(str)).split(), 2)
        combined = ans_words + distractors
        random.shuffle(combined)
        st.session_state.words_with_id = list(enumerate(combined))
        st.session_state.user_answer_indices = []
        st.session_state.start_time = time.time()
        speak_tagalog(item['TG'])

    # CÂU HỎI
    st.markdown(f'<div class="vn-card">{item["VN"]}</div>', unsafe_allow_html=True)
    
    # VÙNG KẾT QUẢ CHỌN
    current_string = " ".join([st.session_state.words_with_id[i][1] for i in st.session_state.user_answer_indices])
    st.markdown(f'<div class="result-box"><p class="result-text">{current_string if current_string else "..."}</p></div>', unsafe_allow_html=True)

    # WORD BANK (Nút bấm to và sát nhau)
    cols = st.columns(3)
    for idx, (original_idx, word) in enumerate(st.session_state.words_with_id):
        if original_idx not in st.session_state.user_answer_indices:
            if cols[idx % 3].button(word, key=f"btn_{original_idx}"):
                st.session_state.user_answer_indices.append(original_idx)
                st.rerun()

    # NÚT ĐIỀU KHIỂN
    st.write("")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🔙 Xóa", key="clear"):
            if st.session_state.user_answer_indices: st.session_state.user_answer_indices.pop(); st.rerun()
    with c2:
        if st.button("🔄 Lại", key="reset"):
            st.session_state.user_answer_indices = []; st.rerun()
    with c3:
        if st.button("🔊 Nghe", key="audio"):
            speak_tagalog(item['TG'])

    # KIỂM TRA TỰ ĐỘNG
    user_ans_lower = current_string.lower().strip()
    target_clean = str(item['TG']).lower().replace('!', '').replace('?', '').replace('.', '').replace(',', '').replace('"', '').strip()
    
    if user_ans_lower == target_clean:
        elapsed = time.time() - st.session_state.start_time
        speak_tagalog(item['TG'])
        if elapsed <= 5.0:
            st.success(f"⚡ BẢN NĂNG: {elapsed:.2f}s")
            st.session_state.lesson_pool.pop(0)
        else:
            st.warning(f"🐢 CHẬM ({elapsed:.2f}s) - Sẽ làm lại!")
            slow_item = st.session_state.lesson_pool.pop(0)
            st.session_state.lesson_pool.append(slow_item)
        
        time.sleep(1.8)
        st.rerun()
else:
    if selected not in st.session_state.history:
        st.session_state.history.append(selected)
    st.balloons()
    st.success(f"🎉 HOÀN THÀNH BÀI: {selected}")
    if st.button("Học lại từ đầu"):
        st.session_state.history.remove(selected)
        del st.session_state.last_selected
        st.rerun()