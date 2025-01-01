import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import json
import traceback

# PostgreSQL 연결 설정
DB_URL = "postgresql://postgres:postgres@db:5432/postgres"
engine = create_engine(DB_URL)

# 데이터 로드 함수
def load_pending_data():
    try:
        query = """
            SELECT queue_id, file_id, processed_data, status
            FROM processed_data_queue
            WHERE status = 'pending_for_review';
        """
        with engine.connect() as connection:
            return pd.read_sql(query, connection)
    except Exception as e:
        st.error("데이터를 불러오는 중 오류가 발생했습니다.")
        st.error(f"오류 메시지: {e}")
        st.text("Stack Trace:")
        st.text(traceback.format_exc())
        return pd.DataFrame()

def load_comparison_data():
    try:
        query = """
            SELECT id, input_data, current_model_output, new_model_output, status
            FROM model_comparison_queue
            WHERE status = 'pending_for_review';
        """
        with engine.connect() as connection:
            return pd.read_sql(query, connection)
    except Exception as e:
        st.error("비교 데이터를 불러오는 중 오류가 발생했습니다.")
        st.error(f"오류 메시지: {e}")
        st.text("Stack Trace:")
        st.text(traceback.format_exc())
        return pd.DataFrame()

# 데이터 상태 업데이트 함수
def update_data_status(queue_id, status, reviewed_data=None):
    query = text("""
        UPDATE processed_data_queue
        SET status = :status, reviewed_data = :reviewed_data, updated_at = NOW()
        WHERE queue_id = :queue_id
    """)
    try:
        reviewed_data = json.dumps(reviewed_data) if isinstance(reviewed_data, (dict, list)) else reviewed_data
        with engine.connect() as connection:
            connection.execute(query, {
                'status': status,
                'reviewed_data': reviewed_data,
                'queue_id': queue_id
            })
        st.success(f"Queue ID {queue_id} 상태 업데이트 성공!")
    except Exception as e:
        st.error("상태를 업데이트하는 중 오류가 발생했습니다.")
        st.error(f"오류 메시지: {e}")
        st.text("Stack Trace:")
        st.text(traceback.format_exc())

def update_comparison_status(record_id, feedback, approved_model):
    query = text("""
        UPDATE model_comparison_queue
        SET status = :status, user_feedback = :feedback, updated_at = NOW()
        WHERE id = :record_id
    """)
    try:
        status = 'approved_new' if approved_model == 'new' else 'approved_current'
        with engine.connect() as connection:
            connection.execute(query, {
                'status': status,
                'feedback': feedback,
                'record_id': record_id
            })
        st.success(f"Comparison ID {record_id} 상태 업데이트 성공!")
    except Exception as e:
        st.error("비교 데이터 상태 업데이트 중 오류가 발생했습니다.")
        st.error(f"오류 메시지: {e}")
        st.text("Stack Trace:")
        st.text(traceback.format_exc())

# Streamlit UI 구성
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Select Page", ["Approval UI", "Comparison UI"])

# Approval UI
if page == "Approval UI":
    st.title("Approval UI")
    st.markdown("### 데이터 검토 및 승인/거부")
    try:
        pending_data = load_pending_data()
        if not pending_data.empty:
            for _, row in pending_data.iterrows():
                st.subheader(f"File ID: {row['file_id']} (Queue ID: {row['queue_id']})")
                try:
                    processed_data = json.loads(row['processed_data']) if isinstance(row['processed_data'], str) else row['processed_data']
                    st.json(processed_data)
                except Exception as e:
                    st.error(f"JSON 데이터를 표시하는 중 오류 발생: {e}")
                    st.text(traceback.format_exc())

                reviewed_data = st.text_area(
                    "수정된 데이터 입력 (필요 시)",
                    value=json.dumps(processed_data, indent=2),
                    key=f"review_{row['queue_id']}"
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("승인", key=f"approve_{row['queue_id']}"):
                        update_data_status(row['queue_id'], "approved", json.loads(reviewed_data))
                with col2:
                    if st.button("거부", key=f"reject_{row['queue_id']}"):
                        update_data_status(row['queue_id'], "rejected", None)
        else:
            st.info("현재 검토 대기 중인 데이터가 없습니다.")
    except Exception as e:
        st.error("Approval UI 로드 중 오류가 발생했습니다.")
        st.text(traceback.format_exc())

# Comparison UI
elif page == "Comparison UI":
    st.title("Comparison UI")
    st.markdown("### 모델 비교 및 평가")
    try:
        comparison_data = load_comparison_data()
        if not comparison_data.empty:
            for _, row in comparison_data.iterrows():
                st.subheader(f"Comparison ID: {row['id']}")
                try:
                    input_data = json.loads(row['input_data']) if isinstance(row['input_data'], str) else row['input_data']
                    current_output = json.loads(row['current_model_output']) if isinstance(row['current_model_output'], str) else row['current_model_output']
                    new_output = json.loads(row['new_model_output']) if isinstance(row['new_model_output'], str) else row['new_model_output']

                    st.text("Input Data:")
                    st.json(input_data)
                    st.text("Current Model Output:")
                    st.json(current_output)
                    st.text("New Model Output:")
                    st.json(new_output)
                except Exception as e:
                    st.error(f"데이터 로드 중 오류 발생: {e}")
                    st.text(traceback.format_exc())

                feedback = st.text_area("Feedback (Optional):", key=f"feedback_{row['id']}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Approve New Model", key=f"approve_new_{row['id']}"):
                        update_comparison_status(row['id'], feedback, "new")
                with col2:
                    if st.button("Keep Current Model", key=f"approve_current_{row['id']}"):
                        update_comparison_status(row['id'], feedback, "current")
        else:
            st.info("현재 비교 대기 중인 데이터가 없습니다.")
    except Exception as e:
        st.error("Comparison UI 로드 중 오류가 발생했습니다.")
        st.text(traceback.format_exc())
