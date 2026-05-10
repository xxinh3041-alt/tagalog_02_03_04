import streamlit as st
import pandas as pd
import random
import os
import time

# Cấu hình trang tối ưu cho thiết bị di động
st.set_page_config(
    page_title="Tagalog Master", 
    page_icon="🇵🇭", 
    layout="centered", # Giữ nội dung tập trung để dễ nhìn trên điện thoại
    initial_sidebar_state="collapsed"
)

# Thêm CSS để các nút bấm trông đẹp và to hơn trên cảm ứng
st.markdown("""
    <style>
    div.stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #f0f2f6;
        font-weight: bold;
        border: 1px solid #d1d5db;
    }
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. HÀM LOAD DỮ LIỆU ---
@st.cache_data
def load_data():
    file_list = ["sach_Tagalog_02.xlsx", "sach_Tagalog_03.xlsx", "sach_Tagalog_04.xlsx"]
    full_data = []
    for file_path in file_list:
        if os.path.exists(file_path):
            try:
                excel_file = pd.ExcelFile(file_path)
                book_label = file_path.replace('sach_', '').replace('.xlsx', '').upper()
                for name in excel_file.sheet_names:
                    if "Mục lục" in name or "Sheet" in name: continue
                    df = pd.read_excel(file_path, sheet_name=name, engine='openpyxl')
                    if df.shape[1] >= 3:
                        df = df.iloc[:, [1, 2]]
                        df.columns = ['VN', 'TG']
                        df = df.dropna(subset=['TG'])
                        df['VN'] = df['VN'].ffill()
                        df['Lesson'] = f"{book_label} - {name}"
                        full_data.append(df)
            except: continue
    return pd.concat(full_data, ignore_index=True) if full_data else pd.DataFrame()

df_all = load_data()

# --- 2. QUẢN LÝ TRẠNG THÁI (SESSION STATE) ---
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'user_answer' not in st.session_state:
    st.session_state.user_answer = []
if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()
if 'lesson_pool' not in st.session_state:
    st.session_state.lesson_pool = []

# --- 3. SIDEBAR CHỌN BÀI ---
st.sidebar.title("🇵🇭 Cài đặt")
all_lessons = sorted(df_all['Lesson'].unique())
selected_lesson = st.sidebar.selectbox("Chọn bài học", all_lessons)

# Nếu đổi bài học thì reset tiến độ
if 'last_lesson' not in st.session_state or st.session_state.last_lesson != selected_lesson:
    st.session_state.lesson_pool = df_all[df_all['Lesson'] == selected_lesson].to_dict('records')
    random.shuffle(st.session_state.lesson_pool) # Trộn câu hỏi
    st.session_state.current_idx = 0
    st.session_state.score = 0
    st.session_state.last_lesson = selected_lesson
    st.session_state.user_answer = []
    st.session_state.start_time = time.time()

# --- 4. LOGIC CÂU HỎI ---
pool = st.session_state.lesson_pool
total_q = len(pool)

if st.session_state.current_idx < total_q:
    current_item = pool[st.session_state.current_idx]
    
    # Hiển thị Thanh tiến độ
    progress = (st.session_state.current_idx) / total_q
    st.progress(progress)
    st.write(f"Câu {st.session_state.current_idx + 1} / {total_q} | Đúng: {st.session_state.score}")

    # Giao diện chính
    st.info(f"Dịch sang Tagalog:\n ### {current_item['VN']}")
    
    # Hiển thị câu đang ghép
    answer_str = " ".join(st.session_state.user_answer)
    st.subheader(f"👉 {answer_str if answer_str else '...'}")

    # Tạo Word Bank (Nút bấm to)
    if 'words' not in st.session_state or st.session_state.new_q:
        clean_tg = str(current_item['TG']).replace('!', '').replace('?', '').replace('.', '').replace(',', '').replace('"', '')
        words = clean_tg.split()
        # Thêm từ bẫy
        distractors = random.sample(" ".join(df_all['TG'].astype(str)).split(), 3)
        word_pool = list(set(words + distractors))
        random.shuffle(word_pool)
        st.session_state.words = word_pool
        st.session_state.new_q = False

    # Hiển thị các nút (3 cột trên mobile để nút đủ to)
    cols = st.columns(3)
    for i, word in enumerate(st.session_state.words):
        if cols[i % 3].button(word, key=f"w_{i}"):
            st.session_state.user_answer.append(word)
            st.rerun()

    # Nút chức năng
    st.write("---")
    c1, c2 = st.columns(2)
    if c1.button("⬅️ Xóa từ cuối"):
        if st.session_state.user_answer: 
            st.session_state.user_answer.pop()
            st.rerun()
    if c2.button("🔄 Làm lại câu này"):
        st.session_state.user_answer = []
        st.rerun()

    # TỰ ĐỘNG KIỂM TRA: Nếu số lượng từ ghép bằng số lượng từ của đáp án (hoặc hơn)
    clean_target = str(current_item['TG']).lower().replace('!', '').replace('?', '').replace('.', '').replace(',', '').replace('"', '').strip()
    if " ".join(st.session_state.user_answer).lower().strip() == clean_target:
        st.balloons()
        st.success(f"Đúng rồi! +1 điểm")
        time.sleep(1.5) # Đợi 1.5 giây để bạn kịp nhìn đáp án
        st.session_state.score += 1
        st.session_state.current_idx += 1
        st.session_state.user_answer = []
        st.session_state.new_q = True
        st.rerun()

else:
    st.balloons()
    st.success(f"🎉 Chúc mừng! Bạn đã hoàn thành bài học.")
    st.write(f"Kết quả: {st.session_state.score}/{total_q}")
    if st.button("Học lại bài này"):
        st.session_state.current_idx = 0
        st.session_state.score = 0
        random.shuffle(st.session_state.lesson_pool)
        st.rerun()