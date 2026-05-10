import streamlit as st
import pandas as pd
import random
import os
import time
import streamlit.components.v1 as components

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="Tagalog Pro", page_icon="🇵🇭", layout="centered")

# --- 2. CSS CHUYÊN NGHIỆP (PRO UI) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    /* Tổng thể */
    html, body, [class*="View"] {
        font-family: 'Inter', sans-serif;
        background-color: #F3F4F6 !important;
    }

    /* Khung câu hỏi (Việt) */
    .vn-card {
        background: linear-gradient(135deg, #6366F1 0%, #4338CA 100%);
        color: white;
        padding: 25px;
        border-radius: 20px;
        font-size: 22px;
        font-weight: 600;
        margin-bottom: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border-left: 8px solid #A5B4FC;
    }

    /* Vùng hiển thị kết quả đang ghép */
    .result-box {
        background-color: #eae59a;
        padding: 20px;
        border-radius: 18px;
        border: 2px solid #E5E7EB;
        min-height: 80px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 25px;
        box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.05);
    }
    .result-text {
        color: red;
        font-size: 40px;
        font-weight: 800;
        text-align: center;
        margin: 0;
    }

    /* Container cho Word Bank */
    .word-bank-container {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        justify-content: center;
    }

    /* Ép các cột Streamlit nằm ngang trên Mobile */
    [data-testid="column"] {
        flex: 1 1 auto !important;
        min-width: 0px !important;
    }

    /* Nút bấm từ vựng */
    div.stButton > button {
        width: 100% !important;
        background-color: white !important;
        color: #374151 !important;
        border: 2px solid #D1D5DB !important;
        border-radius: 14px !important;
        padding: 12px 5px !important;
        font-size: 17px !important;
        font-weight: 600 !important;
        box-shadow: 0px 4px 0px #D1D5DB !important;
        transition: all 0.1s ease;
    }
    div.stButton > button:active {
        box-shadow: none !important;
        transform: translateY(4px) !important;
    }
    div.stButton > button:hover {
        border-color: #6366F1 !important;
        color: #6366F1 !important;
    }

    /* Thanh tiến độ Pro */
    .stProgress > div > div > div > div {
        background: linear-gradient(to right, #10B981, #34D399) !important;
        border-radius: 10px;
        height: 12px !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1E1B4B !important;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
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
                book_num = f.replace('sach_Tagalog_', '').replace('.xlsx', '')
                for sheet in xl.sheet_names:
                    if any(x in sheet for x in ["Mục lục", "Sheet"]): continue
                    df = pd.read_excel(xl, sheet_name=sheet, engine='openpyxl')
                    if df.shape[1] >= 3:
                        df = df.iloc[:, [1, 2]]
                        df.columns = ['VN', 'TG']
                        df = df.dropna(subset=['TG'])
                        df['VN'] = df['VN'].ffill()
                        df['Lesson'] = f"Sách {book_num} • {sheet}"
                        all_rows.append(df)
            except: continue
    return pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()

df_main = load_data()

# --- 5. QUẢN LÝ TRẠNG THÁI ---
if 'lesson_pool' not in st.session_state: st.session_state.lesson_pool = []
if 'user_answer_indices' not in st.session_state: st.session_state.user_answer_indices = []
if 'instinct_count' not in st.session_state: st.session_state.instinct_count = 0
if 'active_q_text' not in st.session_state: st.session_state.active_q_text = ""

# --- 6. SIDEBAR ---
st.sidebar.markdown("# 🇵🇭 TAGALOG PRO")
lessons = sorted(df_main['Lesson'].unique())
selected = st.sidebar.selectbox("Lựa chọn bài học", lessons)

if 'last_selected' not in st.session_state or st.session_state.last_selected != selected:
    filtered = df_main[df_main['Lesson'] == selected].to_dict('records')
    random.shuffle(filtered)
    st.session_state.lesson_pool = filtered
    st.session_state.total_in_lesson = len(filtered)
    st.session_state.instinct_count = 0
    st.session_state.last_selected = selected
    st.session_state.active_q_text = ""

# --- 7. LOGIC CHÍNH ---
if st.session_state.lesson_pool:
    item = st.session_state.lesson_pool[0]
    
    # ID Sync
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
        speak_tagalog(item['TG']) # Đọc trước khi làm

    # UI: Header & Tiến độ
    st.write(f"### {selected}")
    st.progress(st.session_state.instinct_count / st.session_state.total_in_lesson)
    st.caption(f"Đã hoàn thành: **{st.session_state.instinct_count}/{st.session_state.total_in_lesson}**")

    # UI: Thẻ câu hỏi tiếng Việt
    st.markdown(f'<div class="vn-card">{item["VN"]}</div>', unsafe_allow_html=True)
    
    # UI: Vùng hiển thị kết quả
    current_string = " ".join([st.session_state.words_with_id[i][1] for i in st.session_state.user_answer_indices])
    st.markdown(f'<div class="result-box"><p class="result-text">{current_string if current_string else "..."}</p></div>', unsafe_allow_html=True)

    # UI: Word Bank (Nút chọn từ)
    cols = st.columns(3)
    for idx, (original_idx, word) in enumerate(st.session_state.words_with_id):
        if original_idx not in st.session_state.user_answer_indices:
            if cols[idx % 3].button(word, key=f"btn_{original_idx}"):
                st.session_state.user_answer_indices.append(original_idx)
                st.rerun()

    # UI: Điều khiển (Dưới cùng)
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
            st.session_state.instinct_count += 1
        else:
            st.warning(f"🐢 CẦN NHANH HƠN ({elapsed:.2f}s)")
            slow_item = st.session_state.lesson_pool.pop(0)
            st.session_state.lesson_pool.append(slow_item)
        
        time.sleep(2.0)
        st.rerun()
else:
    st.balloons()
    st.success("🎉 TUYỆT VỜI! BẠN ĐÃ THUẦN THỤC TOÀN BỘ BÀI HỌC NÀY.")
    if st.button("Học lại bài này", type="primary"):
        del st.session_state.last_selected
        st.rerun()