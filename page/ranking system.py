import streamlit as st
import pandas as pd
import math

# 1. 초기 가상 데이터 설정 (세션 상태를 이용해 데이터 유지)
if 'ranking_df' not in st.session_state:
    # 예시 국가와 초기 점수 (2026년 기준 상위권 가상 점수)
    data = {
        '국가': ['아르헨티나', '프랑스', '스페인', '잉글랜드', '브라질', '대한민국', '일본'],
        '포인트': [1860.50, 1840.20, 1790.00, 1780.10, 1750.40, 1560.00, 1620.00]
    }
    df = pd.DataFrame(data)
    st.session_state.ranking_df = df.sort_values(by='포인트', ascending=False).reset_index(drop=True)

if 'match_history' not in st.session_state:
    st.session_state.match_history = []

# 피파 SUM 알고리즘 계산 함수
def calculate_elo(p_a, p_b, outcome, importance):
    """
    p_a: 팀 A의 기존 점수
    p_b: 팀 B의 기존 점수
    outcome: 팀 A 기준 결과 (1: 승, 0.5: 무, 0: 패)
    importance: 경기 중요도 가중치 (I)
    """
    # 경기 기대 결과 (We) 계산 공식
    dr = p_a - p_b
    we = 1 / (10 ** (-dr / 600) + 1)
    
    # 포인트 변화량 계산 (P = P_before + I * (W - We))
    delta = importance * (outcome - we)
    return round(delta, 2)

# --- UI 레이아웃 시작 ---
st.set_page_config(page_title="FIFA 실시간 랭킹 시뮬레이터", layout="wide")

st.title("⚽ FIFA 실시간 랭킹 시뮬레이터")
st.markdown("경기 결과를 입력하면 FIFA SUM 알고리즘에 의해 국가별 포인트와 랭킹이 실시간으로 업데이트됩니다.")

# 화면을 두 열로 분할 (좌측: 랭킹 표, 우측: 경기 입력 및 기록)
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🏆 현재 피파 랭킹 순위표")
    
    # 랭킹 재정렬 및 순위 부여
    df_current = st.session_state.ranking_df.sort_values(by='포인트', ascending=False).reset_index(drop=True)
    df_current.index = df_current.index + 1
    df_current.index.name = '순위'
    
    st.dataframe(df_current, use_container_width=True)

with col2:
    st.subheader("📝 새 경기 결과 입력")
    
    countries = st.session_state.ranking_df['국가'].tolist()
    
    # 입력 폼
    with st.form(key='match_form', clear_on_submit=True):
        team_a = st.selectbox("홈 팀 (팀 A)", countries, index=0)
        team_b = st.selectbox("원정 팀 (팀 B)", countries, index=1)
        
        result = st.radio("경기 결과 (팀 A 기준)", ["팀 A 승리", "무승부", "팀 B 승리"])
        
        importance = st.selectbox(
            "경기 중요도 (I 가중치)",
            options=[10, 25, 50, 60],
            format_func=lambda x: {
                10: "친선 경기 (I=10)",
                25: "월드컵/대륙컵 예선 (I=25)",
                50: "월드컵 본선 8강 이전 (I=50)",
                60: "월드컵 본선 8강 이후 (I=60)"
            }[x]
        )
        
        submit_button = st.form_submit_button(label="경기 결과 반영하기")

    if submit_button:
        if team_a == team_b:
            st.error("🚨 홈 팀과 원정 팀은 서로 다른 국가여야 합니다!")
        else:
            # 기존 점수 가져오기
            p_a = st.session_state.ranking_df.loc[st.session_state.ranking_df['국가'] == team_a, '포인트'].values[0]
            p_b = st.session_state.ranking_df.loc[st.session_state.ranking_df['국가'] == team_b, '포인트'].values[0]
            
            # 결과값 매핑
            if result == "팀 A 승리":
                outcome_a, outcome_b = 1, 0
            elif result == "무승부":
                outcome_a, outcome_b = 0.5, 0.5
            else:
                outcome_a, outcome_b = 0, 1
                
            # Elo 점수 변동 계산
            delta_a = calculate_elo(p_a, p_b, outcome_a, importance)
            delta_b = calculate_elo(p_b, p_a, outcome_b, importance)
            
            # 세션 상태 데이터 업데이트
            st.session_state.ranking_df.loc[st.session_state.ranking_df['국가'] == team_a, '포인트'] += delta_a
            st.session_state.ranking_df.loc[st.session_state.ranking_df['국가'] == team_b, '포인트'] += delta_b
            
            # 경기 기록 저장
            res_str = "승리" if result == "팀 A 승리" else ("무승부" if result == "무승부" else "패배")
            st.session_state.match_history.append(
                f"⚽ {team_a} vs {team_b} ({res_str}) | 변동: {team_a}({delta_a:+.2f}), {team_b}({delta_b:+.2f})"
            )
            
            st.success(f"✅ 경기 결과가 반영되었습니다! ({team_a} {delta_a:+.2f} / {team_b} {delta_b:+.2f})")
            st.rerun() # 화면 즉시 새로고침

    # 경기 기록 출력
    if st.session_state.match_history:
        st.subheader("📜 최근 경기 입력 기록")
        for history in reversed(st.session_state.match_history[-5:]): # 최근 5개만 표시
            st.write(history)
