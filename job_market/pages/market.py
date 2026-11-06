"""Trang Thị trường việc làm — khám phá kỹ năng theo bộ lọc.

Mục này làm gì: lọc tin theo nguồn, vai trò, khu vực rồi xem kỹ năng nào được yêu cầu
nhiều nhất và trả lương cao nhất. Chỉ mô tả dữ liệu, không dùng mô hình.
"""

import streamlit as st

from career_market.data.rules import REGIONS, ROLE_ORDER
from career_market.ui import cache
from career_market.ui.charts import skill_table

st.title("Thị trường việc làm")
st.caption("Kỹ năng được nhắc trong tin tuyển dụng CNTT có công bố lương.")
frame = cache.dataset()

# Mục này: bộ lọc; để trống = lấy tất cả.
left, middle, right = st.columns(3)
sources = left.multiselect("Nguồn dữ liệu", sorted(frame["source"].unique()), key="market_src")
roles = middle.multiselect("Vai trò", ROLE_ORDER, key="market_roles")
regions = right.multiselect("Khu vực", REGIONS, key="market_regions")
filters = (tuple(sources), tuple(roles), tuple(regions))
view = cache.filter_postings(frame, *filters)
if view.empty:
    st.info("Không có tin nào khớp bộ lọc.")
    st.stop()

# Mục này: số liệu nhanh của phần dữ liệu đã lọc.
a, b, c = st.columns(3)
a.metric("Tin tuyển dụng", f"{len(view):,}")
b.metric("Tin có nhắc kỹ năng", f"{(view['skill_count'] > 0).sum():,}")
c.metric("Trung vị lương", f"{view['salary'].median():.1f} triệu")

# Mục này: top 20 kỹ năng theo nhu cầu và theo lương.
left, right = st.columns(2, gap="medium")
with left, st.container(border=True):
    st.subheader("Kỹ năng được yêu cầu nhiều")
    st.image(cache.market_chart("demand", *filters), width="stretch")
with right, st.container(border=True):
    st.subheader("Kỹ năng lương cao")
    st.caption("Thanh xám: dưới 10 tin · đường đứt: trung vị chung")
    st.image(cache.market_chart("salary", *filters), width="stretch")

# Mục này: bảng số liệu và tải CSV.
table = skill_table(view).sort_values("postings", ascending=False)
table = table.rename(columns={"skill": "Kỹ năng", "postings": "Số tin", "median": "Trung vị lương"})
st.dataframe(table, hide_index=True, width="stretch")
st.download_button("Tải bảng CSV", table.to_csv(index=False), "skill-demand.csv", "text/csv")
st.caption("Lương gắn với kỹ năng chỉ là tương quan, không chứng minh kỹ năng gây tăng lương.")
