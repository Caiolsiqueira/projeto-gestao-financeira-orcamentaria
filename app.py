"""
Projeto Gestão Financeira e Orçamentária — Indústria Moveleira Vanguarda S.A.
Dashboard Executivo & Simulador Interativo de Controladoria (Com Modo Didático para Leigos)

Autor: Caio Lucas Siqueira
LinkedIn: linkedin.com/in/caio-lucas-siqueira-7py
"""

from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import streamlit.components.v1 as components

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILIZAÇÃO ADAPTATIVA (LIGHT / DARK MODE)
# ==============================================================================
st.set_page_config(
    page_title="Controladoria & Orçamento | Indústria Moveleira",
    page_icon="🪑",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
    }
    div[data-testid="stMetric"] {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.22);
        border-radius: 10px;
        padding: 14px 18px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
    }
    .exec-banner {
        background: linear-gradient(135deg, rgba(30, 64, 175, 0.12), rgba(15, 118, 110, 0.12));
        border-left: 5px solid #2563eb;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 18px;
    }
    .simple-box {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.12), rgba(16, 185, 129, 0.10));
        border: 1px solid rgba(245, 158, 11, 0.40);
        border-left: 5px solid #f59e0b;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 18px;
    }
    .diagnosis-card {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.22);
        border-left: 4px solid #ef4444;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 12px;
    }
    .solution-card {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.22);
        border-left: 4px solid #10b981;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 12px;
    }
    .formula-box {
        background-color: var(--secondary-background-color);
        border: 1px dashed rgba(37, 99, 235, 0.5);
        border-radius: 8px;
        padding: 12px 16px;
        margin: 10px 0;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# 2. FUNÇÕES DE ENGENHARIA ECONÔMICA E MATEMÁTICA FINANCEIRA
# ==============================================================================
def calc_npv(rate: float, cash_flows: list[float]) -> float:
    """Calcula o Valor Presente Líquido (VPL / NPV)."""
    return float(sum(cf / ((1.0 + rate) ** t) for t, cf in enumerate(cash_flows)))


def calc_irr(cash_flows: list[float], tol: float = 1e-7, max_iter: int = 1000) -> float:
    """Calcula a Taxa Interna de Retorno (TIR / IRR)."""
    low, high = -0.50, 5.00
    npv_low = calc_npv(low, cash_flows)
    npv_high = calc_npv(high, cash_flows)
    if npv_low * npv_high > 0:
        return float("nan")

    mid = 0.15
    for _ in range(max_iter):
        mid = (low + high) / 2.0
        npv_mid = calc_npv(mid, cash_flows)
        if abs(npv_mid) < tol:
            return mid
        if npv_low * npv_mid < 0:
            high = mid
            npv_high = npv_mid
        else:
            low = mid
            npv_low = npv_mid
    return mid


def calc_profitability_index(rate: float, cash_flows: list[float]) -> float:
    """Calcula o Índice de Lucratividade (IL = VP dos benefícios / Investimento Inicial)."""
    initial_investment = abs(cash_flows[0])
    if initial_investment == 0:
        return 0.0
    pv_inflows = sum(cf / ((1.0 + rate) ** t) for t, cf in enumerate(cash_flows[1:], start=1))
    return float(pv_inflows / initial_investment)


def calc_discounted_payback(rate: float, cash_flows: list[float]) -> float:
    """Calcula o Payback Descontado (tempo para recuperar o dinheiro investido)."""
    cumulative = cash_flows[0]
    for t in range(1, len(cash_flows)):
        discounted_cf = cash_flows[t] / ((1.0 + rate) ** t)
        prev_cumulative = cumulative
        cumulative += discounted_cf
        if cumulative >= 0 and prev_cumulative < 0:
            fraction = abs(prev_cumulative) / discounted_cf
            return float((t - 1) + fraction)
    return float("inf")


def format_brl(value: float) -> str:
    """Formata valores numéricos no padrão monetário brasileiro (R$ 1.234.567,89)."""
    sign = "-" if value < 0 else ""
    abs_val = abs(value)
    formatted = f"{abs_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{sign}R$ {formatted}"


def format_int_br(value: float) -> str:
    """Formata inteiros com separador de milhar brasileiro."""
    return f"{int(round(value)):,}".replace(",", ".")


# ==============================================================================
# 3. MOTOR DE SIMULAÇÃO DO ESTUDO DE CASO (12 MESES — JAN A DEZ)
# ==============================================================================
@st.cache_data
def get_base_parameters() -> dict:
    """Retorna as premissas base da Indústria Moveleira Vanguarda S.A."""
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

    # 1. Vendas Orçadas: Repetição ingênua do ano anterior (1.000 móveis/mês = 12.000 móveis/ano)
    vendas_orcadas_un = [1000] * 12

    # 2. Vendas Reais: Sazonalidade do setor moveleiro + queda por juros altos (Total: 10.180 móveis)
    vendas_reais_un = [720, 680, 750, 780, 820, 800, 840, 860, 890, 940, 1080, 1020]

    # 3. Preço Médio de Venda e Custos Operacionais Base
    preco_venda_orcado = 1500.00
    preco_venda_real = 1485.00
    custo_mp_unit = 520.00
    custo_mod_unit = 230.00
    custo_cif_var_unit = 110.00
    custo_cif_fixo_mensal = 90000.00
    despesas_fixas_adm_com = 165000.00
    aliquota_impostos_comissoes = 0.14

    # 4. Cronograma de Desembolso de CAPEX no 1º Semestre (Máquinas Concorrentes)
    capex_proj_a_mensal = [0, 400000, 400000, 300000, 0, 0, 0, 0, 0, 0, 0, 0]
    capex_proj_b_mensal = [0, 0, 350000, 350000, 250000, 0, 0, 0, 0, 0, 0, 0]

    # Fluxos de Caixa Anuais dos Projetos de CAPEX (Horizonte de 5 anos)
    fluxo_anual_proj_a = [-1100000.0, 380000.0, 410000.0, 440000.0, 460000.0, 490000.0]
    fluxo_anual_proj_b = [-950000.0, 290000.0, 305000.0, 315000.0, 320000.0, 325000.0]

    return {
        "meses": meses,
        "vendas_orcadas_un": vendas_orcadas_un,
        "vendas_reais_un": vendas_reais_un,
        "preco_venda_orcado": preco_venda_orcado,
        "preco_venda_real": preco_venda_real,
        "custo_mp_unit": custo_mp_unit,
        "custo_mod_unit": custo_mod_unit,
        "custo_cif_var_unit": custo_cif_var_unit,
        "custo_cif_fixo_mensal": custo_cif_fixo_mensal,
        "despesas_fixas_adm_com": despesas_fixas_adm_com,
        "aliquota_impostos_comissoes": aliquota_impostos_comissoes,
        "capex_proj_a_mensal": capex_proj_a_mensal,
        "capex_proj_b_mensal": capex_proj_b_mensal,
        "fluxo_anual_proj_a": fluxo_anual_proj_a,
        "fluxo_anual_proj_b": fluxo_anual_proj_b,
        "caixa_inicial": 550000.00,
        "estoque_inicial_real": 350,
    }


def run_simulation(
    estoque_inicial_sim: int,
    perc_estoque_min: float,
    aderencia_rolling_forecast: float,
    custo_var_unit_sim: float,
    taxa_custo_estocagem_mensal: float,
    cenario_capex: str,
    taxa_juros_curto_prazo_mensal: float,
) -> pd.DataFrame:
    """Executa a simulação de 12 meses comparando o Cenário Errado vs. Cenário Corrigido."""
    base = get_base_parameters()
    meses = base["meses"]
    v_orc = np.array(base["vendas_orcadas_un"], dtype=float)
    v_real = np.array(base["vendas_reais_un"], dtype=float)

    preco_orc = base["preco_venda_orcado"]
    preco_real = base["preco_venda_real"]
    cif_fixo = base["custo_cif_fixo_mensal"]
    desp_fixa = base["despesas_fixas_adm_com"]
    aliq_var = base["aliquota_impostos_comissoes"]
    custo_var_real = base["custo_mp_unit"] + base["custo_mod_unit"] + base["custo_cif_var_unit"]

    # A. DINÂMICA REALIZADA (O ERRO DA EMPRESA: Produção = Vendas Orçadas = 1.000/mês)
    prod_errada = v_orc.copy()
    est_ini_errado = np.zeros(12)
    est_fim_errado = np.zeros(12)
    curr_est_err = float(base["estoque_inicial_real"])

    for m in range(12):
        est_ini_errado[m] = curr_est_err
        est_fim_errado[m] = curr_est_err + prod_errada[m] - v_real[m]
        curr_est_err = est_fim_errado[m]

    # B. DINÂMICA CORRIGIDA PELO PCP (Equação: Produção = Vendas Previstas + EF_desejado - EI)
    v_prevista_pcp = (1.0 - aderencia_rolling_forecast) * v_orc + aderencia_rolling_forecast * v_real

    prod_correta = np.zeros(12)
    est_ini_correto = np.zeros(12)
    est_fim_desejado = np.zeros(12)
    est_fim_correto_real = np.zeros(12)

    curr_est_ok = float(estoque_inicial_sim)
    for m in range(12):
        est_ini_correto[m] = curr_est_ok
        prox_venda = v_prevista_pcp[m + 1] if m < 11 else v_prevista_pcp[m]
        ef_meta = round(prox_venda * perc_estoque_min)
        est_fim_desejado[m] = ef_meta

        prod_req = max(0.0, round(v_prevista_pcp[m] + ef_meta - curr_est_ok))
        prod_correta[m] = prod_req

        est_fim_correto_real[m] = max(0.0, curr_est_ok + prod_req - v_real[m])
        curr_est_ok = est_fim_correto_real[m]

    # C. ORÇAMENTO DE CAIXA, CAPEX E EMPRÉSTIMOS DE CURTO PRAZO
    capex_a = np.array(base["capex_proj_a_mensal"], dtype=float)
    capex_b = np.array(base["capex_proj_b_mensal"], dtype=float)
    capex_erro_ambos = capex_a + capex_b

    if "Ambos" in cenario_capex or "Simultâneos" in cenario_capex:
        capex_sim = capex_erro_ambos.copy()
    elif "Projeto A" in cenario_capex:
        capex_sim = capex_a.copy()
    elif "Projeto B" in cenario_capex:
        capex_sim = capex_b.copy()
    else:
        capex_sim = np.zeros(12)

    receita_orcada = v_orc * preco_orc
    receita_real = v_real * preco_real

    custo_unit_total_orc = custo_var_real + (cif_fixo / 1000.0)
    capital_giro_imob_errado = est_fim_errado * custo_unit_total_orc
    capital_giro_imob_correto = est_fim_correto_real * custo_var_unit_sim

    custo_estocagem_errado = capital_giro_imob_errado * taxa_custo_estocagem_mensal
    custo_estocagem_correto = capital_giro_imob_correto * taxa_custo_estocagem_mensal

    saldo_caixa_real_antes_juros = np.zeros(12)
    juros_curto_prazo_real = np.zeros(12)
    saldo_caixa_real_final = np.zeros(12)

    saldo_caixa_sim_antes_juros = np.zeros(12)
    juros_curto_prazo_sim = np.zeros(12)
    saldo_caixa_sim_final = np.zeros(12)

    caixa_acum_real = base["caixa_inicial"]
    caixa_acum_sim = base["caixa_inicial"]

    economia_op_proj_a = np.array([0, 0, 0, 0, 28000, 32000, 32000, 34000, 34000, 35000, 35000, 35000], dtype=float)
    economia_op_proj_b = np.array([0, 0, 0, 0, 0, 22000, 24000, 24000, 25000, 25000, 25000, 25000], dtype=float)

    for m in range(12):
        entradas_real = receita_real[m]
        saidas_op_real = (
            (prod_errada[m] * custo_var_real)
            + cif_fixo
            + desp_fixa
            + (receita_real[m] * aliq_var)
            + custo_estocagem_errado[m]
        )
        fluxo_liq_real = entradas_real - saidas_op_real - capex_erro_ambos[m] + (economia_op_proj_a[m] * 0.75)

        juros_mes_real = abs(caixa_acum_real) * taxa_juros_curto_prazo_mensal if caixa_acum_real < 0 else 0.0
        juros_curto_prazo_real[m] = juros_mes_real
        saldo_caixa_real_antes_juros[m] = caixa_acum_real + fluxo_liq_real
        caixa_acum_real = saldo_caixa_real_antes_juros[m] - juros_mes_real
        saldo_caixa_real_final[m] = caixa_acum_real

        entradas_sim = receita_real[m]
        saidas_op_sim = (
            (prod_correta[m] * (custo_var_unit_sim - 90.0))
            + cif_fixo
            + desp_fixa
            + (receita_real[m] * aliq_var)
            + custo_estocagem_correto[m]
        )
        if "Projeto A" in cenario_capex or "Simultâneos" in cenario_capex:
            benef_capex = economia_op_proj_a[m]
        elif "Projeto B" in cenario_capex:
            benef_capex = economia_op_proj_b[m]
        else:
            benef_capex = 0.0

        fluxo_liq_sim = entradas_sim - saidas_op_sim - capex_sim[m] + benef_capex
        juros_mes_sim = abs(caixa_acum_sim) * taxa_juros_curto_prazo_mensal if caixa_acum_sim < 0 else 0.0
        juros_curto_prazo_sim[m] = juros_mes_sim
        saldo_caixa_sim_antes_juros[m] = caixa_acum_sim + fluxo_liq_sim
        caixa_acum_sim = saldo_caixa_sim_antes_juros[m] - juros_mes_sim
        saldo_caixa_sim_final[m] = caixa_acum_sim

    df = pd.DataFrame(
        {
            "Mês": meses,
            "Vendas_Orcadas_Un": v_orc.astype(int),
            "Vendas_Reais_Un": v_real.astype(int),
            "Vendas_Previstas_PCP_Un": np.round(v_prevista_pcp).astype(int),
            "Desvio_Vendas_Un": (v_real - v_orc).astype(int),
            "Desvio_Vendas_Perc": ((v_real - v_orc) / v_orc) * 100.0,
            "Receita_Orcada": receita_orcada,
            "Receita_Real": receita_real,
            "Desvio_Receita": receita_real - receita_orcada,
            "Est_Inicial_Errado_Un": est_ini_errado.astype(int),
            "Producao_Errada_Un": prod_errada.astype(int),
            "Est_Final_Errado_Un": est_fim_errado.astype(int),
            "Capital_Imobilizado_Errado": capital_giro_imob_errado,
            "Custo_Estocagem_Errado": custo_estocagem_errado,
            "Est_Inicial_Correto_Un": est_ini_correto.astype(int),
            "Est_Final_Meta_Un": est_fim_desejado.astype(int),
            "Producao_Correta_Un": prod_correta.astype(int),
            "Est_Final_Correto_Un": est_fim_correto_real.astype(int),
            "Capital_Imobilizado_Correto": capital_giro_imob_correto,
            "Custo_Estocagem_Correto": custo_estocagem_correto,
            "CAPEX_Real_Ambos": capex_erro_ambos,
            "CAPEX_Simulado": capex_sim,
            "Juros_Curto_Prazo_Real": juros_curto_prazo_real,
            "Saldo_Caixa_Real": saldo_caixa_real_final,
            "Juros_Curto_Prazo_Sim": juros_curto_prazo_sim,
            "Saldo_Caixa_Simulado": saldo_caixa_sim_final,
        }
    )
    return df


def render_mermaid_diagram(mermaid_code: str, height: int = 580) -> None:
    """Renderiza um diagrama Mermaid.js no Streamlit."""
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 12px;
                background-color: #ffffff;
                border-radius: 10px;
                font-family: 'Segoe UI', Roboto, Helvetica, sans-serif;
                display: flex;
                justify-content: center;
            }}
            .mermaid {{ width: 100%; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="mermaid">{mermaid_code}</div>
        <script>
            mermaid.initialize({{
                startOnLoad: true,
                theme: 'base',
                themeVariables: {{
                    primaryColor: '#dbeafe',
                    primaryTextColor: '#1e3a8a',
                    primaryBorderColor: '#2563eb',
                    lineColor: '#475569',
                    secondaryColor: '#dcfce7',
                    tertiaryColor: '#fef3c7'
                }}
            }});
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=height, scrolling=True)


# ==============================================================================
# 4. BARRA LATERAL (SIDEBAR) — SIMPLES E INTUITIVA + AJUSTE FINO OPCIONAL
# ==============================================================================
with st.sidebar:
    st.markdown("## 🧭 Painel de Controle")

    modo_leigo = st.toggle(
        "💡 Explicação Simples (Para Leigos)",
        value=True,
        help="Ativa caixas explicativas em linguagem do dia a dia (sem 'economês') em todas as abas e mostra um dicionário rápido de termos.",
    )

    st.markdown("### ⚡ 1. Escolha um Cenário Rápido")
    perfil_rapido = st.radio(
        "Como você quer simular a fábrica?",
        options=[
            "🟢 Fábrica Corrigida (Solução do Controller)",
            "🔴 Fábrica com Erros (O que aconteceu no caso)",
            "🛠️ Personalizar Manualmente (Usar controles abaixo)",
        ],
        index=0,
        help="Troque com 1 clique entre a fábrica quebrada e a fábrica consertada, ou escolha 'Personalizar' para mexer nos números livremente.",
    )

    with st.expander("🎚️ 2. Ajustar Números Manualmente", expanded=(perfil_rapido.startswith("🛠️"))):
        if perfil_rapido.startswith("🟢"):
            default_ei, default_min, default_rf, default_capex_idx = 350, 15, 100, 0
        elif perfil_rapido.startswith("🔴"):
            default_ei, default_min, default_rf, default_capex_idx = 0, 0, 0, 1
        else:
            default_ei, default_min, default_rf, default_capex_idx = 350, 15, 100, 0

        estoque_inicial_sim = st.slider(
            "Móveis já prontos no galpão em 1º de Jan (Estoque Inicial)",
            min_value=0,
            max_value=800,
            value=default_ei,
            step=25,
            help="Quantos móveis já estavam prontos antes do ano começar. Na vida real havia 350 móveis, mas a fábrica esqueceu de descontá-los.",
        )
        perc_estoque_min = (
            st.slider(
                "Reserva de segurança desejada no galpão (% das vendas)",
                min_value=0,
                max_value=40,
                value=default_min,
                step=5,
                help="Quantos % das vendas do mês seguinte queremos deixar guardados no estoque para não faltar produto.",
            )
            / 100.0
        )
        aderencia_rolling = (
            st.slider(
                "Ajustar produção quando a venda cair (% Revisão)",
                min_value=0,
                max_value=100,
                value=default_rf,
                step=10,
                help="0% = Continua fabricando 1.000 móveis por mês de olhos fechados. 100% = Ajusta a produção conforme as vendas reais do mercado.",
            )
            / 100.0
        )
        cenario_capex = st.selectbox(
            "Qual máquina comprar? (Investimento / CAPEX)",
            options=[
                "Decisão Ótima: Apenas Projeto A (R$ 1,10M)",
                "Erro Real: Projeto A + B Simultâneos (R$ 2,05M)",
                "Alternativa: Apenas Projeto B (R$ 0,95M)",
                "Conservador: Postergar CAPEX (R$ 0,00)",
            ],
            index=default_capex_idx,
            help="As máquinas A e B fazem a mesma função. Comprar as duas juntas foi um desperdício de R$ 950 mil.",
        )
        tma_wacc_anual = (
            st.slider(
                "Retorno mínimo exigido pela empresa — TMA (% ao ano)",
                min_value=8.0,
                max_value=24.0,
                value=14.0,
                step=0.5,
            )
            / 100.0
        )
        taxa_juros_cp_mensal = (
            st.slider(
                "Juros do banco no Cheque Especial (% ao mês)",
                min_value=1.0,
                max_value=4.5,
                value=2.45,
                step=0.05,
            )
            / 100.0
        )
        custo_unit_sim = 950.0
        taxa_estocagem_sim = 0.022

    st.divider()
    st.markdown(
        "**Autor:** Caio Lucas Siqueira  \n"
        "🔗 [LinkedIn](https://www.linkedin.com/in/caio-lucas-siqueira-7py)"
    )

# Executa a simulação com os parâmetros ativos
df_sim = run_simulation(
    estoque_inicial_sim=estoque_inicial_sim,
    perc_estoque_min=perc_estoque_min,
    aderencia_rolling_forecast=aderencia_rolling,
    custo_var_unit_sim=custo_unit_sim,
    taxa_custo_estocagem_mensal=taxa_estocagem_sim,
    cenario_capex=cenario_capex,
    taxa_juros_curto_prazo_mensal=taxa_juros_cp_mensal,
)

csv_bytes = df_sim.to_csv(index=False).encode("utf-8-sig")
st.sidebar.download_button(
    label="📥 Baixar Planilha dos 12 Meses (.CSV)",
    data=csv_bytes,
    file_name="simulacao_orcamentaria_moveis_vanguarda.csv",
    mime="text/csv",
    use_container_width=True,
)


# ==============================================================================
# 5. CABEÇALHO PRINCIPAL, HISTÓRIA EM 1 MINUTO E GLOSSÁRIO PARA LEIGOS
# ==============================================================================
st.title("🪑 Gestão Financeira e Orçamentária — Fábrica de Móveis")

if modo_leigo:
    st.markdown(
        """
        <div class="simple-box">
            <h4 style="margin-top:0;">📖 Entenda a História deste Projeto em 1 Minuto (Sem "Economês")</h4>
            Imagine uma <strong>fábrica de móveis</strong> que cometeu <strong>4 erros básicos de planejamento</strong> no ano passado:
            <ol style="margin-bottom:8px;">
                <li><strong>Achou que ia vender igual ao ano anterior:</strong> Planejou vender <strong>1.000 móveis todo mês</strong>, mas como os juros subiram, os clientes compraram bem menos (cerca de 700 a 850 por mês).</li>
                <li><strong>Fabricou móveis sem olhar para o galpão:</strong> Mesmo vendendo menos e já tendo <strong>350 móveis prontos</strong> guardados no galpão, a fábrica teimou em produzir 1.000 móveis por mês. O depósito entupiu com <strong>2.170 móveis encalhados (R$ 2 milhões parados em caixas!)</strong>.</li>
                <li><strong>Comprou duas máquinas iguais sem ter dinheiro:</strong> A empresa precisava modernizar a fábrica e tinha duas opções de máquinas concorrentes (Projeto A ou Projeto B). Em vez de escolher só a melhor, a diretoria <strong>comprou as duas ao mesmo tempo</strong>, gastando R$ 2,05 milhões de uma vez.</li>
                <li><strong>Entrou no Cheque Especial e só olhou a conta no fim do ano:</strong> Faltou dinheiro para pagar madeira e salários, a conta bancária ficou <strong>9 meses no vermelho</strong> pagando juros altíssimos, e ninguém corrigiu a rota durante o ano.</li>
            </ol>
            👉 <strong>O que este aplicativo faz?</strong> Nas 4 abas abaixo, mostramos o tamanho do rombo e como o <strong>Controller (gestor financeiro)</strong> conserta cada um desses problemas!
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("📘 Dicionário Rápido: Traduzindo as Siglas de Finanças para o Português Claro"):
        col_dic1, col_dic2 = st.columns(2)
        with col_dic1:
            st.markdown(
                """
                * **Orçamento (*Master Budget*):** É o planejamento financeiro completo da empresa para os 12 meses do ano (quanto vai vender, produzir, gastar e investir).
                * **PCP (Planejamento e Controle da Produção):** É a conta simples que define quantos móveis a fábrica realmente precisa fabricar para não faltar nem sobrar produto no galpão.
                * **Capital de Giro / NCG:** É o dinheiro vivo que a empresa precisa para funcionar no dia a dia (pagar madeira, funcionários e luz antes de receber dos clientes). Quando você fabrica móveis que não vendem, seu dinheiro fica "preso" dentro das caixas no estoque.
                """
            )
        with col_dic2:
            st.markdown(
                """
                * **CAPEX (Orçamento de Capital):** Dinheiro gasto na compra de bens grandes de longo prazo, como máquinas novas ou ampliação do galpão.
                * **VPL (Valor Presente Líquido):** Mostra quantos reais de riqueza líquida uma máquina nova vai dar de lucro para a empresa (já descontando o preço dela e os juros do período). **Regra simples: quanto maior o VPL positivo, melhor o projeto!**
                * **TIR (Taxa Interna de Retorno):** É a rentabilidade em `% ao ano` que o investimento rende. Para valer a pena, a TIR precisa ser maior que a taxa mínima que a empresa exige (**TMA / WACC**).
                * **Rolling Forecast (Revisão Contínua):** Em vez de seguir um plano errado até dezembro, é revisar a meta a cada trimestre conforme a realidade do mercado.
                """
            )
else:
    st.markdown(
        """
        <div class="exec-banner">
            <strong>Estudo de Caso Executivo — Indústria Moveleira Vanguarda S.A.</strong><br/>
            Diagnóstico quantitativo de desvios do <em>Master Budget</em>, Simulador de Planejamento e Controle da Produção (PCP),
            Avaliação de Viabilidade Econômica de CAPEX (VPL, TIR e IL) e Controle Matricial de Variações.
        </div>
        """,
        unsafe_allow_html=True,
    )

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📋 Aba 1 — O Problema Geral & Parecer",
        "🏭 Aba 2 — Consertando a Produção (Estoque)",
        "💰 Aba 3 — Consertando o Caixa & Máquinas (CAPEX)",
        "🎯 Aba 4 — Onde o Dinheiro Sumiu? (Orçado vs Real)",
    ]
)


# ==============================================================================
# ABA 1: VISÃO GERAL E PARECER EXECUTIVO
# ==============================================================================
with tab1:
    st.subheader("📌 Fotografia do Problema: O que aconteceu na Fábrica no Ano?")

    if modo_leigo:
        st.info(
            "👀 **Como ler esta aba:** Os 4 cartões abaixo mostram o resumo da crise da fábrica. "
            "No gráfico logo em seguida, repare como as **barras azuis (vendas reais)** ficaram abaixo das **barras cinzas (o que a fábrica produziu)**, "
            "fazendo a **linha vermelha (móveis encalhados no galpão)** disparar até 2.170 unidades!"
        )

    receita_orc_total = df_sim["Receita_Orcada"].sum()
    receita_real_total = df_sim["Receita_Real"].sum()
    desvio_receita_total = receita_real_total - receita_orc_total
    desvio_receita_perc = (desvio_receita_total / receita_orc_total) * 100.0

    vendas_orc_total = df_sim["Vendas_Orcadas_Un"].sum()
    vendas_real_total = df_sim["Vendas_Reais_Un"].sum()

    estoque_final_dez_errado = int(df_sim["Est_Final_Errado_Un"].iloc[-1])
    capital_imob_dez_errado = df_sim["Capital_Imobilizado_Errado"].iloc[-1]

    juros_totais_real = df_sim["Juros_Curto_Prazo_Real"].sum()
    saldo_caixa_min_real = df_sim["Saldo_Caixa_Real"].min()

    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    with col_kpi1:
        st.metric(
            label="1. Faturamento Real (Vendas em R$)",
            value=format_brl(receita_real_total),
            delta=f"{desvio_receita_perc:.1f}% ({format_brl(desvio_receita_total)} abaixo da meta)",
            delta_color="normal",
            help=f"Meta planejada: {format_brl(receita_orc_total)} | Venda real: {format_brl(receita_real_total)}.",
        )
    with col_kpi2:
        st.metric(
            label="2. Móveis Vendidos no Ano",
            value=f"{format_int_br(vendas_real_total)} móveis",
            delta=f"{format_int_br(vendas_real_total - vendas_orc_total)} móveis a menos que os 12.000 planejados",
            delta_color="normal",
        )
    with col_kpi3:
        st.metric(
            label="3. Móveis Encalhados no Galpão (Dez)",
            value=f"{format_int_br(estoque_final_dez_errado)} móveis",
            delta=f"Dinheiro parado: {format_brl(capital_imob_dez_errado)}",
            delta_color="inverse",
        )
    with col_kpi4:
        st.metric(
            label="4. Juros Pagos ao Banco (Cheque Especial)",
            value=format_brl(juros_totais_real),
            delta=f"Pior saldo no banco: {format_brl(saldo_caixa_min_real)}",
            delta_color="inverse",
        )

    st.markdown("---")

    col_left, col_right = st.columns([1.35, 1.0])

    with col_left:
        st.markdown("#### 📉 Por que o galpão entupiu de móveis? (Mês a Mês)")
        fig_overview = make_subplots(specs=[[{"secondary_y": True}]])
        fig_overview.add_trace(
            go.Bar(
                x=df_sim["Mês"],
                y=df_sim["Vendas_Orcadas_Un"],
                name="O que a Fábrica Produziu (1.000/mês)",
                marker_color="rgba(148, 163, 184, 0.55)",
            ),
            secondary_y=False,
        )
        fig_overview.add_trace(
            go.Bar(
                x=df_sim["Mês"],
                y=df_sim["Vendas_Reais_Un"],
                name="O que Realmente Vendeu",
                marker_color="#2563eb",
            ),
            secondary_y=False,
        )
        fig_overview.add_trace(
            go.Scatter(
                x=df_sim["Mês"],
                y=df_sim["Est_Final_Errado_Un"],
                name="Móveis Acumulados no Galpão",
                mode="lines+markers",
                line=dict(color="#ef4444", width=3),
                marker=dict(size=8),
            ),
            secondary_y=True,
        )
        fig_overview.update_layout(
            barmode="group",
            height=390,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        fig_overview.update_yaxes(title_text="Móveis por Mês (Produção vs Venda)", secondary_y=False)
        fig_overview.update_yaxes(title_text="Total Acumulado no Galpão", secondary_y=True)
        st.plotly_chart(fig_overview, use_container_width=True)

    with col_right:
        st.markdown("#### 🔍 Os 5 Erros Explicados de Forma Direta")
        st.markdown(
            """
            <div class="diagnosis-card">
                <strong>1. Meta de Vendas "Ctrl+C / Ctrl+V":</strong>
                O setor comercial apenas copiou as vendas do ano anterior (1.000 móveis/mês), esquecendo que no começo do ano (IPTU/IPVA) e com juros altos as pessoas compram menos móveis.
            </div>
            <div class="diagnosis-card">
                <strong>2. Produção Cega (Produção = Vendas):</strong>
                A fábrica ignorou os 350 móveis que já estavam prontos e fabricou 1.000 todo mês. Sobraram <strong>2.170 móveis</strong> nas prateleiras.
            </div>
            <div class="diagnosis-card">
                <strong>3. Conta no Vermelho e Empréstimos Caros:</strong>
                Para fabricar móveis que ninguém estava comprando, gastou-se muito com madeira e salários, empurrando a empresa para empréstimos bancários caros.
            </div>
            <div class="diagnosis-card">
                <strong>4. Compra de Duas Máquinas Concorrentes:</strong>
                Sem dinheiro sobrando, a diretoria aprovou 2 projetos de máquinas que fazem o mesmo serviço (gastando R$ 2,05 milhões).
            </div>
            <div class="diagnosis-card">
                <strong>5. Descontrole Durante o Ano:</strong>
                Ninguém acompanhou as metas mês a mês; só descobriram o tamanho do prejuízo quando o ano acabou.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.subheader("📑 Trabalho Acadêmico Completo (Parecer Técnico de Controladoria)")
    st.caption(
        "Esta seção contém o documento formal exigido pela disciplina universitária (com citações ABNT, fórmulas e diagrama técnico)."
    )

    parecer_path = Path(__file__).parent / "PARECER_TECNICO_CONTROLADORIA.md"
    if parecer_path.exists():
        parecer_content = parecer_path.read_text(encoding="utf-8")

        col_dl1, col_dl2 = st.columns([3, 1])
        with col_dl1:
            st.write("Clique nos blocos abaixo para abrir o fluxograma do orçamento ou ler o trabalho acadêmico completo:")
        with col_dl2:
            st.download_button(
                label="📄 Baixar Trabalho Acadêmico (.MD)",
                data=parecer_content.encode("utf-8"),
                file_name="PARECER_TECNICO_CONTROLADORIA.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with st.expander("🗺️ Abrir Fluxograma Visual do Orçamento Empresarial (Master Budget)", expanded=False):
            mermaid_master_budget = """
            flowchart TD
                subgraph Est_Merc["1. Premissas Estrategicas e Mercado"]
                    MACRO["Cenario Macroeconomico, Juros, Credito e Sazonalidade"]
                    VENDAS["ORCAMENTO DE VENDAS<br/>(Ponto de Partida: Volume, Mix e Preco)"]
                    MACRO --> VENDAS
                end
                subgraph Orc_Oper["2. Orcamento Operacional e Industrial"]
                    POL_EST["Politica de Estoques (EI e EF Desejado)<br/>e Capacidade Instalada"]
                    PROD["ORCAMENTO DE PRODUCAO (PCP)<br/>Prod = Vendas + EF - EI"]
                    MP["Orcamento de Materia-Prima (MP)<br/>Consumo e Compras (BOM)"]
                    MOD["Orcamento de Mao de Obra Direta (MOD)<br/>Horas-Homem e Encargos"]
                    CIF["Orcamento de Custos Indiretos (CIF)<br/>Fixos e Variaveis de Fabricacao"]
                    CPV["Orcamento de CPV e Estoque Final"]
                    DESP["Orcamento de Despesas Operacionais<br/>(Comerciais, Fretes, Comissoes, G&A)"]
                    VENDAS -->|Demanda Prevista| PROD
                    POL_EST --> PROD
                    PROD --> MP & MOD & CIF
                    MP & MOD & CIF --> CPV
                    VENDAS -->|Comissoes e Fretes| DESP
                end
                subgraph Orc_Cap["3. Orcamento de Capital"]
                    CAPEX["ORCAMENTO DE CAPITAL (CAPEX)<br/>Analise VPL, TIR e IL sob Restricao"]
                    VENDAS -.->|Expansao de Capacidade| CAPEX
                end
                subgraph Orc_Fin["4. Consolidacao Financeira e Controle"]
                    CAIXA["ORCAMENTO DE CAIXA<br/>Ciclo Financeiro: PME + PMR - PMP"]
                    DRE["DRE Projetada<br/>(Regime de Competencia)"]
                    BP["Balanco Patrimonial Projetado"]
                    CTRL["CONTROLE ORCAMENTARIO MATRICIAL<br/>Analise de Variacoes e Rolling Forecast"]
                    VENDAS -->|Recebimentos PMR| CAIXA
                    MP -->|Fornecedores PMP| CAIXA
                    MOD & CIF & DESP & CAPEX -->|Desembolsos| CAIXA
                    VENDAS & CPV & DESP --> DRE
                    CAIXA & DRE & CAPEX --> BP
                    CAIXA & DRE & BP --> CTRL
                    CTRL -.->|Rolling Forecast e S&OP| VENDAS & PROD
                end
            """
            render_mermaid_diagram(mermaid_master_budget, height=580)

        with st.expander("📖 Ler o Texto Completo do Parecer Técnico Acadêmico (Itens A, B, C e D)", expanded=False):
            st.markdown(parecer_content)


# ==============================================================================
# ABA 2: SIMULADOR DE PRODUÇÃO E ESTOQUES (PCP)
# ==============================================================================
with tab2:
    st.subheader("🏭 Como Consertar a Produção para Não Entupir o Galpão")

    if modo_leigo:
        st.info(
            "💡 **A Lógica Simples desta Aba:** Se você vai dar uma festa para **100 pessoas**, quer deixar **10 refrigerantes de reserva** "
            "na geladeira, mas abre a despensa e vê que **já tem 30 refrigerantes guardados**, quantos você precisa comprar? "
            "Apenas **80** ($100 + 10 - 30 = 80$)! A fábrica de móveis errou porque comprou os 100 sem olhar a despensa. "
            "Veja abaixo como essa conta simples economiza **R$ 1,91 milhão**!"
        )

    st.markdown(
        """
        <div class="formula-box">
            <strong>Fórmula Correta do que Fabricar no Mês (PCP):</strong><br/>
            <span style="font-size: 1.15rem;">
                <code>O que Produzir = Vendas Previstas + Reserva Desejada no Fim do Mês − O que Já Tem no Galpão</code>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    prod_errada_anual = int(df_sim["Producao_Errada_Un"].sum())
    prod_correta_anual = int(df_sim["Producao_Correta_Un"].sum())
    reducao_producao_un = prod_errada_anual - prod_correta_anual

    est_final_errado_dez = int(df_sim["Est_Final_Errado_Un"].iloc[-1])
    est_final_correto_dez = int(df_sim["Est_Final_Correto_Un"].iloc[-1])

    cap_imob_errado_dez = df_sim["Capital_Imobilizado_Errado"].iloc[-1]
    cap_imob_correto_dez = df_sim["Capital_Imobilizado_Correto"].iloc[-1]
    capital_giro_liberado = cap_imob_errado_dez - cap_imob_correto_dez

    economia_estocagem_anual = df_sim["Custo_Estocagem_Errado"].sum() - df_sim["Custo_Estocagem_Correto"].sum()

    c_pcp1, c_pcp2, c_pcp3, c_pcp4 = st.columns(4)
    with c_pcp1:
        st.metric(
            label="Produção Inteligente no Ano",
            value=f"{format_int_br(prod_correta_anual)} móveis",
            delta=f"{format_int_br(-reducao_producao_un)} móveis fabricados sem necessidade",
            delta_color="normal",
        )
    with c_pcp2:
        st.metric(
            label="Estoque no Galpão em Dezembro",
            value=f"{format_int_br(est_final_correto_dez)} móveis",
            delta=f"-{format_int_br(est_final_errado_dez - est_final_correto_dez)} móveis encalhados (vs. {format_int_br(est_final_errado_dez)})",
            delta_color="normal",
        )
    with c_pcp3:
        st.metric(
            label="Dinheiro Destravado do Galpão",
            value=format_brl(capital_giro_liberado),
            delta="Capital de Giro que volta para o caixa da empresa",
            delta_color="normal",
        )
    with c_pcp4:
        st.metric(
            label="Economia de Galpão, Seguro e Perdas",
            value=format_brl(economia_estocagem_anual),
            delta="Gasto evitado com armazenagem excessiva",
            delta_color="normal",
        )

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("#### 🔧 Quantos móveis fabricar por mês: Jeito Errado (Vermelho) vs. Jeito Certo (Verde)")
        fig_prod = go.Figure()
        fig_prod.add_trace(
            go.Bar(
                x=df_sim["Mês"],
                y=df_sim["Producao_Errada_Un"],
                name="Jeito Errado (1.000/mês fixo)",
                marker_color="rgba(239, 68, 68, 0.70)",
            )
        )
        fig_prod.add_trace(
            go.Bar(
                x=df_sim["Mês"],
                y=df_sim["Producao_Correta_Un"],
                name="Jeito Certo (Calculado pelo PCP)",
                marker_color="#10b981",
            )
        )
        fig_prod.add_trace(
            go.Scatter(
                x=df_sim["Mês"],
                y=df_sim["Vendas_Reais_Un"],
                name="Vendas Reais dos Clientes",
                mode="lines+markers",
                line=dict(color="#2563eb", width=3, dash="dot"),
            )
        )
        fig_prod.update_layout(
            barmode="group",
            height=400,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            yaxis_title="Quantidade de Móveis",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_prod, use_container_width=True)

    with col_g2:
        st.markdown("#### 📦 Móveis Acumulados no Galpão: Montanha de Estoque (Vermelho) vs. Estoque Enxuto (Verde)")
        fig_est = go.Figure()
        fig_est.add_trace(
            go.Scatter(
                x=df_sim["Mês"],
                y=df_sim["Est_Final_Errado_Un"],
                name="Galpão Lotado (Jeito Errado)",
                mode="lines+markers",
                fill="tozeroy",
                fillcolor="rgba(239, 68, 68, 0.15)",
                line=dict(color="#ef4444", width=3),
            )
        )
        fig_est.add_trace(
            go.Scatter(
                x=df_sim["Mês"],
                y=df_sim["Est_Final_Correto_Un"],
                name="Galpão sob Controle (Jeito Certo)",
                mode="lines+markers",
                fill="tozeroy",
                fillcolor="rgba(16, 185, 129, 0.20)",
                line=dict(color="#10b981", width=3),
            )
        )
        fig_est.add_trace(
            go.Scatter(
                x=df_sim["Mês"],
                y=df_sim["Est_Final_Meta_Un"],
                name=f"Meta de Reserva ({int(perc_estoque_min * 100)}%)",
                mode="lines",
                line=dict(color="#f59e0b", width=2, dash="dash"),
            )
        )
        fig_est.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            yaxis_title="Móveis Guardados no Galpão",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_est, use_container_width=True)

    with st.expander("📋 Ver Tabela Mês a Mês da Conta de Produção (PCP)", expanded=False):
        df_pcp_table = pd.DataFrame(
            {
                "Mês": df_sim["Mês"],
                "Meta Antiga (un.)": df_sim["Vendas_Orcadas_Un"],
                "Vendas Reais (un.)": df_sim["Vendas_Reais_Un"],
                "Já Tinha no Galpão - EI (un.)": df_sim["Est_Inicial_Correto_Un"],
                "Reserva Desejada - EF (un.)": df_sim["Est_Final_Meta_Un"],
                "Quanto Fabricar - PCP (un.)": df_sim["Producao_Correta_Un"],
                "Estoque no Jeito Certo (un.)": df_sim["Est_Final_Correto_Un"],
                "Estoque no Jeito Errado (un.)": df_sim["Est_Final_Errado_Un"],
                "Dinheiro Economizado no Mês (R$)": (
                    df_sim["Capital_Imobilizado_Errado"] - df_sim["Capital_Imobilizado_Correto"]
                ).apply(format_brl),
            }
        )
        st.dataframe(df_pcp_table, use_container_width=True, hide_index=True)


# ==============================================================================
# ABA 3: ORÇAMENTO DE CAIXA & CAPEX (VPL / TIR / IL)
# ==============================================================================
with tab3:
    st.subheader("💰 Como Tirar a Conta Bancária do Vermelho e Escolher a Máquina Certa")

    if modo_leigo:
        st.info(
            "💡 **A Lógica Simples desta Aba:** A fábrica tinha duas propostas de máquinas para fazer o mesmo trabalho de corte de madeira: "
            "o **Projeto A (R$ 1,10 milhão)** e o **Projeto B (R$ 950 mil)**. Como elas fazem a mesma coisa (são *concorrentes*), "
            "a empresa deveria ter escolhido **apenas a melhor (Projeto A)**. Ao comprar as duas juntas e produzir móveis demais, "
            "o saldo bancário afundou no cheque especial (**linha vermelha**). Com a correção (**linha verde**), a empresa fica no azul o ano todo!"
        )

    base_params = get_base_parameters()
    cf_a = base_params["fluxo_anual_proj_a"]
    cf_b = base_params["fluxo_anual_proj_b"]
    cf_ambos_erro = [
        cf_a[0] + cf_b[0],
        cf_a[1] * 0.92,
        cf_a[2] * 0.92,
        cf_a[3] * 0.92,
        cf_a[4] * 0.92,
        cf_a[5] * 0.92,
    ]

    vpl_a = calc_npv(tma_wacc_anual, cf_a)
    tir_a = calc_irr(cf_a)
    il_a = calc_profitability_index(tma_wacc_anual, cf_a)
    pb_a = calc_discounted_payback(tma_wacc_anual, cf_a)

    vpl_b = calc_npv(tma_wacc_anual, cf_b)
    tir_b = calc_irr(cf_b)
    il_b = calc_profitability_index(tma_wacc_anual, cf_b)
    pb_b = calc_discounted_payback(tma_wacc_anual, cf_b)

    vpl_ambos = calc_npv(tma_wacc_anual, cf_ambos_erro)
    tir_ambos = calc_irr(cf_ambos_erro)
    il_ambos = calc_profitability_index(tma_wacc_anual, cf_ambos_erro)
    pb_ambos = calc_discounted_payback(tma_wacc_anual, cf_ambos_erro)

    saldo_final_real = df_sim["Saldo_Caixa_Real"].iloc[-1]
    saldo_final_sim = df_sim["Saldo_Caixa_Simulado"].iloc[-1]
    juros_real_acum = df_sim["Juros_Curto_Prazo_Real"].sum()
    juros_sim_acum = df_sim["Juros_Curto_Prazo_Sim"].sum()
    economia_juros = juros_real_acum - juros_sim_acum

    c_cx1, c_cx2, c_cx3, c_cx4 = st.columns(4)
    with c_cx1:
        st.metric(
            label="Saldo no Banco em Dezembro (Simulado)",
            value=format_brl(saldo_final_sim),
            delta=f"+{format_brl(saldo_final_sim - saldo_final_real)} melhor que o caso real ({format_brl(saldo_final_real)})",
            delta_color="normal",
        )
    with c_cx2:
        st.metric(
            label="Gasto com Juros de Empréstimos",
            value=format_brl(juros_sim_acum),
            delta=f"Economia de {format_brl(economia_juros)} em juros bancários",
            delta_color="normal",
        )
    with c_cx3:
        st.metric(
            label="Lucro Líquido da Máquina A (VPL)",
            value=format_brl(vpl_a),
            delta=f"Rentabilidade (TIR): {tir_a * 100:.1f}% ao ano",
            delta_color="normal",
        )
    with c_cx4:
        st.metric(
            label="Prejuízo de Comprar A + B Juntas (VPL)",
            value=format_brl(vpl_ambos),
            delta="Comprar as duas máquinas dá prejuízo!",
            delta_color="inverse",
        )

    col_cx_left, col_cx_right = st.columns([1.25, 1.0])

    with col_cx_left:
        st.markdown("#### 📈 Dinheiro na Conta do Banco: O Buraco Real (Vermelho) vs. Conta Saudável (Verde)")
        fig_cash = go.Figure()
        fig_cash.add_hline(
            y=0,
            line_dash="dash",
            line_color="#ef4444",
            annotation_text="Linha Zero (Abaixo daqui a empresa entra no Cheque Especial)",
            annotation_position="top left",
        )
        fig_cash.add_trace(
            go.Scatter(
                x=df_sim["Mês"],
                y=df_sim["Saldo_Caixa_Real"],
                name="Conta Real (Produziu demais + Comprou 2 Máquinas)",
                mode="lines+markers",
                fill="tozeroy",
                fillcolor="rgba(239, 68, 68, 0.14)",
                line=dict(color="#ef4444", width=3),
                marker=dict(size=8),
            )
        )
        fig_cash.add_trace(
            go.Scatter(
                x=df_sim["Mês"],
                y=df_sim["Saldo_Caixa_Simulado"],
                name="Conta Consertada (Pela Controladoria)",
                mode="lines+markers",
                fill="tozeroy",
                fillcolor="rgba(16, 185, 129, 0.14)",
                line=dict(color="#10b981", width=3),
                marker=dict(size=8),
            )
        )
        fig_cash.update_layout(
            height=410,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            yaxis_title="Saldo Acumulado no Banco (R$)",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_cash, use_container_width=True)

    with col_cx_right:
        st.markdown("#### 🏆 Comparação Direta: Por que o Projeto A vence o Projeto B?")
        fig_comp_bar = go.Figure()
        fig_comp_bar.add_trace(
            go.Bar(
                x=["Projeto A (Máquina CNC)", "Projeto B (Semi-Automática)", "Erro: Comprar A + B Juntas"],
                y=[vpl_a, vpl_b, vpl_ambos],
                marker_color=["#10b981", "#3b82f6", "#ef4444"],
                text=[format_brl(vpl_a), format_brl(vpl_b), format_brl(vpl_ambos)],
                textposition="outside",
            )
        )
        fig_comp_bar.add_hline(y=0, line_dash="dot", line_color="gray")
        fig_comp_bar.update_layout(
            height=410,
            margin=dict(l=20, r=20, t=35, b=20),
            yaxis_title="Riqueza Gerada — VPL (R$)",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_comp_bar, use_container_width=True)

    st.markdown("#### 📊 Tabela Resumo para Decisão da Diretoria (Qual Máquina Escolher?)")
    df_capex_comp = pd.DataFrame(
        [
            {
                "Opção de Compra": "Projeto A — Máquina CNC Automatizada",
                "Preço da Máquina": format_brl(abs(cf_a[0])),
                "Lucro Líquido Gerado (VPL)": format_brl(vpl_a),
                "Rentabilidade Anual (TIR)": f"{tir_a * 100:.1f}% ao ano",
                "Retorno p/ Cada R$ 1 Gasto (IL)": f"R$ {il_a:.2f}",
                "Tempo p/ Se Pagar (Payback)": f"{pb_a:.1f} anos" if pb_a != float("inf") else "> 5 anos",
                "Decisão Correta": "✅ ESCOLHER ESTA (Dá quase 4x mais lucro que a B)",
            },
            {
                "Opção de Compra": "Projeto B — Máquina Semi-Automatizada",
                "Preço da Máquina": format_brl(abs(cf_b[0])),
                "Lucro Líquido Gerado (VPL)": format_brl(vpl_b),
                "Rentabilidade Anual (TIR)": f"{tir_b * 100:.1f}% ao ano",
                "Retorno p/ Cada R$ 1 Gasto (IL)": f"R$ {il_b:.2f}",
                "Tempo p/ Se Pagar (Payback)": f"{pb_b:.1f} anos" if pb_b != float("inf") else "> 5 anos",
                "Decisão Correta": "❌ DESCARTAR (Concorre com a Máquina A e rende menos)",
            },
            {
                "Opção de Compra": "ERRO DA EMPRESA — Comprar A + B Juntas",
                "Preço da Máquina": format_brl(abs(cf_ambos_erro[0])),
                "Lucro Líquido Gerado (VPL)": format_brl(vpl_ambos),
                "Rentabilidade Anual (TIR)": f"{tir_ambos * 100:.1f}% ao ano",
                "Retorno p/ Cada R$ 1 Gasto (IL)": f"R$ {il_ambos:.2f}",
                "Tempo p/ Se Pagar (Payback)": "Nunca se paga (> 5 anos)",
                "Decisão Correta": "🚫 ERRO GRAVE (Gasto duplicado que afundou o caixa)",
            },
        ]
    )
    st.dataframe(df_capex_comp, use_container_width=True, hide_index=True)


# ==============================================================================
# ABA 4: CONTROLE ORÇAMENTÁRIO (ORÇADO VS. REALIZADO & ANÁLISE DE VARIAÇÕES)
# ==============================================================================
with tab4:
    st.subheader("🎯 Onde o Lucro Planejado Sumiu e Quando o Controller Deveria Ter Agido?")

    if modo_leigo:
        st.info(
            "💡 **A Lógica Simples desta Aba:** A empresa esperava ter um **Lucro Operacional de R$ 2,10 milhões** no ano, "
            "mas na prática esse lucro derreteu para apenas **R$ 499 mil**. "
            "O gráfico da esquerda (*Cascata*) mostra degrau por degrau **quem comeu esse lucro** (queda de vendas, descontos, "
            "custo de galpão cheio e juros do banco). Já o gráfico da direita mostra **em quais meses o alarme deveria ter tocado**!"
        )

    base_p = get_base_parameters()
    custo_var_unit_base = base_p["custo_mp_unit"] + base_p["custo_mod_unit"] + base_p["custo_cif_var_unit"]
    aliq_imp = base_p["aliquota_impostos_comissoes"]
    custos_fixos_ano = (base_p["custo_cif_fixo_mensal"] + base_p["despesas_fixas_adm_com"]) * 12

    mc_unit_orc = (base_p["preco_venda_orcado"] * (1.0 - aliq_imp)) - custo_var_unit_base
    lucro_liq_orcado = (12000 * mc_unit_orc) - custos_fixos_ano

    var_volume_comercial = (vendas_real_total - 12000) * mc_unit_orc
    var_preco_comercial = (
        (base_p["preco_venda_real"] - base_p["preco_venda_orcado"]) * (1.0 - aliq_imp) * vendas_real_total
    )
    var_custo_estocagem = -df_sim["Custo_Estocagem_Errado"].sum()
    var_despesa_financeira_cp = -df_sim["Juros_Curto_Prazo_Real"].sum()

    lucro_liq_realizado = (
        lucro_liq_orcado
        + var_volume_comercial
        + var_preco_comercial
        + var_custo_estocagem
        + var_despesa_financeira_cp
    )
    lucro_liq_recuperado_sim = (
        lucro_liq_orcado
        + var_volume_comercial
        + var_preco_comercial
        - df_sim["Custo_Estocagem_Correto"].sum()
        - df_sim["Juros_Curto_Prazo_Sim"].sum()
    )

    c_ct1, c_ct2, c_ct3, c_ct4 = st.columns(4)
    with c_ct1:
        st.metric(
            label="1. Lucro que Era Esperado",
            value=format_brl(lucro_liq_orcado),
            delta="Meta original do início do ano",
        )
    with c_ct2:
        st.metric(
            label="2. Perda por Vender Menos Móveis",
            value=format_brl(var_volume_comercial),
            delta="-1.820 móveis que deixaram de ser vendidos",
            delta_color="inverse",
        )
    with c_ct3:
        st.metric(
            label="3. Lucro que Sobrou (Com os Erros)",
            value=format_brl(lucro_liq_realizado),
            delta=f"Encolheu {format_brl(lucro_liq_realizado - lucro_liq_orcado)}",
            delta_color="inverse",
        )
    with c_ct4:
        st.metric(
            label="4. Lucro Salvo pela Controladoria",
            value=format_brl(lucro_liq_recuperado_sim),
            delta=f"Recupera +{format_brl(lucro_liq_recuperado_sim - lucro_liq_realizado)} de lucro!",
            delta_color="normal",
        )

    col_w1, col_w2 = st.columns(2)

    with col_w1:
        st.markdown("#### 🌊 Escadinha do Resultado: Como R$ 2,10 Milhões Viraram R$ 499 Mil?")
        fig_waterfall = go.Figure(
            go.Waterfall(
                name="Decomposição",
                orientation="v",
                measure=["absolute", "relative", "relative", "relative", "relative", "total"],
                x=[
                    "1. Lucro Planejado",
                    "2. Queda nas Vendas",
                    "3. Descontos Dados",
                    "4. Custo Galpão Cheio",
                    "5. Juros do Banco",
                    "6. Lucro que Sobrou",
                ],
                textposition="outside",
                text=[
                    format_brl(lucro_liq_orcado),
                    format_brl(var_volume_comercial),
                    format_brl(var_preco_comercial),
                    format_brl(var_custo_estocagem),
                    format_brl(var_despesa_financeira_cp),
                    format_brl(lucro_liq_realizado),
                ],
                y=[
                    lucro_liq_orcado,
                    var_volume_comercial,
                    var_preco_comercial,
                    var_custo_estocagem,
                    var_despesa_financeira_cp,
                    0,
                ],
                connector={"line": {"color": "rgba(128, 128, 128, 0.5)"}},
                decreasing={"marker": {"color": "#ef4444"}},
                increasing={"marker": {"color": "#10b981"}},
                totals={"marker": {"color": "#2563eb"}},
            )
        )
        fig_waterfall.update_layout(
            height=430,
            margin=dict(l=20, r=20, t=35, b=20),
            yaxis_title="Impacto no Lucro do Ano (R$)",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_waterfall, use_container_width=True)

    with col_w2:
        st.markdown("#### 🚨 Alerta Mês a Mês: Quando o Controller Deveria Ter Apertado o Freio?")
        cores_desvio = [
            "#ef4444" if val < -150000 else "#f59e0b" if val < 0 else "#10b981" for val in df_sim["Desvio_Receita"]
        ]
        fig_desv = go.Figure()
        fig_desv.add_trace(
            go.Bar(
                x=df_sim["Mês"],
                y=df_sim["Desvio_Receita"],
                name="Diferença de Vendas no Mês (R$)",
                marker_color=cores_desvio,
                text=[f"{p:.1f}%" for p in df_sim["Desvio_Vendas_Perc"]],
                textposition="outside",
            )
        )
        fig_desv.add_annotation(
            x="Fev",
            y=df_sim["Desvio_Receita"].iloc[1],
            text="1º Freio (Fev):<br>Cancelar compra da Máquina B!",
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-45,
            bgcolor="rgba(239, 68, 68, 0.15)",
            bordercolor="#ef4444",
        )
        fig_desv.add_annotation(
            x="Mar",
            y=df_sim["Desvio_Receita"].iloc[2],
            text="2º Freio (Março):<br>Reduzir fabricação e compra de madeira!",
            showarrow=True,
            arrowhead=2,
            ax=20,
            ay=-65,
            bgcolor="rgba(37, 99, 235, 0.15)",
            bordercolor="#2563eb",
        )
        fig_desv.update_layout(
            height=430,
            margin=dict(l=20, r=20, t=35, b=20),
            yaxis_title="Faturamento Real vs. Meta Mensal (R$)",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_desv, use_container_width=True)

    st.markdown("#### 🧭 Resumo das 3 Ações Simples que Salvariam o Ano da Fábrica")
    c_sol1, c_sol2, c_sol3 = st.columns(3)
    with c_sol1:
        st.markdown(
            """
            <div class="solution-card">
                <strong>1️⃣ Em Fevereiro (Olhar o Painel Mensal):</strong><br/>
                Ao ver que Janeiro (-28%) e Fevereiro (-32%) venderam muito abaixo do esperado, cancelar na hora a compra da <strong>segunda máquina (Projeto B)</strong> antes de gastar R$ 950 mil em março.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c_sol2:
        st.markdown(
            """
            <div class="solution-card">
                <strong>2️⃣ Em Março (Ajustar a Rota / Rolling Forecast):</strong><br/>
                Parar de produzir 1.000 móveis no automático e reduzir as encomendas de madeira e ferragens para acompanhar o ritmo real de compras dos clientes.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c_sol3:
        st.markdown(
            """
            <div class="solution-card">
                <strong>3️⃣ O Ano Inteiro (Descontar o Estoque do Galpão):</strong><br/>
                Usar a fórmula correta de produção (descontando os 350 móveis que já estavam prontos), deixando **R$ 1,91 milhão livres** na conta da empresa e **zero dívida** no banco!
            </div>
            """,
            unsafe_allow_html=True,
        )
