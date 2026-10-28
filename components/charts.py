import pandas as pd
import plotly.express as px
import streamlit as st

from analytics import category_breakdown, monthly_trend
from components.metric_cards import MUTED, section_header
from utils.formatting import convert_currency, get_currency_symbol
from theme import chart_layout, current_palette


CHART_CONFIG = {"displayModeBar": False}


def _style_chart(fig, height):
    palette = current_palette()
    fig.update_layout(
        **chart_layout(palette),
        height=height,
        autosize=True,
    )


def _six_month_trend(df, selected_month, user_id=None):
    """Six months ending at the selected month; empty months are 0."""

    trend = monthly_trend(
        df,
        user_id=user_id,
        selected_month=selected_month,
    )

    if trend.empty:
        return None

    months = [
        str(pd.Period(selected_month, "M") - i)
        for i in range(5, -1, -1)
    ]

    trend = (
        trend.set_index("month")
        .reindex(months, fill_value=0.0)
        .rename_axis("month")
        .reset_index()
    )

    if (trend[["income", "expenses"]].sum().sum()) <= 0:
        return None

    trend["month_label"] = pd.to_datetime(
        trend["month"] + "-01",
        format="%Y-%m-%d",
        errors="coerce",
    ).dt.strftime("%b %Y")

    return trend


def render_cash_flow(df, selected_month, user_id=None):
    """Income vs expenses line chart for the last six months."""

    with st.container(border=True):
        section_header(
            "Cash Flow Overview",
            "Income vs expenses · last six months",
        )

        trend = _six_month_trend(df, selected_month, user_id=user_id)

        if trend is None:
            st.info(
                "Your cash-flow chart will appear when "
                "transactions are recorded."
            )
            return

        currency_symbol = get_currency_symbol()
        palette = current_palette()
        text_color = palette["text"]
        axis_line_color = palette["border"]
        labels = trend["month_label"].tolist()

        trend_long = trend.melt(
            id_vars=["month", "month_label"],
            value_vars=["income", "expenses"],
            var_name="transaction_type",
            value_name="amount",
        )

        trend_long["transaction_type"] = trend_long[
            "transaction_type"
        ].map({"income": "Income", "expenses": "Expenses"})
        trend_long["amount"] = trend_long["amount"].map(
            lambda amount: convert_currency(amount, currency_symbol)
        )

        fig = px.line(
            trend_long,
            x="month_label",
            y="amount",
            color="transaction_type",
            markers=True,
            color_discrete_map={
                "Income": palette["success"],
                "Expenses": palette["danger"],
            },
            labels={
                "month_label": "",
                "amount": f"Amount ({currency_symbol})",
                "transaction_type": "",
            },
            category_orders={"month_label": labels},
        )

        fig.update_traces(
            mode="lines+markers",
            line=dict(width=3),
            marker=dict(
                size=11,
                opacity=1,
                line=dict(width=2, color=palette["surface_2"]),
            ),
            hovertemplate=(
                f"{currency_symbol}%{{y:,.2f}}"
                "<extra>%{fullData.name}</extra>"
            ),
        )

        _style_chart(fig, 340)

        fig.update_layout(
            margin=dict(l=12, r=12, t=25, b=12),
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=12, color=text_color),
            ),
            xaxis=dict(
                type="category",
                categoryorder="array",
                categoryarray=labels,
                showgrid=False,
                showline=True,
                linecolor=axis_line_color,
                tickfont=dict(color=text_color),
                fixedrange=True,
            ),
            yaxis=dict(
                title=dict(
                    text=f"Amount ({currency_symbol})",
                    font=dict(color=text_color),
                ),
                gridcolor=palette["grid"],
                zeroline=False,
                tickprefix=currency_symbol,
                tickformat=",.0f",
                tickfont=dict(color=text_color),
                fixedrange=True,
            ),
        )

        st.plotly_chart(
            fig,
            width="stretch",
            config=CHART_CONFIG,
        )


def render_spending_breakdown(
    month_df,
    money,
    user_id=None,
    selected_month=None,
):
    """Donut chart of expenses by category for the selected month."""

    with st.container(border=True):
        section_header(
            "Spending Breakdown",
            "Where your money went this month",
        )

        breakdown = category_breakdown(
            month_df,
            user_id=user_id,
            selected_month=selected_month,
        )

        if breakdown.empty:
            st.info("No expenses recorded for this month yet.")
            return

        total_spent = float(breakdown["amount"].sum())
        currency_symbol = get_currency_symbol()
        palette = current_palette()
        displayed_breakdown = breakdown.copy()
        displayed_breakdown["amount"] = displayed_breakdown[
            "amount"
        ].map(lambda amount: convert_currency(amount, currency_symbol))

        fig = px.pie(
            displayed_breakdown,
            names="category",
            values="amount",
            hole=0.72,
            color_discrete_sequence=[
                palette["accent"],
                palette["info"],
                palette["success"],
                palette["warning"],
                palette["danger"],
            ],
        )

        percentages = (
            displayed_breakdown["amount"]
            / displayed_breakdown["amount"].sum()
        )
        fig.update_traces(
            textposition="inside",
            texttemplate=[
                "%{percent}" if percentage >= 0.04 else ""
                for percentage in percentages
            ],
            textfont=dict(color=palette["on_accent"], size=11),
            hovertemplate=(
                "<b>%{label}</b><br>"
                f"Amount: {currency_symbol}%{{value:,.2f}}<br>"
                "Share: %{percent}<extra></extra>"
            ),
            marker=dict(line=dict(color=palette["surface"], width=3)),
        )

        _style_chart(fig, 285)

        fig.update_layout(
            margin=dict(l=0, r=0, t=8, b=0),
            showlegend=True,
            legend=dict(
                font=dict(size=10, color=palette["text"]),
                orientation="h",
                yanchor="top",
                y=-0.03,
            ),
            annotations=[
                dict(
                    text=(
                        f"<b>{money(total_spent)}</b><br>"
                        "<span style='font-size:10px;color:"
                        f"{palette['text_muted']}'>"
                        "total spent</span>"
                    ),
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(size=16, color=palette["text"]),
                )
            ],
        )

        st.plotly_chart(
            fig,
            width="stretch",
            config=CHART_CONFIG,
        )

        top = breakdown.iloc[0]

        st.caption(
            f"Highest category: **{top['category']}** · "
            f"{money(top['amount'])}"
        )