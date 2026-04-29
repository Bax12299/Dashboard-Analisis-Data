import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ─────────────────────────────────────────────
# Konfigurasi halaman
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Kualitas Udara Changping",
    page_icon="🌫️",
    layout="wide"
)

# ─────────────────────────────────────────────
# Load & siapkan data
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("PRSA_Data_Changping_20130301-20170228.csv")

    # Imputasi
    cols_num = ['PM2.5','PM10','SO2','NO2','CO','O3','WSPM','RAIN','TEMP','PRES','DEWP']
    for col in cols_num:
        df[col] = df[col].fillna(df[col].median())
    df['wd'] = df['wd'].fillna(df['wd'].mode()[0])

    # Kolom tambahan
    df['datetime'] = pd.to_datetime(df[['year','month','day','hour']])
    bulan = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'Mei',6:'Jun',
             7:'Jul',8:'Agu',9:'Sep',10:'Okt',11:'Nov',12:'Des'}
    df['month_label'] = df['month'].map(bulan)

    # AQI category
    bins   = [0, 51, 101, 151, 201, 301, float('inf')]
    labels = ['Good','Moderate','Unhealthy for Sensitive Groups',
              'Unhealthy','Very Unhealthy','Hazardous']
    df['AQI_Category'] = pd.cut(df['PM2.5'], bins=bins, labels=labels)

    return df

df = load_data()

# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
st.title("🌫️ Dashboard Kualitas Udara — Stasiun Changping, Beijing")
st.markdown(
    "Dashboard ini menyajikan hasil analisis kualitas udara di stasiun **Changping, Beijing** "
    "berdasarkan data pengamatan per jam dari **Maret 2013 hingga Februari 2017**. "
    "Gunakan filter di sidebar untuk menyesuaikan tampilan data."
)
st.divider()

# ─────────────────────────────────────────────
# Sidebar filter
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("🔧 Filter Data")
    st.markdown("Sesuaikan rentang tahun dan polutan yang ingin ditampilkan.")

    tahun_tersedia = sorted(df['year'].unique())
    tahun_dipilih = st.slider(
        "Rentang Tahun",
        min_value=int(tahun_tersedia[0]),
        max_value=int(tahun_tersedia[-1]),
        value=(int(tahun_tersedia[0]), int(tahun_tersedia[-1]))
    )

    polutan_pilihan = st.multiselect(
        "Polutan yang Ditampilkan",
        options=['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3'],
        default=['PM2.5', 'PM10']
    )

    st.divider()
    st.markdown("**Tentang Dataset**")
    st.markdown(
        "- 📍 Lokasi: Changping, Beijing\n"
        "- 📅 Periode: Mar 2013 – Feb 2017\n"
        "- ⏱️ Frekuensi: Per jam\n"
        "- 📊 Total: 35.064 baris"
    )

# Filter data berdasarkan tahun
df_filtered = df[df['year'].between(tahun_dipilih[0], tahun_dipilih[1])]

# ─────────────────────────────────────────────
# Metrik ringkasan
# ─────────────────────────────────────────────
st.subheader("📌 Ringkasan Periode yang Dipilih")
col1, col2, col3, col4 = st.columns(4)

rata_pm25 = df_filtered['PM2.5'].mean()
rata_pm10 = df_filtered['PM10'].mean()
hari_baik = (df_filtered['AQI_Category'] == 'Good').sum() / len(df_filtered) * 100
hari_buruk = df_filtered['AQI_Category'].isin(['Unhealthy','Very Unhealthy','Hazardous']).sum() / len(df_filtered) * 100

col1.metric("Rata-rata PM2.5", f"{rata_pm25:.1f} µg/m³",
            help="Batas aman WHO: 15 µg/m³")
col2.metric("Rata-rata PM10", f"{rata_pm10:.1f} µg/m³",
            help="Batas aman WHO: 45 µg/m³")
col3.metric("Jam Udara 'Good'", f"{hari_baik:.1f}%",
            help="Persentase jam dengan AQI kategori Good")
col4.metric("Jam Udara Berbahaya", f"{hari_buruk:.1f}%",
            help="Unhealthy + Very Unhealthy + Hazardous")

st.divider()

# ─────────────────────────────────────────────
# Bagian 1 — Tren Tahunan
# ─────────────────────────────────────────────
st.subheader("📈 Pertanyaan 1: Bagaimana tren PM2.5 dan PM10 dari tahun ke tahun?")
st.markdown(
    "Grafik berikut menunjukkan rata-rata konsentrasi PM2.5 dan PM10 per tahun "
    "dibandingkan dengan ambang batas aman WHO. Idealnya, nilai-nilai ini terus "
    "mendekati atau berada di bawah garis putus-putus."
)

tren = df_filtered.groupby('year')[['PM2.5','PM10']].mean().reset_index()

fig1, axes = plt.subplots(1, 2, figsize=(13, 4.5))
fig1.suptitle(
    f"Tren Rata-rata PM2.5 dan PM10 di Changping ({tahun_dipilih[0]}–{tahun_dipilih[1]})",
    fontsize=12, fontweight='bold'
)

who = {'PM2.5': (15, 'tomato'), 'PM10': (45, 'steelblue')}
for ax, (col, (batas, warna)) in zip(axes, who.items()):
    ax.plot(tren['year'], tren[col], marker='o', color=warna,
            linewidth=2.2, markersize=8, label=col)
    ax.axhline(y=batas, color='gray', linestyle='--', linewidth=1.2,
               label=f'Batas WHO ({batas} µg/m³)')
    for _, row in tren.iterrows():
        ax.annotate(f"{row[col]:.1f}",
                    xy=(row['year'], row[col]),
                    xytext=(0, 10), textcoords='offset points',
                    ha='center', fontsize=9)
    ax.set_title(f'Rata-rata {col} per Tahun', fontweight='bold')
    ax.set_xlabel('Tahun')
    ax.set_ylabel('Konsentrasi (µg/m³)')
    ax.set_xticks(tren['year'])
    ax.legend(fontsize=8)
    ax.grid(axis='y', alpha=0.3)
    ax.spines[['top','right']].set_visible(False)

plt.tight_layout()
st.pyplot(fig1)

with st.expander("💡 Baca insight dari grafik ini"):
    st.markdown(
        "Tren PM2.5 dan PM10 **tidak turun secara konsisten** sepanjang periode analisis. "
        "Keduanya sempat naik di 2014, kemudian turun ke titik terendah di **2016**, "
        "namun kembali meningkat di awal 2017. Yang perlu dicatat, seluruh nilai "
        "rata-rata tahunan masih **jauh melampaui batas WHO** — bahkan nilai terbaik "
        "di 2016 pun masih lebih dari 4× lipat batas PM2.5. Ini menunjukkan polusi "
        "udara di Changping masih menjadi masalah struktural yang belum terselesaikan."
    )

st.divider()

# ─────────────────────────────────────────────
# Bagian 2 — Arah Angin vs PM2.5
# ─────────────────────────────────────────────
st.subheader("🧭 Pertanyaan 2: Dari arah mana polusi paling sering datang?")
st.markdown(
    "Rata-rata konsentrasi PM2.5 dihitung untuk setiap dari 16 arah angin yang tercatat. "
    "Ini membantu kita mengidentifikasi dari sisi mana sumber polusi paling dominan berasal."
)

pm25_wd = df_filtered.groupby('wd')['PM2.5'].mean().sort_values(ascending=False).reset_index()
pm25_wd.columns = ['Arah Angin', 'Rata-rata PM2.5']
n = len(pm25_wd)
colors_wd = ['#e74c3c' if i < 3 else ('#2ecc71' if i >= n-3 else '#95a5a6')
             for i in range(n)]

fig2, ax2 = plt.subplots(figsize=(12, 4.5))
bars2 = ax2.bar(pm25_wd['Arah Angin'], pm25_wd['Rata-rata PM2.5'],
                color=colors_wd, edgecolor='white', width=0.6)
for bar, val in zip(bars2, pm25_wd['Rata-rata PM2.5']):
    ax2.text(bar.get_x() + bar.get_width()/2,
             bar.get_height() + 0.8, f'{val:.1f}',
             ha='center', va='bottom', fontsize=8)
ax2.set_title(
    f"Rata-rata PM2.5 Berdasarkan Arah Angin ({tahun_dipilih[0]}–{tahun_dipilih[1]})",
    fontweight='bold', fontsize=11
)
ax2.set_xlabel('Arah Angin')
ax2.set_ylabel('Rata-rata PM2.5 (µg/m³)')
ax2.grid(axis='y', alpha=0.3)
ax2.spines[['top','right']].set_visible(False)
legend_wd = [
    mpatches.Patch(facecolor='#e74c3c', label='3 Tertinggi'),
    mpatches.Patch(facecolor='#2ecc71', label='3 Terendah'),
    mpatches.Patch(facecolor='#95a5a6', label='Lainnya'),
]
ax2.legend(handles=legend_wd, loc='upper right', fontsize=9)
plt.tight_layout()
st.pyplot(fig2)

col_a, col_b = st.columns(2)
with col_a:
    st.markdown("**🔴 3 Arah Angin Terkotor:**")
    st.dataframe(pm25_wd.head(3).reset_index(drop=True), use_container_width=True)
with col_b:
    st.markdown("**🟢 3 Arah Angin Terbersih:**")
    st.dataframe(pm25_wd.tail(3).reset_index(drop=True), use_container_width=True)

with st.expander("💡 Baca insight dari grafik ini"):
    st.markdown(
        "Angin dari arah **timur-tenggara (ESE, E, SE)** secara konsisten membawa "
        "konsentrasi PM2.5 tertinggi, sementara angin dari **barat-barat laut (WNW, W, NW)** "
        "membawa udara paling bersih. Selisih keduanya mencapai lebih dari 2× lipat — "
        "mengindikasikan adanya sumber polusi yang terkonsentrasi di sisi timur-tenggara "
        "wilayah Changping."
    )

st.divider()

# ─────────────────────────────────────────────
# Bagian 3 — AQI Binning
# ─────────────────────────────────────────────
st.subheader("🗂️ Analisis Lanjutan 1: Seberapa sering udara berada di level berbahaya?")
st.markdown(
    "Menggunakan standar **AQI dari EPA**, setiap jam pengamatan dikategorikan ke dalam "
    "6 level kualitas udara berdasarkan konsentrasi PM2.5. "
    "Ini memberi gambaran yang lebih konkret dibanding angka rata-rata saja."
)

labels_aqi = ['Good','Moderate','Unhealthy for Sensitive Groups',
              'Unhealthy','Very Unhealthy','Hazardous']
palette_aqi = ['#2ecc71','#f1c40f','#e67e22','#e74c3c','#8e44ad','#2c3e50']

aqi_dist = df_filtered['AQI_Category'].value_counts().reindex(labels_aqi)
aqi_per_year = (
    df_filtered.groupby('year')['AQI_Category']
    .value_counts(normalize=True)
    .mul(100).round(1)
    .unstack()
    .reindex(columns=labels_aqi)
)

fig3, axes3 = plt.subplots(1, 2, figsize=(14, 5))
fig3.suptitle(
    f"Distribusi Kategori AQI PM2.5 di Changping ({tahun_dipilih[0]}–{tahun_dipilih[1]})",
    fontsize=12, fontweight='bold'
)

# Pie chart
axes3[0].pie(aqi_dist, labels=aqi_dist.index, autopct='%1.1f%%',
             colors=palette_aqi, startangle=90,
             wedgeprops={'edgecolor':'white','linewidth':1.2})
axes3[0].set_title('Proporsi Keseluruhan', fontweight='bold')

# Stacked bar dengan label %
bottoms = [0] * len(aqi_per_year)
for col_aqi, color in zip(labels_aqi, palette_aqi):
    if col_aqi not in aqi_per_year.columns:
        continue
    vals = aqi_per_year[col_aqi].fillna(0).values
    bars3 = axes3[1].bar(aqi_per_year.index, vals, bottom=bottoms,
                         color=color, edgecolor='white', label=col_aqi)
    for bar, val, bot in zip(bars3, vals, bottoms):
        if val > 3:
            axes3[1].text(
                bar.get_x() + bar.get_width()/2,
                bot + val/2,
                f'{val:.1f}%',
                ha='center', va='center',
                fontsize=7.5, color='white', fontweight='bold'
            )
    bottoms = [b + v for b, v in zip(bottoms, vals)]

axes3[1].set_title('Distribusi per Tahun', fontweight='bold')
axes3[1].set_xlabel('Tahun')
axes3[1].set_ylabel('Persentase (%)')
axes3[1].set_xticks(aqi_per_year.index)
axes3[1].set_xticklabels(aqi_per_year.index, rotation=0)
axes3[1].legend(title='Kategori AQI', bbox_to_anchor=(1.05,1),
                loc='upper left', fontsize=8)
axes3[1].grid(axis='y', alpha=0.3)
axes3[1].spines[['top','right']].set_visible(False)

plt.tight_layout()
st.pyplot(fig3)

with st.expander("💡 Baca insight dari grafik ini"):
    st.markdown(
        "Dari total jam pengamatan, **54,2% berada di kategori Good** — artinya lebih dari "
        "separuh waktu udara masih dalam batas aman. Namun **12,3% jam masuk kategori "
        "Unhealthy ke atas**, setara dengan sekitar 1 dari 8 jam pengamatan. "
        "Tren membaik dari 2013 ke 2016, tapi berbalik di 2017 di mana kategori "
        "*Very Unhealthy* melonjak ke 9,1% — tertinggi sepanjang periode analisis."
    )

st.divider()

# ─────────────────────────────────────────────
# Bagian 4 — Pola Bulanan PM10
# ─────────────────────────────────────────────
st.subheader("📆 Analisis Lanjutan 2: Kapan PM10 paling tinggi dalam setahun?")
st.markdown(
    "PM10 menunjukkan pola musiman yang menarik — berbeda dari PM2.5 yang lebih "
    "dominan di musim dingin, PM10 juga dipengaruhi oleh **badai debu musim semi** "
    "dari Gurun Gobi. Grafik berikut memperlihatkan pola bulanannya."
)

bulan_label = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'Mei',6:'Jun',
               7:'Jul',8:'Agu',9:'Sep',10:'Okt',11:'Nov',12:'Des'}

pm10_bulanan  = df_filtered.groupby(['year','month'])['PM10'].mean().reset_index()
pm10_avg_bln  = df_filtered.groupby('month')['PM10'].mean()

fig4, axes4 = plt.subplots(1, 2, figsize=(14, 4.5))
fig4.suptitle(
    f"Pola Bulanan PM10 di Changping ({tahun_dipilih[0]}–{tahun_dipilih[1]})",
    fontsize=12, fontweight='bold'
)

# Line chart per tahun
for year, grp in pm10_bulanan.groupby('year'):
    axes4[0].plot(grp['month'], grp['PM10'], marker='o',
                  label=str(year), linewidth=1.8)
axes4[0].axhline(y=45, color='gray', linestyle='--',
                 linewidth=1.2, label='Batas WHO (45 µg/m³)')
axes4[0].set_title('Tren Bulanan per Tahun', fontweight='bold')
axes4[0].set_xlabel('Bulan')
axes4[0].set_ylabel('Rata-rata PM10 (µg/m³)')
axes4[0].set_xticks(range(1,13))
axes4[0].set_xticklabels(bulan_label.values(), fontsize=8)
axes4[0].legend(title='Tahun', fontsize=8)
axes4[0].grid(alpha=0.3)
axes4[0].spines[['top','right']].set_visible(False)

# Bar chart rata-rata
warna_bar = ['#e74c3c' if v == pm10_avg_bln.max()
             else ('#2ecc71' if v == pm10_avg_bln.min() else '#95a5a6')
             for v in pm10_avg_bln.values]
bars4 = axes4[1].bar([bulan_label[m] for m in pm10_avg_bln.index],
                     pm10_avg_bln.values, color=warna_bar, edgecolor='white')
axes4[1].axhline(y=45, color='gray', linestyle='--',
                 linewidth=1.2, label='Batas WHO (45 µg/m³)')
for bar, val in zip(bars4, pm10_avg_bln.values):
    axes4[1].text(bar.get_x() + bar.get_width()/2,
                  bar.get_height() + 1, f'{val:.1f}',
                  ha='center', fontsize=8)
legend_pm10 = [
    mpatches.Patch(facecolor='#e74c3c', label='Tertinggi (Mar)'),
    mpatches.Patch(facecolor='#2ecc71', label='Terendah (Agu)'),
    mpatches.Patch(facecolor='#95a5a6', label='Lainnya'),
]
axes4[1].legend(handles=legend_pm10, fontsize=8)
axes4[1].set_title('Rata-rata Bulanan (Semua Tahun)', fontweight='bold')
axes4[1].set_xlabel('Bulan')
axes4[1].set_ylabel('Rata-rata PM10 (µg/m³)')
axes4[1].grid(axis='y', alpha=0.3)
axes4[1].spines[['top','right']].set_visible(False)

plt.tight_layout()
st.pyplot(fig4)

with st.expander("💡 Baca insight dari grafik ini"):
    st.markdown(
        "PM10 memiliki **dua puncak dalam setahun**: puncak pertama di **Maret (129,30 µg/m³)** "
        "akibat badai debu dari Gurun Gobi, dan puncak kedua di **Desember (110,35 µg/m³)** "
        "saat musim dingin. Titik terendah jatuh di **Agustus (63,33 µg/m³)** — bertepatan "
        "dengan musim hujan yang membantu membersihkan partikel dari udara. Pola dua puncak "
        "ini yang membedakan PM10 dari PM2.5, yang lebih didominasi musim dingin saja."
    )

st.divider()

# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center; color:gray; font-size:13px;'>"
    "Data bersumber dari PRSA Air Quality Dataset — Stasiun Changping, Beijing (2013–2017). "
    "Dashboard dibuat sebagai bagian dari proyek analisis data."
    "</div>",
    unsafe_allow_html=True
)
