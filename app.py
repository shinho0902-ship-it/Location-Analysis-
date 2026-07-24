import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
import os
from dotenv import load_dotenv

load_dotenv()

KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")

# 페이지 설정
st.set_page_config(page_title="입지분석 대시보드", layout="wide")
st.title("🏪 만만마켓 입지분석 대시보드")
st.subtitle("경기도 용인시 수지구")

# 수지구 좌표
SUJI_LAT = 37.32
SUJI_LNG = 127.05

@st.cache_data
def search_kakao_places(query, x, y, radius=2000):
    """카카오맵 로컬 API로 장소 검색"""
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}

    params = {
        "query": query,
        "x": x,
        "y": y,
        "radius": radius,
        "sort": "distance"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API 요청 실패: {e}")
        return None

def get_places_dataframe(api_response):
    """API 응답을 DataFrame으로 변환"""
    if not api_response or "documents" not in api_response:
        return pd.DataFrame()

    documents = api_response["documents"]
    data = []
    for doc in documents:
        data.append({
            "이름": doc.get("place_name", ""),
            "주소": doc.get("address_name", ""),
            "전화": doc.get("phone", "미등록"),
            "위도": float(doc.get("y", 0)),
            "경도": float(doc.get("x", 0)),
            "카테고리": doc.get("category_name", "")
        })

    return pd.DataFrame(data)

# 사이드바에서 검색 옵션
with st.sidebar:
    st.header("⚙️ 검색 범위")
    radius = st.slider("검색 반경 (m)", 500, 5000, 2000, 100)

    st.header("📊 분석 옵션")
    show_competitors = st.checkbox("경쟁사 표시", value=True)
    show_convenience = st.checkbox("편의점 표시", value=True)

# 메인 영역
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📍 지도")

    # 지도 생성
    m = folium.Map(
        location=[SUJI_LAT, SUJI_LNG],
        zoom_start=14,
        tiles="OpenStreetMap"
    )

    # 만만마켓 검색
    st.info("📍 만만마켓 매장을 검색 중입니다...")
    market_data = search_kakao_places("만만마켓", SUJI_LNG, SUJI_LAT, radius)
    market_df = get_places_dataframe(market_data)

    # 만만마켓 마커 추가
    if not market_df.empty:
        for idx, row in market_df.iterrows():
            folium.Marker(
                location=[row["위도"], row["경도"]],
                popup=row["이름"],
                icon=folium.Icon(color="red", icon="shopping-cart"),
                tooltip=row["이름"]
            ).add_to(m)

    # 경쟁사 검색 및 표시
    if show_competitors:
        st.info("🏪 경쟁사(마트/슈퍼)를 검색 중입니다...")
        market_types = ["마트", "슈퍼마켓", "편의점"]

        for market_type in market_types:
            competitor_data = search_kakao_places(market_type, SUJI_LNG, SUJI_LAT, radius)
            competitor_df = get_places_dataframe(competitor_data)

            color = "blue" if market_type == "마트" else "orange"

            if not competitor_df.empty:
                for idx, row in competitor_df.head(15).iterrows():  # 상위 15개만 표시
                    folium.CircleMarker(
                        location=[row["위도"], row["경도"]],
                        radius=4,
                        popup=f"{row['이름']}<br>{market_type}",
                        color=color,
                        fill=True,
                        fillOpacity=0.5,
                        tooltip=row["이름"]
                    ).add_to(m)

    # 지도 표시
    st_folium(m, width=700, height=500)

with col2:
    st.subheader("📈 분석 결과")

    if not market_df.empty:
        st.metric("만만마켓 매장 수", len(market_df))
        st.markdown("---")
        st.write("**매장 목록**")
        st.dataframe(
            market_df[["이름", "주소"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("⚠️ 검색 반경 내 만만마켓이 없습니다.")

# 상세 분석 탭
st.markdown("---")
tab1, tab2, tab3 = st.tabs(["만만마켓", "경쟁사 분석", "지역 정보"])

with tab1:
    if not market_df.empty:
        st.subheader("만만마켓 상세 정보")
        st.dataframe(market_df, use_container_width=True, hide_index=True)
    else:
        st.info("검색 범위 내 만만마켓이 없습니다.")

with tab2:
    st.subheader("경쟁사 분석")

    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.write("**마트/슈퍼마켓**")
        market_data = search_kakao_places("마트", SUJI_LNG, SUJI_LAT, radius)
        market_list = get_places_dataframe(market_data)
        if not market_list.empty:
            st.metric("마트 개수", len(market_list))
            st.dataframe(market_list[["이름", "주소"]].head(10), hide_index=True)
        else:
            st.info("검색 결과 없음")

    with col_c2:
        st.write("**편의점**")
        conv_data = search_kakao_places("편의점", SUJI_LNG, SUJI_LAT, radius)
        conv_list = get_places_dataframe(conv_data)
        if not conv_list.empty:
            st.metric("편의점 개수", len(conv_list))
            st.dataframe(conv_list[["이름", "주소"]].head(10), hide_index=True)
        else:
            st.info("검색 결과 없음")

with tab3:
    st.subheader("수지구 기본 정보")
    st.write("""
    **위치**: 경기도 용인시 수지구

    **좌표**:
    - 위도: 37.32°N
    - 경도: 127.05°E

    **특징**:
    - 용인시의 동쪽 지역
    - 상권 발달 지역
    - 주거 밀집 지역

    **분석 범위**: 검색 중심지 반경 2km 이내
    """)
