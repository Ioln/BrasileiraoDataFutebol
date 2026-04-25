app_code = """
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="História do Brasileirão",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# DADOS 
@st.cache_data
def load_data():
    df = pd.read_excel("BRAT_FINAL.xlsx")
    df["Data"]       = pd.to_datetime(df["Data"])
    df["Temporada"]  = pd.to_numeric(df["Temporada"], errors="coerce").fillna(0).astype(int)
    df = df[df["Temporada"] > 0]
    return df

df         = load_data()
all_teams  = sorted(df["Time"].dropna().unique().tolist())
all_states = sorted(df["UF Mandante"].dropna().unique().tolist())
seasons    = sorted(df["Temporada"].unique().tolist())

# CONSTANTES / HELPERS

COR_PADRAO = ["#AAFF00","#F7F7F7","#FFFFFF","#39FF14","#00FF7F","#7FFF00"]

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#FFFFFF", family="Inter"),
    margin=dict(t=24, b=44, l=44, r=20),
)

METRIC_MAP = {
    "Aproveitamento (%)":       "aprov",
    "% Vitórias":               "pct_v",
    "% Empates":                "pct_e",
    "% Derrotas":               "pct_d",
    "Média Gols Marcados/Jogo": "gf_j",
    "Média Gols Sofridos/Jogo": "ga_j",
    "Saldo Médio/Jogo":         "saldo_j",
    "Pontos":                   "PTS",
    "Jogos":                    "J",
    "Vitórias":                 "W",
    "Empates":                  "D",
    "Derrotas":                 "L",
}

def calc_aprov(w, d, total):
    return round((w * 3 + d) / (total * 3) * 100, 1) if total > 0 else 0.0

def agg_season(df_in):
    g = df_in.groupby("Temporada").agg(
        J  =("Resultado", "count"),
        W  =("Resultado", lambda x: (x == "V").sum()),
        D  =("Resultado", lambda x: (x == "E").sum()),
        L  =("Resultado", lambda x: (x == "D").sum()),
        GF =("Gols Marcados", "sum"),
        GA =("Gols Sofridos", "sum"),
    ).reset_index()
    g["PTS"]     = g["W"] * 3 + g["D"]
    g["saldo"]   = g["GF"] - g["GA"]
    g["aprov"]   = ((g["W"]*3 + g["D"]) / (g["J"]*3) * 100).round(1)
    g["pct_v"]   = (g["W"] / g["J"] * 100).round(1)
    g["pct_e"]   = (g["D"] / g["J"] * 100).round(1)
    g["pct_d"]   = (g["L"] / g["J"] * 100).round(1)
    g["gf_j"]    = (g["GF"] / g["J"]).round(2)
    g["ga_j"]    = (g["GA"] / g["J"]).round(2)
    g["saldo_j"] = (g["saldo"] / g["J"]).round(2)
    return g

def agg_total(df_in):
    J   = len(df_in)
    W   = (df_in["Resultado"] == "V").sum()
    D   = (df_in["Resultado"] == "E").sum()
    L   = (df_in["Resultado"] == "D").sum()
    GF  = df_in["Gols Marcados"].sum()
    GA  = df_in["Gols Sofridos"].sum()
    PTS = W * 3 + D
    return dict(
        J=J, W=W, D=D, L=L, GF=GF, GA=GA, PTS=PTS,
        saldo=GF-GA,
        aprov=calc_aprov(W, D, J),
        pct_v=round(W/J*100,1) if J else 0,
        pct_e=round(D/J*100,1) if J else 0,
        pct_d=round(L/J*100,1) if J else 0,
        gf_j=round(GF/J,2)      if J else 0,
        ga_j=round(GA/J,2)      if J else 0,
        saldo_j=round((GF-GA)/J,2) if J else 0,
    )

def stat_card(label, value, sub=""):
    return (
        '<div class="stat-card">'
        f'<div class="stat-label">{label}</div>'
        f'<div class="stat-value">{value}</div>'
        f'<div class="stat-sub">{sub}</div>'
        '</div>'
    )

def section_title(text):
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)

def br(n=1):
    st.markdown(f"<div style='margin:{n*8}px 0'></div>", unsafe_allow_html=True)

def render_contact_bar():
    st.markdown(
        '<div class="contact-bar">'
        '<div class="contact-pix">PIX para doações: <span>contato.datafutebol@gmail.com</span></div>'
        '<div class="contact-links">'
        '<a href="https://x.com/DataFutebol"   target="_blank">🐦 Twitter</a>'
        '<a href="https://www.instagram.com/datafutebol_/" target="_blank">📸 Instagram</a>'
        '<a href="https://www.linkedin.com/in/ioannis-canteiro-958280226/"    target="_blank">💻 Linkedln</a>'
        '<a href="mailto:contato.datafutebol@gmail.com">✉️ E-mail</a>'
        '</div></div>',
        unsafe_allow_html=True
    )

with st.sidebar:
    try:
        st.image("Brasileirão.png", use_container_width=True)
    except Exception:
        st.markdown(
            '<div class="sidebar-logo">'
            '<div style="font-size:60px;text-align:center">🏆</div>'
            '<div class="sidebar-title">BRASILEIRAO</div>'
            '<div class="sidebar-sub">HISTORICO COMPLETO</div>'
            '<div class="sidebar-info">1937 – 2025 · 193 times</div>'
            '</div>',
            unsafe_allow_html=True
        )
    st.markdown("---")
    page = st.radio(
        "nav",
        ["🏠 Início", "🔍 Busca de Jogos", "📊 Histórico do Time", "🔥 Sequências", "📈 Gráficos"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.markdown(
        '<div class="sidebar-pix">'
        'PIX: <span>contato.datafutebol@gmail.com</span><br><br>'
        '<a href="https://x.com/DataFutebol">Twitter</a> · '
        '<a href="https://www.instagram.com/datafutebol_/">Instagram</a> · '
        '<a href="https://www.linkedin.com/in/ioannis-canteiro-958280226/">Linkedln</a>'
        '</div>',
        unsafe_allow_html=True
    )

# INÍCIO
if page == "🏠 Início":
    render_contact_bar()

    col_logo, col_texto = st.columns([1, 2])
    with col_logo:
        try:
            st.image("Brasileirão.png", use_container_width=True)
        except Exception:
            st.markdown('<div style="text-align:center;font-size:90px;padding:40px 0">🏆</div>', unsafe_allow_html=True)
    with col_texto:
        st.markdown(
            '<div class="hero-title">BRASILEIRAO<br><span class="hero-green">HISTORICO</span></div>'
            '<div class="hero-desc">'
            'O maior banco de dados do Brasileirão. Todos os jogos do Campeonato Brasileiro '
            'desde <strong>1937</strong>, com as informações de cada partida.'
            '</div>',
            unsafe_allow_html=True
        )

    br(3)
    c1, c2, c3, c4, c5 = st.columns(5)
    for col, (lbl, val, sub) in zip(
        [c1, c2, c3, c4, c5],
        [
            ("JOGOS",      f"{len(df)//2:,}".replace(",","."), "desde 1937"),
            ("TIMES",      str(df["Time"].nunique()),           "participantes"),
            ("TEMPORADAS", str(df["Temporada"].nunique()),      "edições"),
            ("GOLS",       f"{int(df['Gols Marcados'].sum()):,}".replace(",","."), "marcados"),
            ("ESTADOS",    str(df["UF Mandante"].nunique()),    "representados"),
        ]
    ):
        col.markdown(stat_card(lbl, val, sub), unsafe_allow_html=True)

    br(3)
    section_title("O QUE VOCÊ PODE EXPLORAR")
    f1, f2, f3, f4 = st.columns(4)
    for col, (icon, title, desc) in zip(
        [f1, f2, f3, f4],
        [
            ("🔍", "Busca de Jogos",    "Filtre por time, adversário, mando, estado e período."),
            ("📊", "Histórico do Time", "Painel completo de estatísticas de um time no Brasileirão."),
            ("🔥", "Sequências",        "Maiores sequências de V/E/D. Destaque para sequências ativas."),
            ("📈", "Gráficos",          "Evolução por temporada, comparações e scatter plots."),
        ]
    ):
        col.markdown(
            '<div class="feat-card">'
            f'<div class="feat-icon">{icon}</div>'
            f'<div class="feat-title">{title}</div>'
            f'<div class="feat-desc">{desc}</div>'
            '</div>',
            unsafe_allow_html=True
        )

    br(3)
    section_title("APOIE O PROJETO")
    st.markdown(
        '<div class="pix-box">'
        'Este projeto é mantido de forma independente por um apaixonado por futebol e dados.<br>'
        'Se achou útil, considere uma doação via PIX!<br><br>'
        '<strong>Chave PIX: contato.datafutebol@gmail.com</strong><br><br>'
        '📧 <a href="mailto:contato.datafutebol@gmail.com">contato.datafutebol@gmail.com</a>'
        ' &nbsp;·&nbsp; '
        '🐦 <a href="https://x.com/DataFutebol">@DataFutebol</a>'
        ' &nbsp;·&nbsp; '
        '📸 <a href="https://www.instagram.com/datafutebol_/">@datafutebol_.com</a>'
        '</div>',
        unsafe_allow_html=True
    )


# BUSCA DE JOGOS
elif page == "🔍 Busca de Jogos":
    render_contact_bar()
    section_title("🔍 BUSCA DE JOGOS")

    with st.expander("⚙️ FILTROS", expanded=True):
        c1, c2, c3 = st.columns(3)
        time_busca  = c1.selectbox("Time",       ["(Todos)"] + all_teams)
        adv_busca   = c2.selectbox("Adversário", ["(Todos)"] + all_teams)
        venue_busca = c3.selectbox("Mando",      ["Todos", "Mandante (Casa)", "Visitante (Fora)"])

        c4, c5, c6 = st.columns(3)
        estado_oponente = c4.multiselect("Estado do adversário", all_states)
        temp_ini        = c5.selectbox("Temporada início", seasons, index=0)
        temp_fim        = c6.selectbox("Temporada fim",    seasons, index=len(seasons)-1)
        resultado_busca = st.multiselect("Resultado", ["V – Vitória", "E – Empate", "D – Derrota"])

    mask = (df["Temporada"] >= temp_ini) & (df["Temporada"] <= temp_fim)
    if time_busca != "(Todos)":  mask &= df["Time"]       == time_busca
    if adv_busca  != "(Todos)":  mask &= df["Adversário"] == adv_busca
    if venue_busca == "Mandante (Casa)":    mask &= df["Mando"] == "Casa"
    elif venue_busca == "Visitante (Fora)": mask &= df["Mando"] == "Fora"
    if estado_oponente: mask &= df["UF Adversário"].isin(estado_oponente)
    if resultado_busca:
        rmap = {"V – Vitória": "V", "E – Empate": "E", "D – Derrota": "D"}
        mask &= df["Resultado"].isin([rmap[r] for r in resultado_busca])

    res   = df[mask].copy()
    total = len(res)

    if total > 0:
        stats = agg_total(res)
        br()
        cols6 = st.columns(6)
        for col, (lbl, val, sub) in zip(cols6, [
            ("JOGOS",    total,                    "encontrados"),
            ("VITÓRIAS", stats["W"],               f"{stats['pct_v']}%"),
            ("EMPATES",  stats["D"],               f"{stats['pct_e']}%"),
            ("DERROTAS", stats["L"],               f"{stats['pct_d']}%"),
            ("SALDO",    f"{stats['saldo']:+d}",   f"{stats['GF']} GF · {stats['GA']} GC"),
            ("APROV.",   f"{stats['aprov']}%",     "pts possíveis"),
        ]):
            col.markdown(stat_card(lbl, val, sub), unsafe_allow_html=True)

    br()
    show = res[[
        "Temporada","Data","Time","Gols Marcados","Gols Sofridos",
        "Adversário","Mando","Resultado","UF Mandante","UF Adversário","Competição","Fase"
    ]].copy()
    show["Resultado"] = show["Resultado"].map({"V":"✅ Vitória","E":"🟡 Empate","D":"❌ Derrota"})
    show["Data"]      = show["Data"].dt.strftime("%d/%m/%Y")
    show = show.rename(columns={"Gols Marcados":"GF","Gols Sofridos":"GC"})
    st.markdown(f"**{total:,}** jogo(s) encontrado(s)".replace(",","."))
    st.dataframe(show.reset_index(drop=True), use_container_width=True, height=460)


# HISTÓRICO DO TIME
elif page == "📊 Histórico do Time":
    render_contact_bar()
    section_title("📊 HISTÓRICO DO TIME")

    c1, c2, c3 = st.columns([2, 1, 1])
    time_hist = c1.selectbox("Time", all_teams)
    periodo   = c2.selectbox("Período", ["História completa","Por temporada","Intervalo"])
    with c3:
        if periodo == "Por temporada":
            temp_unica = st.selectbox("Temporada", seasons[::-1])
        elif periodo == "Intervalo":
            ca, cb = st.columns(2)
            hist_ini = ca.selectbox("De",  seasons, index=0)
            hist_fim = cb.selectbox("Até", seasons, index=len(seasons)-1)

    t = df[df["Time"] == time_hist].copy()
    if periodo == "Por temporada":
        t = t[t["Temporada"] == temp_unica]
    elif periodo == "Intervalo":
        t = t[(t["Temporada"] >= hist_ini) & (t["Temporada"] <= hist_fim)]

    if len(t) == 0:
        st.warning("Sem dados para o filtro selecionado.")
        st.stop()

    s       = agg_total(t)
    n_seas  = t["Temporada"].nunique()
    home_df = t[t["Mando"] == "Casa"]
    away_df = t[t["Mando"] == "Fora"]

    st.markdown(
        '<div class="team-header">'
        f'<span class="team-name">{time_hist}</span>'
        f'<span class="team-seasons">{n_seas} temporada(s) no Brasileirão</span>'
        '</div>',
        unsafe_allow_html=True
    )
    br()

    for row_stats in [
        [("JOGOS",    s["J"], "disputados"),
         ("VITÓRIAS", s["W"], f"{s['pct_v']}% dos jogos"),
         ("EMPATES",  s["D"], f"{s['pct_e']}% dos jogos"),
         ("DERROTAS", s["L"], f"{s['pct_d']}% dos jogos")],
        [("MÉDIA GF/JOGO",    f"{s['gf_j']}",         f"{s['GF']} gols no total"),
         ("MÉDIA GC/JOGO",    f"{s['ga_j']}",         f"{s['GA']} gols sofridos"),
         ("SALDO MÉDIO/JOGO", f"{s['saldo_j']:+.2f}", f"saldo total {s['saldo']:+d}"),
         ("APROVEITAMENTO",   f"{s['aprov']}%",        f"{s['PTS']} pontos")],
        [("VITÓRIAS EM CASA",
              (home_df["Resultado"]=="V").sum(),
              f"aprov. {calc_aprov((home_df['Resultado']=='V').sum(),(home_df['Resultado']=='E').sum(),len(home_df))}% em {len(home_df)} jogos"),
         ("VITÓRIAS FORA",
              (away_df["Resultado"]=="V").sum(),
              f"aprov. {calc_aprov((away_df['Resultado']=='V').sum(),(away_df['Resultado']=='E').sum(),len(away_df))}% em {len(away_df)} jogos"),
         ("MAIOR PLACAR",  t["Gols Marcados"].max(), "gols marcados num jogo"),
         ("TEMPORADAS",    n_seas,                    "edições do Brasileirão")],
    ]:
        cols = st.columns(4)
        for col, (lbl, val, sub) in zip(cols, row_stats):
            col.markdown(stat_card(lbl, val, sub), unsafe_allow_html=True)
        br()

    col_pie, col_evo = st.columns([1, 2])
    with col_pie:
        section_title("DISTRIBUIÇÃO")
        fig = go.Figure(go.Pie(
            labels=["Vitórias","Empates","Derrotas"],
            values=[s["W"], s["D"], s["L"]],
            hole=0.55,
            marker=dict(colors=["#AAFF00","#C0C0C0","#444444"]),
            textfont=dict(color="#000000"),
        ))
        fig.update_layout(**PLOTLY_LAYOUT, height=280, showlegend=True,
                          legend=dict(font=dict(size=12, color="#FFFFFF")))
        st.plotly_chart(fig, use_container_width=True)

    with col_evo:
        section_title("APROVEITAMENTO POR TEMPORADA")
        by_s = agg_season(t)
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=by_s["Temporada"], y=by_s["aprov"],
            mode="lines+markers",
            line=dict(color="#AAFF00", width=2),
            marker=dict(size=6, color="#FFFFFF"),
            fill="tozeroy", fillcolor="rgba(170,255,0,0.07)"
        ))
        fig2.add_hline(y=s["aprov"], line_dash="dash", line_color="#C0C0C0", opacity=0.5,
                       annotation_text=f"Média: {s['aprov']}%",
                       annotation_font_color="#C0C0C0")
        fig2.update_layout(
            **PLOTLY_LAYOUT, height=280,
            xaxis=dict(gridcolor="#1a1a1a", color="#888"),
            yaxis=dict(gridcolor="#1a1a1a", color="#888", range=[0,100])
        )
        st.plotly_chart(fig2, use_container_width=True)

    br()
    section_title("TOP ADVERSÁRIOS")
    adv = t.groupby("Adversário").agg(
        J=("Resultado","count"),
        W=("Resultado", lambda x: (x=="V").sum()),
        D=("Resultado", lambda x: (x=="E").sum()),
        L=("Resultado", lambda x: (x=="D").sum()),
        GF=("Gols Marcados","sum"),
        GA=("Gols Sofridos","sum"),
    ).reset_index()
    adv["Saldo"]    = adv["GF"] - adv["GA"]
    adv["Aprov%"]   = ((adv["W"]*3 + adv["D"]) / (adv["J"]*3) * 100).round(1)
    adv["Média GF"] = (adv["GF"] / adv["J"]).round(2)
    adv["Média GC"] = (adv["GA"] / adv["J"]).round(2)
    adv = adv.sort_values("J", ascending=False).head(20).reset_index(drop=True)
    adv.index += 1
    adv = adv.rename(columns={"J":"Jogos","W":"V","D":"E","L":"D","GF":"Gols Pró","GA":"Gols Contra"})
    st.dataframe(adv, use_container_width=True, height=380)


# SEQUÊNCIAS
elif page == "🔥 Sequências":
    render_contact_bar()
    section_title("🔥 SEQUÊNCIAS HISTÓRICAS")

    c1, c2, c3, c4 = st.columns(4)
    time_seq  = c1.selectbox("Time", all_teams)
    tipo_seq  = c2.selectbox("Tipo",
        ["Vitórias","Empates","Derrotas","Sem derrota (V+E)","Sem vitória (E+D)"])
    mando_seq = c3.selectbox("Mando", ["Todos","Mandante (Casa)","Visitante (Fora)"])
    adv_seq   = c4.selectbox("Contra time específico", ["(Todos)"] + all_teams)

    seq_df = df[df["Time"] == time_seq].copy().sort_values("Data").reset_index(drop=True)
    if mando_seq == "Mandante (Casa)":   seq_df = seq_df[seq_df["Mando"] == "Casa"]
    elif mando_seq == "Visitante (Fora)": seq_df = seq_df[seq_df["Mando"] == "Fora"]
    if adv_seq != "(Todos)":              seq_df = seq_df[seq_df["Adversário"] == adv_seq]

    FLAGS = {
        "Vitórias":           lambda r: r == "V",
        "Empates":            lambda r: r == "E",
        "Derrotas":           lambda r: r == "D",
        "Sem derrota (V+E)":  lambda r: r in ["V","E"],
        "Sem vitória (E+D)":  lambda r: r in ["E","D"],
    }
    seq_df["flag"] = seq_df["Resultado"].apply(FLAGS[tipo_seq])

    def find_sequences(rows):
        seqs, streak, start = [], 0, None
        for i, flag in enumerate(rows["flag"]):
            if flag:
                streak += 1
                if start is None: start = i
            else:
                if streak:
                    seqs.append({"tamanho": streak,
                                 "inicio": rows.iloc[start]["Data"],
                                 "fim":    rows.iloc[i-1]["Data"],
                                 "ini_idx": start, "fim_idx": i-1, "ativa": False})
                streak, start = 0, None
        if streak:
            seqs.append({"tamanho": streak,
                         "inicio": rows.iloc[start]["Data"],
                         "fim":    rows.iloc[len(rows)-1]["Data"],
                         "ini_idx": start, "fim_idx": len(rows)-1, "ativa": True})
        return sorted(seqs, key=lambda x: x["tamanho"], reverse=True)

    seqs = find_sequences(seq_df)
    top5 = seqs[:5]

    if not top5:
        st.warning("Nenhuma sequência encontrada.")
        st.stop()

    adv_info = f" · vs {adv_seq}" if adv_seq != "(Todos)" else ""
    st.markdown(
        '<div class="seq-header">'
        f'<span class="seq-team">{time_seq}</span>'
        f'<span class="seq-meta"> · {tipo_seq.upper()} · {mando_seq}{adv_info} · {len(seqs)} sequência(s)</span>'
        '</div>',
        unsafe_allow_html=True
    )

    RANK_ICONS  = ["🥇","🥈","🥉","4️⃣","5️⃣"]
    RANK_LABELS = ["1ª MAIOR","2ª MAIOR","3ª MAIOR","4ª MAIOR","5ª MAIOR"]

    for i, seq in enumerate(top5):
        ativa   = seq["ativa"]
        ini_str = seq["inicio"].strftime("%d/%m/%Y")
        fim_str = seq["fim"].strftime("%d/%m/%Y")
        games   = seq_df.iloc[seq["ini_idx"]:seq["fim_idx"]+1]
        resumo  = " → ".join(
            f"{r['Gols Marcados']}-{r['Gols Sofridos']} {r['Adversário']} ({r['Temporada']})"
            for _, r in games.head(5).iterrows()
        )
        if len(games) > 5:
            resumo += f" ... +{len(games)-5} jogos"

        badge    = '<span class="badge-active">⚡ ATIVA</span>' if ativa else ""
        card_cls = "seq-card active" if ativa else ("seq-card gold" if i == 0 else "seq-card")
        cnt_cls  = "seq-count gold" if i == 0 else "seq-count"

        cr, ci = st.columns([1, 5])
        cr.markdown(
            '<div class="seq-rank-box">'
            f'<div style="font-size:26px">{RANK_ICONS[i]}</div>'
            f'<div class="{cnt_cls}">{seq["tamanho"]}</div>'
            f'<div class="seq-tipo">{tipo_seq.lower()}</div>'
            '</div>', unsafe_allow_html=True
        )
        ci.markdown(
            f'<div class="{card_cls}">'
            f'<div class="seq-top"><span class="seq-label">{RANK_LABELS[i]} SEQUÊNCIA</span>{badge}</div>'
            f'<div class="seq-period">📅 {ini_str} → {fim_str}</div>'
            f'<div class="seq-games">{resumo}</div>'
            '</div>', unsafe_allow_html=True
        )

    if len(seqs) > 1:
        br(2)
        section_title("DISTRIBUIÇÃO DE TAMANHOS")
        sizes = [s["tamanho"] for s in seqs]
        fig = px.histogram(x=sizes, nbins=min(20, len(set(sizes))),
                           color_discrete_sequence=["#AAFF00"])
        fig.update_layout(
            **PLOTLY_LAYOUT, height=220, showlegend=False,
            xaxis=dict(title="Tamanho da sequência", gridcolor="#1a1a1a"),
            yaxis=dict(title="Frequência",            gridcolor="#1a1a1a")
        )
        st.plotly_chart(fig, use_container_width=True)


# GRÁFICOS
elif page == "📈 Gráficos":
    render_contact_bar()
    section_title("📈 GRÁFICOS E ANÁLISES")

    tab_evo, tab_scatter, tab_comp = st.tabs(
        ["📉 Evolução Temporal", "🔵 Scatter Plot", "⚖️ Comparação"]
    )

    # ── Evolução Temporal ────────────────────────────────────────────────────
    with tab_evo:
        c1, c2 = st.columns([3, 2])
        times_evo   = c1.multiselect("Times (até 5)", all_teams, default=[all_teams[0]], max_selections=5)
        metrica_evo = c2.selectbox("Métrica", list(METRIC_MAP.keys()), key="evo_met")

        c3, c4 = st.columns(2)
        evo_ini = c3.selectbox("Temporada início", seasons, index=0,              key="evo_ini")
        evo_fim = c4.selectbox("Temporada fim",    seasons, index=len(seasons)-1, key="evo_fim")

        if times_evo:
            br()
            st.markdown("**Cores dos times:**")
            cor_cols = st.columns(len(times_evo))
            cores_escolhidas = []
            for idx, (col, nome) in enumerate(zip(cor_cols, times_evo)):
                c = col.color_picker(nome, value=COR_PADRAO[idx % len(COR_PADRAO)], key=f"cor_evo_{idx}")
                cores_escolhidas.append(c)

            fig_evo = go.Figure()
            for i, nome in enumerate(times_evo):
                t2 = df[(df["Time"] == nome) &
                        (df["Temporada"] >= evo_ini) & (df["Temporada"] <= evo_fim)]
                if len(t2) == 0: continue
                by_s = agg_season(t2)
                y    = by_s[METRIC_MAP[metrica_evo]]
                fig_evo.add_trace(go.Scatter(
                    x=by_s["Temporada"], y=y, name=nome,
                    mode="lines+markers",
                    line=dict(color=cores_escolhidas[i], width=2),
                    marker=dict(size=7, color=cores_escolhidas[i])
                ))
            fig_evo.update_layout(
                **PLOTLY_LAYOUT, height=460, hovermode="x unified",
                xaxis=dict(title="Temporada", gridcolor="#1a1a1a", color="#888"),
                yaxis=dict(title=metrica_evo, gridcolor="#1a1a1a", color="#888"),
                legend=dict(bgcolor="rgba(0,0,0,0.5)", bordercolor="#2a2a2a")
            )
            st.plotly_chart(fig_evo, use_container_width=True)

    # ── Scatter Plot ─────────────────────────────────────────────────────────
    with tab_scatter:
        c1, c2, c3 = st.columns(3)
        sc_modo = c1.selectbox("Escopo", ["História completa","Temporada única","Intervalo"])
        sc_temp = sc_ini = sc_fim = None
        with c2:
            if sc_modo == "Temporada única":
                sc_temp = st.selectbox("Temporada", seasons[::-1], key="sc_temp")
            elif sc_modo == "Intervalo":
                sc_ini = st.selectbox("De", seasons, index=0, key="sc_ini")
        with c3:
            if sc_modo == "Intervalo":
                sc_fim = st.selectbox("Até", seasons, index=len(seasons)-1, key="sc_fim")

        cx, cy, ctam = st.columns(3)
        eixo_x    = cx.selectbox("Eixo X",        list(METRIC_MAP.keys()), index=4, key="sc_x")
        eixo_y    = cy.selectbox("Eixo Y",        list(METRIC_MAP.keys()), index=0, key="sc_y")
        tam_bolha = ctam.selectbox("Tamanho bolha", ["(nenhum)"] + list(METRIC_MAP.keys()), key="sc_tam")

        sc = df.copy()
        if sc_modo == "Temporada única" and sc_temp:
            sc = sc[sc["Temporada"] == sc_temp]
        elif sc_modo == "Intervalo" and sc_ini and sc_fim:
            sc = sc[(sc["Temporada"] >= sc_ini) & (sc["Temporada"] <= sc_fim)]

        agg = sc.groupby("Time").agg(
            J=("Resultado","count"),
            W=("Resultado", lambda x: (x=="V").sum()),
            D=("Resultado", lambda x: (x=="E").sum()),
            L=("Resultado", lambda x: (x=="D").sum()),
            GF=("Gols Marcados","sum"),
            GA=("Gols Sofridos","sum"),
        ).reset_index()
        agg["PTS"]     = agg["W"]*3 + agg["D"]
        agg["saldo"]   = agg["GF"] - agg["GA"]
        agg["aprov"]   = ((agg["W"]*3 + agg["D"]) / (agg["J"]*3) * 100).round(1)
        agg["pct_v"]   = (agg["W"] / agg["J"] * 100).round(1)
        agg["pct_e"]   = (agg["D"] / agg["J"] * 100).round(1)
        agg["pct_d"]   = (agg["L"] / agg["J"] * 100).round(1)
        agg["gf_j"]    = (agg["GF"] / agg["J"]).round(2)
        agg["ga_j"]    = (agg["GA"] / agg["J"]).round(2)
        agg["saldo_j"] = (agg["saldo"] / agg["J"]).round(2)

        x_col    = METRIC_MAP[eixo_x]
        y_col    = METRIC_MAP[eixo_y]
        size_col  = METRIC_MAP[tam_bolha] if tam_bolha != "(nenhum)" else None
        size_data = agg[size_col].abs().clip(lower=1) if size_col else None

        fig_sc = px.scatter(
            agg, x=x_col, y=y_col, text="Time",
            size=size_data, color=y_col,
            color_continuous_scale=[[0,"#444444"],[0.5,"#C0C0C0"],[1,"#AAFF00"]],
            hover_name="Time",
            labels={x_col: eixo_x, y_col: eixo_y}
        )
        fig_sc.update_traces(textposition="top center", textfont=dict(size=9, color="#C0C0C0"))
        fig_sc.update_layout(
            **PLOTLY_LAYOUT, height=520, coloraxis_showscale=False,
            xaxis=dict(gridcolor="#1a1a1a", color="#888"),
            yaxis=dict(gridcolor="#1a1a1a", color="#888")
        )
        st.plotly_chart(fig_sc, use_container_width=True)

    # ── Comparação ───────────────────────────────────────────────────────────
    with tab_comp:
        c1, c2, c3 = st.columns([2,1,1])
        times_comp = c1.multiselect("Times (até 6)", all_teams, default=all_teams[:3], max_selections=6)
        comp_ini   = c2.selectbox("De",  seasons, index=0,              key="comp_ini")
        comp_fim   = c3.selectbox("Até", seasons, index=len(seasons)-1, key="comp_fim")

        if times_comp:
            br()
            st.markdown("**Cores dos times:**")
            cc = st.columns(len(times_comp))
            cores_comp = []
            for idx, (col, nome) in enumerate(zip(cc, times_comp)):
                c_ = col.color_picker(nome, value=COR_PADRAO[idx % len(COR_PADRAO)], key=f"cor_comp_{idx}")
                cores_comp.append(c_)

            tc = df[(df["Time"].isin(times_comp)) &
                    (df["Temporada"] >= comp_ini) & (df["Temporada"] <= comp_fim)]
            ac = tc.groupby("Time").agg(
                J=("Resultado","count"),
                W=("Resultado", lambda x: (x=="V").sum()),
                D=("Resultado", lambda x: (x=="E").sum()),
                L=("Resultado", lambda x: (x=="D").sum()),
                GF=("Gols Marcados","sum"),
                GA=("Gols Sofridos","sum"),
            ).reset_index()
            ac["PTS"]    = ac["W"]*3 + ac["D"]
            ac["Saldo"]  = ac["GF"] - ac["GA"]
            ac["Aprov%"] = ((ac["W"]*3 + ac["D"]) / (ac["J"]*3) * 100).round(1)
            ac["% V"]    = (ac["W"] / ac["J"] * 100).round(1)
            ac["% E"]    = (ac["D"] / ac["J"] * 100).round(1)
            ac["% D"]    = (ac["L"] / ac["J"] * 100).round(1)
            ac["Méd GF"] = (ac["GF"] / ac["J"]).round(2)
            ac["Méd GC"] = (ac["GA"] / ac["J"]).round(2)

            metrica_comp = st.selectbox(
                "Métrica para o gráfico",
                ["Aproveitamento (%)","% Vitórias","% Empates","% Derrotas",
                 "Média GF/Jogo","Média GC/Jogo"],
                key="comp_met"
            )
            map_comp = {
                "Aproveitamento (%)": "Aprov%",
                "% Vitórias":         "% V",
                "% Empates":          "% E",
                "% Derrotas":         "% D",
                "Média GF/Jogo":      "Méd GF",
                "Média GC/Jogo":      "Méd GC",
            }
            fig_comp = go.Figure()
            for i, nome in enumerate(times_comp):
                r = ac[ac["Time"] == nome]
                if len(r) == 0: continue
                fig_comp.add_trace(go.Bar(
                    name=nome,
                    x=[nome],
                    y=[r[map_comp[metrica_comp]].values[0]],
                    marker_color=cores_comp[i],
                    text=[f"{r[map_comp[metrica_comp]].values[0]}"],
                    textposition="outside",
                    textfont=dict(color="#FFFFFF", size=13),
                ))
            fig_comp.update_layout(
                **PLOTLY_LAYOUT, barmode="group", height=380,
                xaxis=dict(gridcolor="#1a1a1a"),
                yaxis=dict(gridcolor="#1a1a1a", title=metrica_comp),
                legend=dict(bgcolor="rgba(0,0,0,0.5)"),
                showlegend=False,
            )
            st.plotly_chart(fig_comp, use_container_width=True)

            section_title("TABELA COMPARATIVA")
            show = ac.rename(columns={
                "Time":"Time","J":"Jogos","W":"V","D":"E","L":"D",
                "GF":"Gols Pró","GA":"Gols Contra","PTS":"Pontos"
            }).sort_values("Aprov%", ascending=False).reset_index(drop=True)
            show.index += 1
            st.dataframe(show, use_container_width=True)
"""
with open("app.py", "w") as f:
    f.write(app_code)
