import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import os
from datetime import datetime

st.set_page_config(
    page_title="لوحة مؤشرات إدارة البيانات",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

RTL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Cairo', sans-serif;
    direction: rtl;
    text-align: right;
}
.stApp { direction: rtl; }
.stSidebar { direction: rtl; text-align: right; }
h1, h2, h3, h4 { text-align: center; }
.metric-card {
    background: linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 100%);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    color: white;
    margin: 5px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}
.metric-value {
    font-size: 2.5rem;
    font-weight: 700;
    color: #f0c040;
}
.metric-label {
    font-size: 0.9rem;
    opacity: 0.9;
    margin-top: 5px;
}
.domain-header {
    background: linear-gradient(90deg, #1e3a5f, #2d6a9f);
    color: white;
    padding: 15px 25px;
    border-radius: 10px;
    text-align: center;
    font-size: 1.4rem;
    font-weight: 700;
    margin-bottom: 20px;
}
.status-green { color: #28a745; font-weight: bold; }
.status-yellow { color: #ffc107; font-weight: bold; }
.status-red { color: #dc3545; font-weight: bold; }
.stNumberInput input { text-align: center; direction: ltr; }
.stTextInput input { direction: rtl; text-align: right; }
</style>
"""
st.markdown(RTL_CSS, unsafe_allow_html=True)

DATA_FILE = "kpi_data.json"

DOMAINS = {
    "حوكمة البيانات": {
        "icon": "🏛️",
        "color": "#1e3a5f",
        "kpis": [
            {"id": "dg_policy_coverage", "name": "نسبة تغطية سياسات البيانات", "unit": "%", "target": 100, "description": "نسبة السياسات المعتمدة من إجمالي السياسات المطلوبة"},
            {"id": "dg_stewardship", "name": "نسبة تعيين أمناء البيانات", "unit": "%", "target": 100, "description": "نسبة الأصول البيانية المعيّن لها أمين بيانات"},
            {"id": "dg_compliance", "name": "نسبة الامتثال للوائح", "unit": "%", "target": 95, "description": "نسبة الامتثال للوائح والأنظمة المعمول بها"},
            {"id": "dg_issues_resolved", "name": "نسبة حل مشكلات الحوكمة", "unit": "%", "target": 90, "description": "نسبة مشكلات الحوكمة المحلولة خلال المهلة المحددة"},
            {"id": "dg_training", "name": "نسبة تدريب الكوادر على الحوكمة", "unit": "%", "target": 80, "description": "نسبة الموظفين المدرّبين على سياسات إدارة البيانات"},
        ]
    },
    "جودة البيانات": {
        "icon": "✅",
        "color": "#155724",
        "kpis": [
            {"id": "dq_completeness", "name": "اكتمال البيانات", "unit": "%", "target": 95, "description": "نسبة الحقول المكتملة من إجمالي الحقول المطلوبة"},
            {"id": "dq_accuracy", "name": "دقة البيانات", "unit": "%", "target": 98, "description": "نسبة السجلات الدقيقة مقارنة بمصدر الحقيقة"},
            {"id": "dq_consistency", "name": "اتساق البيانات", "unit": "%", "target": 95, "description": "نسبة البيانات المتسقة عبر الأنظمة المختلفة"},
            {"id": "dq_timeliness", "name": "حداثة البيانات", "unit": "%", "target": 90, "description": "نسبة البيانات المحدّثة ضمن الفترة الزمنية المعيارية"},
            {"id": "dq_uniqueness", "name": "تفرد البيانات (عدم التكرار)", "unit": "%", "target": 99, "description": "نسبة السجلات الفريدة من إجمالي السجلات"},
        ]
    },
    "هندسة البيانات": {
        "icon": "🏗️",
        "color": "#856404",
        "kpis": [
            {"id": "da_catalog_coverage", "name": "تغطية كتالوج البيانات", "unit": "%", "target": 90, "description": "نسبة الأصول البيانية الموثقة في الكتالوج"},
            {"id": "da_integration", "name": "نسبة تكامل المصادر البيانية", "unit": "%", "target": 85, "description": "نسبة مصادر البيانات المتكاملة مع المنصة المركزية"},
            {"id": "da_model_compliance", "name": "الامتثال لنماذج البيانات المعيارية", "unit": "%", "target": 90, "description": "نسبة الأنظمة الملتزمة بنماذج البيانات القياسية"},
            {"id": "da_pipeline_availability", "name": "توافر خطوط معالجة البيانات", "unit": "%", "target": 99, "description": "نسبة توافر خطوط تدفق البيانات (Data Pipelines)"},
            {"id": "da_metadata", "name": "اكتمال البيانات الوصفية", "unit": "%", "target": 85, "description": "نسبة الأصول البيانية ذات البيانات الوصفية المكتملة"},
        ]
    },
    "أمن البيانات وخصوصيتها": {
        "icon": "🔐",
        "color": "#721c24",
        "kpis": [
            {"id": "ds_classification", "name": "نسبة تصنيف البيانات", "unit": "%", "target": 100, "description": "نسبة البيانات المصنّفة وفق سياسة التصنيف المعتمدة"},
            {"id": "ds_access_review", "name": "مراجعة صلاحيات الوصول", "unit": "%", "target": 100, "description": "نسبة الصلاحيات التي خضعت للمراجعة الدورية"},
            {"id": "ds_incidents_resolved", "name": "نسبة حل حوادث أمن البيانات", "unit": "%", "target": 95, "description": "نسبة حوادث اختراق البيانات المعالجة في الوقت المحدد"},
            {"id": "ds_masking", "name": "تطبيق إخفاء هوية البيانات", "unit": "%", "target": 100, "description": "نسبة البيانات الحساسة الخاضعة لإجراءات الإخفاء"},
            {"id": "ds_privacy_compliance", "name": "الامتثال لأنظمة حماية البيانات الشخصية", "unit": "%", "target": 100, "description": "نسبة الامتثال لنظام حماية البيانات الشخصية"},
        ]
    },
    "إدارة البيانات الرئيسية والمرجعية": {
        "icon": "📋",
        "color": "#4a235a",
        "kpis": [
            {"id": "md_golden_records", "name": "نسبة اكتمال السجلات الذهبية", "unit": "%", "target": 95, "description": "نسبة الكيانات الرئيسية ذات سجل ذهبي موحّد ومكتمل"},
            {"id": "md_deduplication", "name": "معدل إزالة التكرار", "unit": "%", "target": 99, "description": "نسبة السجلات المكررة التي تم دمجها أو حذفها"},
            {"id": "md_ref_coverage", "name": "تغطية قوائم البيانات المرجعية", "unit": "%", "target": 100, "description": "نسبة القوائم المرجعية المكتملة والمعتمدة"},
            {"id": "md_synchronization", "name": "نسبة مزامنة البيانات الرئيسية", "unit": "%", "target": 98, "description": "نسبة الأنظمة المتزامنة مع مستودع البيانات الرئيسية"},
            {"id": "md_adoption", "name": "معدل اعتماد مستودع البيانات الرئيسية", "unit": "%", "target": 85, "description": "نسبة الأنظمة التي تستخدم مستودع البيانات الرئيسية كمصدر وحيد للحقيقة"},
        ]
    },
    "إدارة دورة حياة البيانات": {
        "icon": "🔄",
        "color": "#0c3547",
        "kpis": [
            {"id": "dl_retention_compliance", "name": "الامتثال لسياسات الاحتفاظ بالبيانات", "unit": "%", "target": 95, "description": "نسبة البيانات الخاضعة لجداول الاحتفاظ المعتمدة"},
            {"id": "dl_archiving", "name": "نسبة أرشفة البيانات في الوقت المحدد", "unit": "%", "target": 90, "description": "نسبة البيانات المؤرشفة وفق الجدول الزمني المقرر"},
            {"id": "dl_disposal", "name": "نسبة إتلاف البيانات وفق السياسة", "unit": "%", "target": 100, "description": "نسبة البيانات التي تم إتلافها بشكل آمن وموثق"},
            {"id": "dl_lineage", "name": "توثيق سلسلة البيانات (Data Lineage)", "unit": "%", "target": 80, "description": "نسبة الأصول البيانية ذات سلسلة بيانات موثقة"},
            {"id": "dl_backup", "name": "نجاح عمليات النسخ الاحتياطي", "unit": "%", "target": 100, "description": "نسبة عمليات النسخ الاحتياطي الناجحة"},
        ]
    },
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_status(value, target):
    ratio = value / target if target > 0 else 0
    if ratio >= 0.9:
        return "مرتفع", "#28a745", "🟢"
    elif ratio >= 0.7:
        return "متوسط", "#ffc107", "🟡"
    else:
        return "منخفض", "#dc3545", "🔴"

def render_gauge(value, target, title, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        delta={"reference": target, "valueformat": ".1f", "suffix": "%"},
        title={"text": title, "font": {"size": 13, "family": "Cairo"}},
        number={"suffix": "%", "font": {"size": 22}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": color},
            "bgcolor": "white",
            "steps": [
                {"range": [0, 70], "color": "#ffe0e0"},
                {"range": [70, 90], "color": "#fff3cd"},
                {"range": [90, 100], "color": "#d4edda"},
            ],
            "threshold": {
                "line": {"color": "black", "width": 3},
                "thickness": 0.75,
                "value": target,
            },
        },
    ))
    fig.update_layout(
        height=200,
        margin=dict(l=10, r=10, t=40, b=10),
        font={"family": "Cairo"},
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig

def render_domain_radar(domain_name, domain_data, kpi_data):
    kpis = domain_data["kpis"]
    names = [k["name"][:20] for k in kpis]
    values = [kpi_data.get(k["id"], 0) for k in kpis]
    targets = [k["target"] for k in kpis]
    pct = [min(v / t * 100, 100) if t > 0 else 0 for v, t in zip(values, targets)]
    names_closed = names + [names[0]]
    pct_closed = pct + [pct[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[100] * (len(names) + 1),
        theta=names_closed,
        fill="toself",
        fillcolor="rgba(200,200,200,0.1)",
        line=dict(color="rgba(150,150,150,0.4)", dash="dot"),
        name="الهدف",
        showlegend=True,
    ))
    fig.add_trace(go.Scatterpolar(
        r=pct_closed,
        theta=names_closed,
        fill="toself",
        fillcolor=f"rgba({int(domain_data['color'][1:3],16)},{int(domain_data['color'][3:5],16)},{int(domain_data['color'][5:7],16)},0.3)",
        line=dict(color=domain_data["color"], width=2),
        name="الأداء الفعلي",
        showlegend=True,
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        font={"family": "Cairo"},
        height=350,
        margin=dict(l=40, r=40, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(font=dict(family="Cairo")),
    )
    return fig

def render_overview_bar(kpi_data):
    rows = []
    for domain_name, domain_data in DOMAINS.items():
        scores = []
        for kpi in domain_data["kpis"]:
            v = kpi_data.get(kpi["id"], 0)
            t = kpi["target"]
            scores.append(min(v / t * 100, 100) if t > 0 else 0)
        avg = sum(scores) / len(scores) if scores else 0
        rows.append({"الدومين": f"{domain_data['icon']} {domain_name}", "متوسط الأداء": round(avg, 1)})
    df = pd.DataFrame(rows)
    colors = ["#28a745" if v >= 90 else "#ffc107" if v >= 70 else "#dc3545" for v in df["متوسط الأداء"]]
    fig = go.Figure(go.Bar(
        x=df["متوسط الأداء"],
        y=df["الدومين"],
        orientation="h",
        marker_color=colors,
        text=[f"{v}%" for v in df["متوسط الأداء"]],
        textposition="outside",
        textfont=dict(family="Cairo", size=13),
    ))
    fig.update_layout(
        xaxis=dict(range=[0, 110], title="نسبة الأداء %"),
        yaxis=dict(autorange="reversed"),
        font={"family": "Cairo"},
        height=350,
        margin=dict(l=10, r=60, t=20, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.add_vline(x=90, line_dash="dash", line_color="#28a745", annotation_text="الهدف 90%")
    return fig


# ─── Load persisted data ───
kpi_data = load_data()

# ─── Sidebar ───
with st.sidebar:
    st.markdown("<h2 style='text-align:center;'>📊 لوحة مؤشرات<br>إدارة البيانات</h2>", unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio(
        "التنقل",
        ["🏠 نظرة عامة", "📥 إدخال البيانات"] + [f"{v['icon']} {k}" for k, v in DOMAINS.items()],
        label_visibility="collapsed",
    )
    st.markdown("---")
    period = st.selectbox("الفترة الزمنية", ["الربع الأول 2025", "الربع الثاني 2025", "الربع الثالث 2025", "الربع الرابع 2025", "2025 كامل"])
    st.markdown(f"<small style='opacity:0.6'>آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}</small>", unsafe_allow_html=True)

# ═══════════════════════════════════════════
# PAGE: OVERVIEW
# ═══════════════════════════════════════════
if page == "🏠 نظرة عامة":
    st.markdown("<h1>🏠 نظرة عامة — مؤشرات إدارة البيانات</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center;opacity:0.7'>الفترة: {period}</p>", unsafe_allow_html=True)

    # Overall score
    all_scores = []
    for domain_name, domain_data in DOMAINS.items():
        for kpi in domain_data["kpis"]:
            v = kpi_data.get(kpi["id"], 0)
            t = kpi["target"]
            all_scores.append(min(v / t * 100, 100) if t > 0 else 0)
    overall = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0
    status_label, status_color, status_icon = get_status(overall, 90)

    col1, col2, col3, col4 = st.columns(4)
    kpis_filled = sum(1 for kpi_id, v in kpi_data.items() if v > 0)
    total_kpis = sum(len(d["kpis"]) for d in DOMAINS.values())

    with col1:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-value'>{overall}%</div>
            <div class='metric-label'>الأداء الإجمالي</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        green_domains = sum(
            1 for d in DOMAINS.values()
            if (lambda sc: sum(sc)/len(sc) >= 90)([min(kpi_data.get(k["id"],0)/k["target"]*100,100) for k in d["kpis"]])
        )
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-value'>{green_domains}/{len(DOMAINS)}</div>
            <div class='metric-label'>دومينات تحقق الهدف</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-value'>{kpis_filled}/{total_kpis}</div>
            <div class='metric-label'>مؤشرات مُدخلة</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class='metric-card' style='background:linear-gradient(135deg,{status_color}88,{status_color});'>
            <div class='metric-value'>{status_icon}</div>
            <div class='metric-label'>{status_label}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown("#### أداء الدومينات")
        st.plotly_chart(render_overview_bar(kpi_data), use_container_width=True)
    with c2:
        st.markdown("#### حالة المؤشرات")
        greens = sum(1 for d in DOMAINS.values() for k in d["kpis"] if get_status(kpi_data.get(k["id"],0), k["target"])[0] == "مرتفع")
        yellows = sum(1 for d in DOMAINS.values() for k in d["kpis"] if get_status(kpi_data.get(k["id"],0), k["target"])[0] == "متوسط")
        reds = sum(1 for d in DOMAINS.values() for k in d["kpis"] if get_status(kpi_data.get(k["id"],0), k["target"])[0] == "منخفض")
        fig_pie = go.Figure(go.Pie(
            labels=["مرتفع 🟢", "متوسط 🟡", "منخفض 🔴"],
            values=[greens, yellows, reds],
            marker_colors=["#28a745", "#ffc107", "#dc3545"],
            hole=0.5,
            textfont=dict(family="Cairo"),
        ))
        fig_pie.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10), font={"family":"Cairo"}, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")
    st.markdown("#### ملخص الدومينات")
    summary_rows = []
    for domain_name, domain_data in DOMAINS.items():
        scores = [min(kpi_data.get(k["id"],0)/k["target"]*100,100) if k["target"]>0 else 0 for k in domain_data["kpis"]]
        avg = round(sum(scores)/len(scores),1) if scores else 0
        s_label, s_color, s_icon = get_status(avg, 90)
        summary_rows.append({
            "الدومين": f"{domain_data['icon']} {domain_name}",
            "متوسط الأداء": f"{avg}%",
            "الحالة": f"{s_icon} {s_label}",
        })
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════
# PAGE: DATA ENTRY
# ═══════════════════════════════════════════
elif page == "📥 إدخال البيانات":
    st.markdown("<h1>📥 إدخال بيانات المؤشرات</h1>", unsafe_allow_html=True)
    st.info("أدخل القيمة الفعلية لكل مؤشر ثم اضغط **حفظ البيانات**")

    updated = dict(kpi_data)
    tabs = st.tabs([f"{v['icon']} {k}" for k, v in DOMAINS.items()])

    for tab, (domain_name, domain_data) in zip(tabs, DOMAINS.items()):
        with tab:
            st.markdown(f"<div class='domain-header'>{domain_data['icon']} {domain_name}</div>", unsafe_allow_html=True)
            cols = st.columns(2)
            for i, kpi in enumerate(domain_data["kpis"]):
                with cols[i % 2]:
                    with st.container(border=True):
                        st.markdown(f"**{kpi['name']}**")
                        st.caption(kpi["description"])
                        current = kpi_data.get(kpi["id"], 0.0)
                        val = st.number_input(
                            f"القيمة الفعلية ({kpi['unit']})",
                            min_value=0.0, max_value=100.0,
                            value=float(current),
                            step=0.1,
                            key=f"input_{kpi['id']}",
                            label_visibility="visible",
                        )
                        updated[kpi["id"]] = val
                        s_label, s_color, s_icon = get_status(val, kpi["target"])
                        st.markdown(f"الهدف: **{kpi['target']}%** | الحالة: <span style='color:{s_color}'>{s_icon} {s_label}</span>", unsafe_allow_html=True)

    if st.button("💾 حفظ البيانات", type="primary", use_container_width=True):
        save_data(updated)
        kpi_data = updated
        st.success("✅ تم حفظ البيانات بنجاح!")
        st.rerun()


# ═══════════════════════════════════════════
# PAGE: DOMAIN DASHBOARD
# ═══════════════════════════════════════════
else:
    domain_name = page.split(" ", 1)[1] if " " in page else page
    if domain_name in DOMAINS:
        domain_data = DOMAINS[domain_name]
        st.markdown(f"<div class='domain-header'>{domain_data['icon']} {domain_name}</div>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center;opacity:0.7'>الفترة: {period}</p>", unsafe_allow_html=True)

        scores = [min(kpi_data.get(k["id"],0)/k["target"]*100,100) if k["target"]>0 else 0 for k in domain_data["kpis"]]
        avg = round(sum(scores)/len(scores),1) if scores else 0
        s_label, s_color, s_icon = get_status(avg, 90)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""<div class='metric-card'>
                <div class='metric-value'>{avg}%</div>
                <div class='metric-label'>متوسط أداء الدومين</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            above = sum(1 for s in scores if s >= 90)
            st.markdown(f"""<div class='metric-card'>
                <div class='metric-value'>{above}/{len(scores)}</div>
                <div class='metric-label'>مؤشرات تحقق الهدف</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class='metric-card' style='background:linear-gradient(135deg,{s_color}88,{s_color});'>
                <div class='metric-value'>{s_icon}</div>
                <div class='metric-label'>{s_label}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_radar, col_bar = st.columns([1, 1])
        with col_radar:
            st.markdown("#### مخطط الرادار")
            st.plotly_chart(render_domain_radar(domain_name, domain_data, kpi_data), use_container_width=True)
        with col_bar:
            st.markdown("#### الأداء مقابل الهدف")
            kpi_names = [k["name"] for k in domain_data["kpis"]]
            kpi_vals = [kpi_data.get(k["id"], 0) for k in domain_data["kpis"]]
            kpi_targets = [k["target"] for k in domain_data["kpis"]]
            bar_fig = go.Figure()
            bar_fig.add_trace(go.Bar(name="الهدف", x=kpi_names, y=kpi_targets,
                                     marker_color="rgba(150,150,150,0.4)",
                                     text=kpi_targets, textposition="outside",
                                     textfont=dict(family="Cairo")))
            bar_colors = [get_status(v, t)[1] for v, t in zip(kpi_vals, kpi_targets)]
            bar_fig.add_trace(go.Bar(name="الأداء الفعلي", x=kpi_names, y=kpi_vals,
                                     marker_color=bar_colors,
                                     text=kpi_vals, textposition="outside",
                                     textfont=dict(family="Cairo")))
            bar_fig.update_layout(
                barmode="group", font={"family":"Cairo"},
                height=350, margin=dict(l=10,r=10,t=20,b=80),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(tickangle=-30),
                legend=dict(font=dict(family="Cairo")),
                yaxis=dict(range=[0, 115], title="%"),
            )
            st.plotly_chart(bar_fig, use_container_width=True)

        st.markdown("---")
        st.markdown("#### تفاصيل المؤشرات")
        gauge_cols = st.columns(len(domain_data["kpis"]))
        for col, kpi in zip(gauge_cols, domain_data["kpis"]):
            with col:
                v = kpi_data.get(kpi["id"], 0)
                st.plotly_chart(
                    render_gauge(v, kpi["target"], kpi["name"], domain_data["color"]),
                    use_container_width=True,
                )

        st.markdown("#### جدول المؤشرات التفصيلي")
        table_rows = []
        for kpi in domain_data["kpis"]:
            v = kpi_data.get(kpi["id"], 0)
            t = kpi["target"]
            s_l, s_c, s_i = get_status(v, t)
            gap = round(t - v, 1)
            table_rows.append({
                "المؤشر": kpi["name"],
                "القيمة الفعلية": f"{v}%",
                "الهدف": f"{t}%",
                "الفجوة": f"{gap}%",
                "الحالة": f"{s_i} {s_l}",
                "الوصف": kpi["description"],
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
