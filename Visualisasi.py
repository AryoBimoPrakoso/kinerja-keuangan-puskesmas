import pandas as pd
import plotly.graph_objects as go
import vizro.models as vm
from vizro import Vizro
from vizro.models.types import capture
import vizro.plotly.express as px
from vizro.tables import dash_ag_grid

data = pd.read_csv("./dataset/puskesmas.csv")
data.info()
df = data.dropna()

df_keuangan = pd.read_csv("./data-visualisasi/df_keuangan.csv")
df_keuangan_agregat = pd.read_csv("./data-visualisasi/df_keuangan_agregat.csv")
df_keuangan_agregat_tabel = pd.read_csv("./data-visualisasi/df_keuangan_agregat_tabel.csv")

df_program_anggaran = (
    df.groupby(["TAHUN", "PENERIMA MANFAAT (HB)", "FS1", "PR1", "HA2", "Karakter Puskesmas"])[["ALOKASI BELANJA (RP)", "REALISASI BELANJA (RP)"]]
    .sum()
    .reset_index()
)

@capture("graph")
def sankey_alokasi_anggaran(data_frame: pd.DataFrame):
    """
    Membuat diagram Sankey untuk aliran anggaran dari FS1 -> PR1 -> HA2 -> Penerima Manfaat
    """
    # Menyiapkan data untuk Sankey
    sources = []
    targets = []
    values = []

    # Unique values untuk setiap kategori
    FS1_unique = data_frame["FS1"].unique()
    PR1_unique = data_frame["PR1"].unique()
    HA2_unique = data_frame["HA2"].unique()
    hb_unique = data_frame["PENERIMA MANFAAT (HB)"].unique()

    # Membuat label mapping dengan urutan: FS1, PR1, HA2, HB
    all_labels = (
        list(FS1_unique) + list(PR1_unique) + list(HA2_unique) + list(hb_unique)
    )
    label_to_index = {label: idx for idx, label in enumerate(all_labels)}

    # Flow 1: FS1 -> PR1 (Alokasi Belanja)
    FS1_to_PR1 = (
        data_frame.groupby(["FS1", "PR1"])["REALISASI BELANJA (RP)"].sum().reset_index()
    )
    for _, row in FS1_to_PR1.iterrows():
        sources.append(label_to_index[row["FS1"]])
        targets.append(label_to_index[row["PR1"]])
        values.append(row["REALISASI BELANJA (RP)"])

    # Flow 2: PR1 -> HA2 (Program ke Jenis Kegiatan)
    PR1_to_HA2 = (
        data_frame.groupby(["PR1", "HA2"])["REALISASI BELANJA (RP)"].sum().reset_index()
    )
    for _, row in PR1_to_HA2.iterrows():
        sources.append(label_to_index[row["PR1"]])
        targets.append(label_to_index[row["HA2"]])
        values.append(row["REALISASI BELANJA (RP)"])

    # Flow 3: HA2 -> PENERIMA MANFAAT (Jenis Kegiatan ke Penerima Manfaat)
    HA2_to_HB = (
        data_frame.groupby(["HA2", "PENERIMA MANFAAT (HB)"])["REALISASI BELANJA (RP)"]
        .sum()
        .reset_index()
    )
    for _, row in HA2_to_HB.iterrows():
        sources.append(label_to_index[row["HA2"]])
        targets.append(label_to_index[row["PENERIMA MANFAAT (HB)"]])
        values.append(row["REALISASI BELANJA (RP)"])

    # Warna yang lebih bervariasi untuk 4 level
    node_colors = []
    # Warna untuk FS1 (Sumber Pembiayaan) - Biru
    node_colors.extend(["#1f77b4"] * len(FS1_unique))
    # Warna untuk PR1 (Program) - Orange
    node_colors.extend(["#ff7f0e"] * len(PR1_unique))
    # Warna untuk HA2 (Jenis Kegiatan) - Hijau
    node_colors.extend(["#2ca02c"] * len(HA2_unique))
    # Warna untuk HB (Penerima Manfaat) - Merah
    node_colors.extend(["#d62728"] * len(hb_unique))

    return go.Figure(
        data=go.Sankey(
            node={
                "pad": 15,
                "thickness": 20,
                "line": {"color": "black", "width": 0.5},
                "label": all_labels,
                "color": node_colors,
                "hovertemplate": "%{label}<br>Total: Rp %{value:,.0f}<extra></extra>",
            },
            link={
                "source": sources,
                "target": targets,
                "value": values,
                "color": "rgba(100, 150, 200, 0.3)",
                "hovertemplate": "%{source.label} → %{target.label}<br>Nilai: Rp %{value:,.0f}<extra></extra>",
            },
            valueformat=",.0f",
            valuesuffix=" ",
        ),
        layout={
            "title": "Aliran Anggaran: Sumber Pembiayaan → Program → Jenis Kegiatan → Penerima Manfaat",
            "font": {"size": 11},
            "height": 650,
            "margin": {"l": 50, "r": 50, "t": 80, "b": 50},
        },
    )


page1 = vm.Page(
    title="Visualisasi Kinerja Keuangan Antara Puskesmas Perkotaan dan Perdesaan",
    layout=vm.Grid(grid=[[0], [1], [2], [3]], row_min_height="650px"),
    components=[
        vm.Container(
            layout=vm.Flex(direction="column"),
            components=[
                vm.Graph(
                    id="sankey_diagram",
                    figure=sankey_alokasi_anggaran(df_program_anggaran),
                ),
            ],
        ),
        vm.Container(
            layout=vm.Grid(grid=[[0,1]]),
            components=[
                vm.Graph(
                    id="histogram-alokasi",
                    figure=px.histogram(
                        df_keuangan,
                        title="Total Alokasi Belanja sesuai Karakter Puskesmas",
                        y="TOTAL ALOKASI BELANJA (RP)",
                        x="Karakter Puskesmas",
                        color="TAHUN",
                        barmode="group",
                        labels={
                            "TOTAL ALOKASI BELANJA (RP)": "Total Alokasi Belanja",
                        },
                        hover_data={
                            "Nama Puskesmas": True,
                            "TOTAL ALOKASI BELANJA (RP)": False,
                            "alokasi_rupiah": True,
                        },
                        height=650,
                    ),
                ),
                vm.Graph(
                    id="histogram-realisasi",
                    figure=px.histogram(
                        df_keuangan,
                        title="Total Realisasi Belanja sesuai Karakter Puskesmas",
                        y="TOTAL REALISASI BELANJA (RP)",
                        x="Karakter Puskesmas",
                        barmode="group",
                        labels={
                            "TOTAL REALISASI BELANJA (RP)": "Total Realisasi Belanja",
                        },
                        color="TAHUN",
                        hover_data={
                            "Nama Puskesmas": True,
                            "TOTAL REALISASI BELANJA (RP)": False,
                            "realisasi_rupiah": True,
                        },
                        height=650,
                    ),
                ),
            ],
        ),
        vm.Container(
            layout=vm.Grid(grid=[[0, 1]]),
            components=[
                vm.Graph(
                    id="grafik_perbandingan_alokasi_realisasi",
                    figure=px.line(
                        df_keuangan_agregat,
                        x="Karakter Puskesmas",
                        y=[
                            "TOTAL ALOKASI BELANJA (RP)",
                            "TOTAL REALISASI BELANJA (RP)",
                        ],
                        color="TAHUN",
                        title="Perbandingan Total Alokasi dan Realisasi Belanja sesuai Karakter Puskesmas",
                        labels={
                            "Karakter Puskesmas": "Karakter Puskesmas",
                            "RATA-RATA REALISASI BELANJA (RP)": "Rata-rata Realisasi",
                        },
                        markers=True,
                        height=650,
                    ),
                ),
                vm.Graph(
                    id="grafik_perbandingan_rata_rata_alokasi_realisasi",
                    figure=px.line(
                        df_keuangan_agregat,
                        x="Karakter Puskesmas",
                        y=[
                            "RATA-RATA ALOKASI BELANJA (RP)",
                            "RATA-RATA REALISASI BELANJA (RP)",
                        ],
                        color="TAHUN",
                        title="Perbandingan Rata-rata Alokasi dan Realisasi Belanja sesuai Karakter Puskesmas",
                        labels={
                            "Karakter Puskesmas": "Karakter Puskesmas",
                            "RATA-RATA REALISASI BELANJA (RP)": "Rata-rata Realisasi",
                        },
                        markers=True,
                        height=650,
                    ),
                ),
            ],
        ),
        vm.Container(
            layout=vm.Grid(grid=[[0]]),
            components=[
                vm.AgGrid(
                    id="tabel_kesimpulan",
                    title="Kesimpulan Keseluruhan",
                    figure=dash_ag_grid(
                        df_keuangan_agregat_tabel,
                        columnDefs=[
                            {
                                "field": "TAHUN",
                                "headerName": "TAHUN",
                            },
                            {
                                "field": "Karakter Puskesmas",
                                "headerName": "Karakter Puskesmas",
                            },
                            {
                                "field": "TOTAL ALOKASI BELANJA (RP)",
                                "headerName": "Total Alokasi Belanja",
                            },
                            {
                                "field": "RATA-RATA ALOKASI BELANJA (RP)",
                                "headerName": "Rata-rata Alokasi Belanja",
                            },
                            {
                                "field": "TOTAL REALISASI BELANJA (RP)",
                                "headerName": "Total Realisasi Belanja",
                            },
                            {
                                "field": "RATA-RATA REALISASI BELANJA (RP)",
                                "headerName": "Rata-rata Realisasi Belanja",
                            },
                            {
                                "field": "RASIO REALISASI (%)",
                                "headerName": "Rasio Realisasi (%)",
                            },
                        ],
                    ),
                ),
            ],
        ),
    ],
    controls=[
        vm.Filter(
            column="TAHUN",
            targets=["sankey_diagram", "tabel_kesimpulan"],
            selector=vm.Dropdown(
                options=df["TAHUN"].unique().tolist(),
                multi=True,
                value=df["TAHUN"].unique().tolist(),
            ),
        ),
        vm.Filter(
            column="Karakter Puskesmas",
            targets=["sankey_diagram", "tabel_kesimpulan"],
            selector=vm.Checklist(
                options=df["Karakter Puskesmas"].unique().tolist(),
                value=df["Karakter Puskesmas"].unique().tolist(),
            ),
        ),
    ],
)

dashboard = vm.Dashboard(pages=[page1])
Vizro().build(dashboard).run()
