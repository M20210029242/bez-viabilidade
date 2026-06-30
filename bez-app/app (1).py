"""
BEZ | Análise de Viabilidade Financeira
----------------------------------------
Sistema desenvolvido para a disciplina de Matemática Financeira (UFRN).
Calcula indicadores de viabilidade (VPL, TIR, Payback, Índice de Lucratividade)
para apoiar a decisão de investimento em uma nova coleção da marca BEZ.

Autor: Pedro
Tecnologias: Python, Streamlit, Pandas, NumPy, numpy-financial, Plotly
"""

import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import plotly.graph_objects as go

# ----------------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA E CORES DA MARCA
# ----------------------------------------------------------------------------------

st.set_page_config(
    page_title="BEZ | Viabilidade Financeira",
    page_icon="👔",
    layout="wide",
)

COR_PRIMARIA = "#6B1E2A"   # bordô (cor da marca BEZ)
COR_PRIMARIA_CLARA = "#8C2C3B"
COR_POSITIVO = "#1E8449"
COR_NEUTRO = "#B7950B"
COR_NEGATIVO = "#B03A2E"

# Pequeno ajuste visual: destaca a cor da marca em títulos e na sidebar
st.markdown(
    f"""
    <style>
        h1, h2, h3 {{ color: {COR_PRIMARIA}; }}
        section[data-testid="stSidebar"] {{
            background-color: #FAFAFA;
            border-right: 2px solid {COR_PRIMARIA};
        }}
        div[data-testid="stMetric"] {{
            background-color: #FFFFFF;
            border: 1px solid #E0E0E0;
            border-radius: 10px;
            padding: 12px;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------------
# FUNÇÕES DE CÁLCULO FINANCEIRO
# ----------------------------------------------------------------------------------

def calcular_indicadores(investimento, qtd_produzida, custo_unit, preco_venda,
                          qtd_vendida, tma_mensal, meses):
    """
    Calcula os principais indicadores financeiros do projeto.
    Retorna um dicionário com todos os resultados e o fluxo de caixa mensal.
    """
    receita_total = preco_venda * qtd_vendida
    custo_total = qtd_produzida * custo_unit
    lucro_total = receita_total - custo_total

    # Distribui o lucro igualmente ao longo dos meses (fluxo de caixa simplificado)
    lucro_mensal = lucro_total / meses if meses > 0 else 0

    # Fluxo de caixa: mês 0 é o investimento (saída); meses seguintes, o lucro mensal
    fluxo = [-investimento] + [lucro_mensal] * meses
    fluxo_acumulado = np.cumsum(fluxo)

    # Payback: primeiro mês em que o fluxo acumulado fica positivo
    payback_mes = None
    for i, valor in enumerate(fluxo_acumulado):
        if valor >= 0:
            payback_mes = i
            break

    # VPL (Valor Presente Líquido)
    vpl = npf.npv(tma_mensal / 100, fluxo)

    # TIR (Taxa Interna de Retorno) — só calcula se houver mudança de sinal no fluxo
    try:
        tir = npf.irr(fluxo)
        if tir is None or np.isnan(tir):
            tir = None
    except Exception:
        tir = None

    # Índice de Lucratividade = VP dos retornos / Investimento inicial
    if investimento > 0:
        vp_retornos = vpl + investimento
        indice_lucratividade = vp_retornos / investimento
    else:
        indice_lucratividade = None

    margem = (lucro_total / receita_total * 100) if receita_total > 0 else 0

    df_fluxo = pd.DataFrame({
        "Mês": list(range(0, meses + 1)),
        "Fluxo do Mês (R$)": fluxo,
        "Fluxo Acumulado (R$)": fluxo_acumulado,
    })

    return {
        "receita_total": receita_total,
        "custo_total": custo_total,
        "lucro_total": lucro_total,
        "margem": margem,
        "payback_mes": payback_mes,
        "vpl": vpl,
        "tir": tir,
        "indice_lucratividade": indice_lucratividade,
        "df_fluxo": df_fluxo,
    }


def gerar_recomendacao(resultado, meses):
    """
    Define a recomendação automática (verde/amarelo/vermelho) com base em
    VPL, TIR e Payback.
    """
    vpl = resultado["vpl"]
    payback = resultado["payback_mes"]

    pontos_positivos = 0
    pontos_positivos += 1 if vpl > 0 else 0
    pontos_positivos += 1 if (payback is not None and payback <= meses) else 0
    pontos_positivos += 1 if resultado["indice_lucratividade"] and resultado["indice_lucratividade"] > 1 else 0

    if pontos_positivos == 3:
        return "🟢", "Projeto recomendado", COR_POSITIVO, \
            "O projeto apresenta VPL positivo, payback dentro do prazo e índice de lucratividade favorável."
    elif pontos_positivos == 2:
        return "🟡", "Projeto apresenta risco moderado", COR_NEUTRO, \
            "Pelo menos um indicador ficou abaixo do esperado. Vale revisar premissas de custo ou preço."
    else:
        return "🔴", "Projeto não recomendado", COR_NEGATIVO, \
            "Os indicadores financeiros não sustentam o investimento nas condições atuais."


# ----------------------------------------------------------------------------------
# SIDEBAR — ENTRADA DE DADOS
# ----------------------------------------------------------------------------------

st.sidebar.title("👔 BEZ")
st.sidebar.caption("Dados do projeto / coleção")

nome_projeto = st.sidebar.text_input("Nome do projeto", value="Nova Coleção BEZ")
investimento = st.sidebar.number_input("Investimento inicial (R$)", min_value=0.0, value=10000.0, step=100.0)
qtd_produzida = st.sidebar.number_input("Quantidade produzida (peças)", min_value=1, value=200, step=1)
custo_unit = st.sidebar.number_input("Custo unitário (R$)", min_value=0.0, value=35.0, step=1.0)
preco_venda = st.sidebar.number_input("Preço de venda (R$)", min_value=0.0, value=89.0, step=1.0)
qtd_vendida = st.sidebar.number_input("Quantidade estimada de vendas (peças)", min_value=0, value=180, step=1)
tma = st.sidebar.number_input("Taxa Mínima de Atratividade - TMA (% ao mês)", min_value=0.0, value=2.0, step=0.1)
meses = st.sidebar.number_input("Meses previstos para recuperação", min_value=1, value=6, step=1)

# ----------------------------------------------------------------------------------
# CÁLCULOS
# ----------------------------------------------------------------------------------

resultado = calcular_indicadores(investimento, qtd_produzida, custo_unit, preco_venda,
                                  qtd_vendida, tma, meses)
emoji, titulo_rec, cor_rec, texto_rec = gerar_recomendacao(resultado, meses)

# ----------------------------------------------------------------------------------
# CABEÇALHO
# ----------------------------------------------------------------------------------

st.title(f"BEZ | Análise de Viabilidade — {nome_projeto}")
st.caption("Ferramenta de apoio à decisão de investimento em novas coleções, baseada em indicadores de Matemática Financeira.")

# ----------------------------------------------------------------------------------
# CARDS PRINCIPAIS
# ----------------------------------------------------------------------------------

col1, col2, col3, col4 = st.columns(4)
col1.metric("Receita Total", f"R$ {resultado['receita_total']:,.2f}")
col2.metric("Lucro Total", f"R$ {resultado['lucro_total']:,.2f}")
col3.metric("Investimento", f"R$ {investimento:,.2f}")
col4.metric("Margem", f"{resultado['margem']:.1f}%")

col5, col6, col7 = st.columns(3)
payback_txt = f"{resultado['payback_mes']} meses" if resultado["payback_mes"] is not None else "Não recupera"
col5.metric("Payback", payback_txt)
col6.metric("VPL", f"R$ {resultado['vpl']:,.2f}")
tir_txt = f"{resultado['tir']*100:.2f}% a.m." if resultado["tir"] is not None else "Não calculável"
col7.metric("TIR", tir_txt)

# ----------------------------------------------------------------------------------
# PAINEL DE RECOMENDAÇÃO
# ----------------------------------------------------------------------------------

st.markdown(
    f"""
    <div style="background-color:{cor_rec}20; border-left: 6px solid {cor_rec};
                padding: 16px; border-radius: 8px; margin: 16px 0;">
        <h3 style="color:{cor_rec}; margin:0;">{emoji} {titulo_rec}</h3>
        <p style="margin:4px 0 0 0;">{texto_rec}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------------
# ABAS
# ----------------------------------------------------------------------------------

aba_resultados, aba_cenarios, aba_indicadores = st.tabs(
    ["📊 Resultados", "🔍 Cenários", "📘 Sobre os Indicadores"]
)

# --- ABA: RESULTADOS ---------------------------------------------------------------
with aba_resultados:
    st.subheader("Fluxo de Caixa")
    st.dataframe(resultado["df_fluxo"], use_container_width=True, hide_index=True)

    col_a, col_b = st.columns(2)

    with col_a:
        fig_barras = go.Figure(data=[
            go.Bar(name="Receita", x=["Projeto"], y=[resultado["receita_total"]], marker_color=COR_PRIMARIA),
            go.Bar(name="Custo", x=["Projeto"], y=[resultado["custo_total"]], marker_color="#BDBDBD"),
        ])
        fig_barras.update_layout(title="Receita x Custos", barmode="group")
        st.plotly_chart(fig_barras, use_container_width=True)

    with col_b:
        fig_pizza = go.Figure(data=[go.Pie(
            labels=["Custo de Produção", "Lucro"],
            values=[resultado["custo_total"], max(resultado["lucro_total"], 0)],
            marker_colors=["#BDBDBD", COR_PRIMARIA],
        )])
        fig_pizza.update_layout(title="Distribuição: Custo x Lucro")
        st.plotly_chart(fig_pizza, use_container_width=True)

    fig_linha = go.Figure()
    fig_linha.add_trace(go.Scatter(
        x=resultado["df_fluxo"]["Mês"],
        y=resultado["df_fluxo"]["Fluxo Acumulado (R$)"],
        mode="lines+markers",
        line=dict(color=COR_PRIMARIA, width=3),
        name="Fluxo Acumulado",
    ))
    fig_linha.add_hline(y=0, line_dash="dash", line_color="gray")
    fig_linha.update_layout(title="Fluxo de Caixa Acumulado")
    st.plotly_chart(fig_linha, use_container_width=True)

# --- ABA: CENÁRIOS ------------------------------------------------------------------
with aba_cenarios:
    st.subheader("Análise de Cenários")
    st.caption("Simulação automática considerando diferentes percentuais de vendas.")

    cenarios = {
        "Conservador (60% das vendas)": 0.6,
        "Esperado (80% das vendas)": 0.8,
        "Otimista (100% das vendas)": 1.0,
    }

    cols_cenarios = st.columns(3)

    for col, (nome_cenario, percentual) in zip(cols_cenarios, cenarios.items()):
        qtd_cenario = qtd_vendida * percentual
        res_cenario = calcular_indicadores(investimento, qtd_produzida, custo_unit,
                                            preco_venda, qtd_cenario, tma, meses)
        emoji_c, titulo_c, cor_c, _ = gerar_recomendacao(res_cenario, meses)
        payback_c = f"{res_cenario['payback_mes']} meses" if res_cenario["payback_mes"] is not None else "Não recupera"
        tir_c = f"{res_cenario['tir']*100:.2f}%" if res_cenario["tir"] is not None else "N/A"

        with col:
            st.markdown(
                f"""
                <div style="border: 1px solid #E0E0E0; border-radius: 10px; padding: 16px;">
                    <h4 style="color:{COR_PRIMARIA}; margin-top:0;">{nome_cenario}</h4>
                    <p>Receita: <b>R$ {res_cenario['receita_total']:,.2f}</b></p>
                    <p>Lucro: <b>R$ {res_cenario['lucro_total']:,.2f}</b></p>
                    <p>VPL: <b>R$ {res_cenario['vpl']:,.2f}</b></p>
                    <p>Payback: <b>{payback_c}</b></p>
                    <p>TIR: <b>{tir_c}</b></p>
                    <p style="color:{cor_c}; font-weight:bold;">{emoji_c} {titulo_c}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

# --- ABA: SOBRE OS INDICADORES -------------------------------------------------------
with aba_indicadores:
    st.subheader("O que significa cada indicador?")

    st.markdown("**💰 VPL (Valor Presente Líquido)**")
    st.write("Representa quanto valor financeiro o projeto gera, trazendo todos os fluxos futuros "
             "para o valor presente, descontados pela Taxa Mínima de Atratividade. "
             "VPL positivo indica que o projeto cria valor.")

    st.markdown("**⏱️ Payback**")
    st.write("Tempo necessário para recuperar o valor investido inicialmente, com base no fluxo de caixa gerado pelo projeto.")

    st.markdown("**📈 TIR (Taxa Interna de Retorno)**")
    st.write("Rentabilidade percentual do projeto. Quando a TIR é maior que a TMA, o investimento tende a ser atrativo.")

    st.markdown("**📊 Índice de Lucratividade**")
    st.write("Relação entre o valor presente dos retornos e o investimento inicial. "
             "Valores acima de 1 indicam que o projeto retorna mais do que foi investido, em termos de valor presente.")
