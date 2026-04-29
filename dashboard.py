import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ── Konfigurasi halaman ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kualitas Udara Changping",
    page_icon="💨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Font & background */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .block-container { padding-top: 2rem; }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #0f3460;
        border-radius: 16px;
        padding: 1.2rem 1.4rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .metric-card .label {
        font-size: 0.78rem;
        color: #a0aec0;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.3rem;
    }
    .metric-card .value {
        font-size: 2rem;
        font-weight: 700;
        color: #e2e8f0;
        line-height: 1;
    }
    .metric-card .sub {
        font-size: 0.72rem;
        color: #718096;
        margin-top: 0.25rem;
    }

    /* AQI badge */
    .aqi-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 2px;
    }

    /* Section header */
    .section-header {
        border-left: 4px solid #4299e1;
        padding-left: 12px;
        margin-bottom: 1rem;
    }

    /* Insight box */
    .insight-box {
        background: rgba(66,153,225,0.08);
        border: 1px solid rgba(66,153,225,0.25);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-top: 0.8rem;
        font-size: 0.88rem;
        line-height: 1.7;
        color: #cbd5e0;
    }
    .insight-box b { color: #90cdf4; }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── Load & proses data ─────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("PRSA_Data_Changping_20130301-20170228.csv")
    cols_num = ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3', 'WSPM', 'RAIN', 'TEMP', 'PRES', 'DEWP']
    for col in cols_num:
        df[col] = df[col].fillna(df[col].median())
    df['wd'] = df['wd'].fillna(df['wd'].mode()[0])

    bins   = [0, 51, 101, 151, 201, 301, float('inf')]
    labels = ['Good', 'Moderate', 'Unhealthy for Sensitive Groups',
              'Unhealthy', 'Very Unhealthy', 'Hazardous']
    df['AQI_PM25'] = pd.cut(df['PM2.5'], bins=bins, labels=labels)
    df['AQI_PM10'] = pd.cut(df['PM10'],  bins=bins, labels=labels)
    df['date']     = pd.to_datetime(df[['year','month','day','hour']])
    return df, labels

df, AQI_LABELS = load_data()

# Warna tetap
AQI_COLORS  = ['#2ecc71','#f1c40f','#e67e22','#e74c3c','#8e44ad','#2c3e50']
AQI_MAP     = dict(zip(AQI_LABELS, AQI_COLORS))
WHO_PM25    = 15
WHO_PM10    = 45


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 💨 Filter Data")
    st.markdown("---")

    years = sorted(df['year'].unique())
    sel_years = st.multiselect(
        "Pilih Tahun", years, default=years,
        help="Pilih satu atau lebih tahun untuk memfilter semua grafik."
    )
    if not sel_years:
        sel_years = years

    st.markdown("---")
    st.markdown("### Tentang Dashboard")
    st.markdown(
        "Dashboard ini menampilkan analisis kualitas udara di **Changping**, Beijing, "
        "berdasarkan data pengukuran per jam selama periode **Maret 2013 – Februari 2017**."
    )
    st.markdown("---")
    st.markdown(
        "<small>📊 Sumber data: PRSA Air Quality Dataset · "
        "Standar AQI: EPA · Batas WHO: PM2.5 15 µg/m³ | PM10 45 µg/m³</small>",
        unsafe_allow_html=True
    )

dff = df[df['year'].isin(sel_years)]


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("# 💨 Dashboard Kualitas Udara — Changping, Beijing")
st.markdown(
    "Analisis kualitas udara di **Changping, Beijing**"
)
st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: KARTU RINGKASAN
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><h3>📌 Sekilas Info</h3></div>', unsafe_allow_html=True)

total_jam      = len(dff)
rata_pm25      = dff['PM2.5'].mean()
rata_pm10      = dff['PM10'].mean()
pct_good_pm25  = (dff['AQI_PM25'] == 'Good').sum() / total_jam * 100
pct_good_pm10  = (dff['AQI_PM10'] == 'Good').sum() / total_jam * 100
pct_bad_pm25   = (dff['AQI_PM25'].isin(['Unhealthy','Very Unhealthy','Hazardous'])).sum() / total_jam * 100
pct_bad_pm10   = (dff['AQI_PM10'].isin(['Unhealthy','Very Unhealthy','Hazardous'])).sum() / total_jam * 100

c1, c2, c3, c4, c5 = st.columns(5)

def metric_card(col, label, value, sub):
    col.markdown(f"""
    <div class="metric-card">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
        <div class="sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

metric_card(c1, "Total Jam Pengamatan", f"{total_jam:,}", f"{len(sel_years)} tahun dipilih")
metric_card(c2, "Rata-rata PM2.5", f"{rata_pm25:.1f}", "µg/m³ · batas WHO: 15")
metric_card(c3, "Rata-rata PM10",  f"{rata_pm10:.1f}", "µg/m³ · batas WHO: 45")
metric_card(c4, "Jam Udara Aman (PM2.5)", f"{pct_good_pm25:.1f}%", "kategori Good")
metric_card(c5, "Jam Berbahaya (PM10)",   f"{pct_bad_pm10:.1f}%",  "Unhealthy ke atas")

st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2: TREN TAHUNAN
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><h3>📈 Tren Rata-rata PM2.5 dan PM10 per Tahun</h3></div>', unsafe_allow_html=True)

tren = dff.groupby('year')[['PM2.5','PM10']].mean().reset_index()

fig_tren = go.Figure()
fig_tren.add_trace(go.Scatter(
    x=tren['year'], y=tren['PM2.5'],
    name='PM2.5', mode='lines+markers+text',
    line=dict(color='#e74c3c', width=2.5),
    marker=dict(size=10),
    text=[f"{v:.1f}" for v in tren['PM2.5']],
    textposition='top center', textfont=dict(size=11)
))
fig_tren.add_trace(go.Scatter(
    x=tren['year'], y=tren['PM10'],
    name='PM10', mode='lines+markers+text',
    line=dict(color='#3498db', width=2.5),
    marker=dict(size=10),
    text=[f"{v:.1f}" for v in tren['PM10']],
    textposition='top center', textfont=dict(size=11)
))
fig_tren.add_hline(y=WHO_PM25, line_dash='dash', line_color='#e74c3c', opacity=0.5,
                   annotation_text=f"Batas WHO PM2.5 ({WHO_PM25} µg/m³)",
                   annotation_position="bottom right")
fig_tren.add_hline(y=WHO_PM10, line_dash='dash', line_color='#3498db', opacity=0.5,
                   annotation_text=f"Batas WHO PM10 ({WHO_PM10} µg/m³)",
                   annotation_position="top right")
fig_tren.update_layout(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font_color='#cbd5e0',
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    xaxis=dict(tickmode='array', tickvals=tren['year'], gridcolor='rgba(255,255,255,0.05)'),
    yaxis=dict(title='Konsentrasi (µg/m³)', gridcolor='rgba(255,255,255,0.05)'),
    hovermode='x unified', height=380, margin=dict(t=20, b=20)
)
st.plotly_chart(fig_tren, use_container_width=True)

st.markdown("""
<div class="insight-box">
💡Insight :  Konsentrasi PM2.5 dan PM10 di Changping tidak menunjukkan tren penurunan yang konsisten selama periode 2013–2017. 
PM2.5 meningkat dari 72.52 µg/m³ pada tahun 2013 menjadi 78.34 µg/m³ pada tahun 2014, kemudian menurun hingga mencapai titik terendah sebesar 61.45 µg/m³ pada tahun 2016, sebelum kembali meningkat pada awal 2017. 
Pola serupa juga terlihat pada PM10.

Yang lebih mengkhawatirkan, seluruh nilai rata-rata tahunan masih jauh melampaui ambang batas WHO. Bahkan pada kondisi terbaiknya (2016), konsentrasi PM2.5 masih lebih dari empat kali lipat batas yang direkomendasikan. 
Hal ini menunjukkan bahwa polusi udara di Changping masih merupakan masalah struktural yang belum terselesaikan.
""")
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3: TREN BULANAN
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><h3>📅 Pola Bulanan — Apakah Ada Musim Tertentu yang Lebih Buruk?</h3></div>', unsafe_allow_html=True)

bulan_map = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'Mei',6:'Jun',
             7:'Jul',8:'Ags',9:'Sep',10:'Okt',11:'Nov',12:'Des'}

tren_bulan = dff.groupby(['year','month'])[['PM2.5','PM10']].mean().reset_index()
tren_bulan['bulan_label'] = tren_bulan['month'].map(bulan_map)

tab1, tab2 = st.tabs(["PM2.5", "PM10"])

for tab, col, color in [(tab1, 'PM2.5', '#e74c3c'), (tab2, 'PM10', '#3498db')]:
    with tab:
        fig_b = go.Figure()
        for yr in sorted(tren_bulan['year'].unique()):
            d = tren_bulan[tren_bulan['year'] == yr].sort_values('month')
            fig_b.add_trace(go.Scatter(
                x=d['month'], y=d[col],
                name=str(yr), mode='lines+markers',
                line=dict(width=2), marker=dict(size=6),
                hovertemplate=f"%{{y:.1f}} µg/m³<extra>{yr}</extra>"
            ))
        fig_b.add_hline(y=WHO_PM25 if col == 'PM2.5' else WHO_PM10,
                        line_dash='dash', line_color='white', opacity=0.4,
                        annotation_text="Batas WHO", annotation_position="bottom right")
        fig_b.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font_color='#cbd5e0',
            xaxis=dict(tickmode='array', tickvals=list(range(1,13)),
                       ticktext=list(bulan_map.values()),
                       gridcolor='rgba(255,255,255,0.05)'),
            yaxis=dict(title='Konsentrasi (µg/m³)', gridcolor='rgba(255,255,255,0.05)'),
            hovermode='x unified', height=350, margin=dict(t=10, b=10),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        st.plotly_chart(fig_b, use_container_width=True)

st.markdown("""
<div class="insight-box">
"💡 <b>Polusi udara punya musim tersendiri.</b> Konsentrasi PM2.5 dan PM10 secara konsisten melonjak"
"di bulan-bulan dingin (November–Februari) dan relatif membaik di musim panas (Juni–Agustus)."
"Ini mungkin terjadi <b>pembakaran batu bara seperti briket untuk pemanas ruangan</b> di musim dingin,"
"ditambah kondisi atmosfer yang lebih stabil sehingga polutan sulit tersebar."
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4: ARAH ANGIN
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><h3>🧭 Dari Mana Angin Membawa Polusi Terbanyak?</h3></div>', unsafe_allow_html=True)

pm25_wd = dff.groupby('wd')['PM2.5'].mean().sort_values(ascending=False).reset_index()
pm25_wd.columns = ['Arah Angin','Rata-rata PM2.5']
n = len(pm25_wd)
colors_wd = ['#e74c3c' if i < 3 else ('#2ecc71' if i >= n-3 else '#95a5a6') for i in range(n)]

col_bar, col_radar = st.columns([3, 2])

with col_bar:
    fig_wd = go.Figure(go.Bar(
        x=pm25_wd['Arah Angin'],
        y=pm25_wd['Rata-rata PM2.5'],
        marker_color=colors_wd,
        text=[f"{v:.1f}" for v in pm25_wd['Rata-rata PM2.5']],
        textposition='outside',
        hovertemplate='%{x}: <b>%{y:.1f} µg/m³</b><extra></extra>'
    ))
    fig_wd.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font_color='#cbd5e0',
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(title='Rata-rata PM2.5 (µg/m³)', gridcolor='rgba(255,255,255,0.05)'),
        height=380, margin=dict(t=20, b=20),
        showlegend=False
    )
    st.plotly_chart(fig_wd, use_container_width=True)

with col_radar:
    # Radar chart polar
    all_dirs = ['N','NNE','NE','ENE','E','ESE','SE','SSE',
                'S','SSW','SW','WSW','W','WNW','NW','NNW']
    dir_map  = {d: i * (360/16) for i, d in enumerate(all_dirs)}
    pm25_wd['theta'] = pm25_wd['Arah Angin'].map(dir_map)

    fig_polar = go.Figure(go.Barpolar(
        r=pm25_wd['Rata-rata PM2.5'],
        theta=pm25_wd['theta'],
        width=18,
        marker=dict(
            color=pm25_wd['Rata-rata PM2.5'],
            colorscale='RdYlGn_r',
            showscale=True,
            colorbar=dict(title='µg/m³', thickness=12, len=0.7)
        ),
        hovertemplate='%{theta}°: <b>%{r:.1f} µg/m³</b><extra></extra>'
    ))
    fig_polar.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(showticklabels=True, tickfont=dict(size=9, color='#718096'),
                            gridcolor='rgba(255,255,255,0.1)'),
            angularaxis=dict(
                tickmode='array',
                tickvals=[i*(360/16) for i in range(16)],
                ticktext=all_dirs,
                direction='clockwise',
                rotation=90,
                gridcolor='rgba(255,255,255,0.1)',
                tickfont=dict(size=10, color='#a0aec0')
            )
        ),
        height=380, margin=dict(t=20, b=20)
    )
    st.plotly_chart(fig_polar, use_container_width=True)

st.markdown("""
<div class="insight-box">
💡 <b>Arah angin sangat menentukan seberapa buruk udara yang kita hirup.</b>
Angin dari <b>ESE (timur-tenggara)</b> secara konsisten membawa PM2.5 tertinggi (<b>98,2 µg/m³</b>),
sementara angin dari <b>WNW (barat-barat laut)</b> membawa udara paling bersih (<b>42,8 µg/m³</b>).
Selisih antara keduanya lebih dari <b>2× lipat</b> mengindikasikan adanya sumber polusi yang terkonsentrasi
di sisi timur-tenggara Changping, kemungkinan kawasan industri atau jalan arteri padat.
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5: AQI BINNING
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><h3>🏷️ Seberapa Sering Udara di Changping Benar-benar Berbahaya?</h3></div>', unsafe_allow_html=True)
st.markdown(
    "Kita bagi setiap jam pengamatan ke dalam 6 kategori kualitas udara menggunakan bins AQI"
    "untuk PM2.5 dan PM10, sehingga keduanya bisa dibandingkan secara langsung."
)

tab_p25, tab_p10 = st.tabs(["PM2.5", "PM10"])

for tab, aqi_col, title in [
    (tab_p25, 'AQI_PM25', 'PM2.5'),
    (tab_p10, 'AQI_PM10', 'PM10')
]:
    with tab:
        dist    = dff[aqi_col].value_counts().reindex(AQI_LABELS).fillna(0)
        per_yr  = (
            dff.groupby('year')[aqi_col]
            .value_counts(normalize=True).mul(100).round(1)
            .unstack().reindex(columns=AQI_LABELS).fillna(0)
        )

        col_pie, col_stack = st.columns([2, 3])

        with col_pie:
            fig_pie = go.Figure(go.Pie(
                labels=AQI_LABELS,
                values=dist.values,
                marker=dict(colors=AQI_COLORS, line=dict(color='#1a1a2e', width=2)),
                textinfo='percent+label',
                textfont=dict(size=11),
                hole=0.38,
                hovertemplate='%{label}<br><b>%{value:,} jam</b> (%{percent})<extra></extra>'
            ))
            fig_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', font_color='#cbd5e0',
                showlegend=False, height=340, margin=dict(t=10, b=10, l=10, r=10),
                annotations=[dict(text=f'<b>{title}</b>', x=0.5, y=0.5,
                                  font_size=14, showarrow=False, font_color='#e2e8f0')]
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_stack:
            fig_stack = go.Figure()
            for cat, color in zip(AQI_LABELS, AQI_COLORS):
                vals = per_yr[cat].values if cat in per_yr.columns else [0]*len(per_yr)
                fig_stack.add_trace(go.Bar(
                    name=cat,
                    x=per_yr.index.tolist(),
                    y=vals,
                    marker_color=color,
                    hovertemplate=f'{cat}: <b>%{{y:.1f}}%</b><extra></extra>'
                ))
            fig_stack.update_layout(
                barmode='stack',
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font_color='#cbd5e0',
                xaxis=dict(tickmode='array', tickvals=per_yr.index.tolist(),
                           title='Tahun', gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(title='Persentase (%)', range=[0,101],
                           gridcolor='rgba(255,255,255,0.05)'),
                legend=dict(orientation='h', yanchor='bottom', y=1.02,
                            xanchor='right', x=1, font=dict(size=10)),
                height=340, margin=dict(t=40, b=20)
            )
            st.plotly_chart(fig_stack, use_container_width=True)

st.markdown("""
<div class="insight-box">
💡 <b>Perbandingan PM2.5 vs PM10 dengan skala yang sama mengungkap fakta menarik:</b><br>
• <b>PM2.5</b> — 54,2% jam masuk kategori <i>Good</i>, tapi 12,3% jam sudah di level berbahaya (<i>Unhealthy</i> ke atas). Tahun 2017 jadi yang terparah dengan <i>Very Unhealthy</i> melonjak ke <b>9,1%</b>.<br>
• <b>PM10</b> — kondisinya lebih mengkhawatirkan. Hanya <b>37,5%</b> jam yang masuk <i>Good</i>, dan <b>18,8%</b> jam sudah berbahaya hampir 1,5× lebih buruk dari PM2.5.<br>
Artinya, Changping menghadapi <b>tekanan ganda dari kedua jenis partikulat</b> sekaligus. Pemantauan dan pengendalian keduanya perlu dilakukan bersama, bukan salah satu saja.
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6: EKSPLORASI BEBAS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><h3>🔍 Eksplorasi Korelasi Antar Variabel</h3></div>', unsafe_allow_html=True)
st.markdown("Mau lihat hubungan antara dua variabel secara bebas? Pilih saja di bawah ini.")

num_cols = ['PM2.5','PM10','SO2','NO2','CO','O3','TEMP','PRES','DEWP','WSPM','RAIN']
cx, cy = st.columns(2)
x_var = cx.selectbox("Sumbu X", num_cols, index=0)
y_var = cy.selectbox("Sumbu Y", num_cols, index=1)

sample = dff.sample(min(3000, len(dff)), random_state=42)
fig_scatter = px.scatter(
    sample, x=x_var, y=y_var, color='year',
    color_continuous_scale='viridis',
    opacity=0.55,
    labels={x_var: f'{x_var} (µg/m³)' if x_var not in ['TEMP','PRES','DEWP','WSPM','RAIN'] else x_var,
            y_var: f'{y_var} (µg/m³)' if y_var not in ['TEMP','PRES','DEWP','WSPM','RAIN'] else y_var},
    trendline='ols',
    hover_data=['year','month']
)
fig_scatter.update_layout(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font_color='#cbd5e0',
    xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
    yaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
    coloraxis_colorbar=dict(title='Tahun'),
    height=400, margin=dict(t=20, b=20)
)
st.plotly_chart(fig_scatter, use_container_width=True)

corr_val = dff[[x_var, y_var]].corr().iloc[0,1]
st.markdown(f"""
<div class="insight-box">
Korelasi antara <b>{x_var}</b> dan <b>{y_var}</b>: <b>r = {corr_val:.3f}</b>
{"— keduanya bergerak sangat searah, kemungkinan punya sumber yang sama." if corr_val > 0.7
 else "— hubungannya lemah, keduanya dipengaruhi faktor yang berbeda." if abs(corr_val) < 0.3
 else "— ada hubungan moderat di antara keduanya."}
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#4a5568; font-size:0.82rem; padding: 0.5rem 0 1.5rem;">
   Dashboard kualitas udara di Changping Station ·
    Haba L Herlambang Banjarnahor
</div>
""", unsafe_allow_html=True)
