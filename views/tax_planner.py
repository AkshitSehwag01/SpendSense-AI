import streamlit as st

from domain.tax import (
    NEW_REGIME,
    OLD_REGIME,
    build_deduction_statement,
    build_tax_export,
    financial_year,
    financial_year_transactions,
    income_after_deductions,
    tax_prefill,
)
from utils.dates import today_local


def _pdf_statement(
    statement,
    financial_year,
    return_form,
    tax_regime,
    gross_income,
    total_claimed,
):
    import pymupdf

    document = pymupdf.open()
    page = document.new_page()
    lines = [
        "SpendSense AI - ITR Tax Deduction Summary",
        f"Financial year: {financial_year}",
        f"Return type: {return_form}",
        f"Tax regime: {tax_regime}",
        f"Gross income entered: INR {gross_income:,.2f}",
        "",
    ]
    for row in statement.to_dict("records"):
        lines.extend(
            [
                f"{row['Section']} - {row['Line item']}",
                f"  Maximum limit: INR {row['Maximum limit (INR)']:,.2f}",
                "  Actual invested / paid: "
                f"INR {row['Actual invested / paid (INR)']:,.2f}",
                "  Eligible deduction: "
                f"INR {row['Eligible deduction (INR)']:,.2f}",
                "",
            ]
        )
    lines.extend(
        [
            f"Total deductions claimed: INR {total_claimed:,.2f}",
            "Estimated income after deductions: "
            f"INR {max(0.0, gross_income - total_claimed):,.2f}",
            "",
            "Estimate only - verify eligibility and supporting records "
            "with a qualified tax professional before filing.",
        ]
    )

    page.insert_textbox(
        pymupdf.Rect(48, 48, 547, 794),
        "\n".join(lines),
        fontsize=10,
        fontname="helv",
        lineheight=1.35,
    )
    return document.tobytes()


def render_tax_planner(
    financial_year_df,
    money,
    user_id=None,
    today=None,
):
    """Render an estimated ITR-1 / ITR-2 deduction statement for this FY."""

    del user_id  # All calculations operate on the caller's user-scoped data.
    fy_start, fy_end = financial_year(today or today_local())
    transactions = financial_year_transactions(
        financial_year_df,
        fy_start,
        fy_end,
    )
    prefill = tax_prefill(transactions)
    mapped_80c = prefill["mapped_80c"]
    mapped_self_health = prefill["self_health_premium"]
    mapped_parent_health = prefill["parent_health_premium"]
    mapped_interest = prefill["savings_interest"]
    rent_recorded = prefill["rent_recorded"]
    salary_recorded = prefill["salary_recorded"]

    st.subheader("ITR-1 / ITR-2 tax deduction summary")
    st.caption(
        f"Financial year {fy_start.year}-{fy_end.year} "
        f"({fy_start:%d %b %Y} to {fy_end:%d %b %Y})"
    )
    st.info(
        "This is an estimate for review, not a tax filing or eligibility "
        "determination. Transaction descriptions and manually entered "
        "amounts must be verified against documents."
    )

    with st.container(border=True):
        st.markdown("**Return and tax details**")
        return_form = st.segmented_control(
            "Return form",
            ("ITR-1", "ITR-2"),
            default="ITR-1",
            help="Choose the return form you expect to file; verify eligibility.",
            key="tax_planner_return_form",
        )
        tax_regime = st.segmented_control(
            "Tax regime",
            (OLD_REGIME, NEW_REGIME),
            default=OLD_REGIME,
            key="tax_planner_regime",
        )
        gross_income = st.number_input(
            "Gross total income before these deductions (₹)",
            min_value=0.0,
            value=max(0.0, salary_recorded),
            step=10_000.0,
            key="tax_planner_gross_income",
            help="Defaults to recorded Salary transactions; edit to include "
            "other income from your tax records.",
        )
        taxpayer_is_senior = st.checkbox(
            "Taxpayer is a senior citizen (60+)",
            key="tax_planner_taxpayer_senior",
        )

    with st.container(border=True):
        st.markdown("**Section 80C and HRA records**")
        st.caption(
            f"Recognized 80C transaction descriptions: {money(mapped_80c)}"
        )
        other_80c = st.number_input(
            "Additional eligible 80C investments not categorized above (₹)",
            min_value=0.0,
            step=5_000.0,
            key="tax_planner_other_80c",
        )
        basic_salary = st.number_input(
            "Annual basic salary plus eligible DA (₹)",
            min_value=0.0,
            step=10_000.0,
            key="tax_planner_basic_salary",
        )
        hra_received = st.number_input(
            "Annual HRA received (₹)",
            min_value=0.0,
            step=10_000.0,
            key="tax_planner_hra_received",
        )
        rent_paid = st.number_input(
            "Annual rent paid (₹)",
            min_value=0.0,
            value=rent_recorded,
            step=10_000.0,
            key="tax_planner_rent_paid",
            help="Defaults to recorded Rent expenses; edit to match receipts.",
        )
        metro_city = st.checkbox(
            "HRA calculation uses a metro city",
            key="tax_planner_metro_city",
        )

    with st.container(border=True):
        st.markdown("**Health insurance and savings interest**")
        self_health_premium = st.number_input(
            "Annual 80D premium for self/family (₹)",
            min_value=0.0,
            value=mapped_self_health,
            step=2_500.0,
            key="tax_planner_self_health",
        )
        parent_health_premium = st.number_input(
            "Annual 80D premium for parents (₹)",
            min_value=0.0,
            value=mapped_parent_health,
            step=2_500.0,
            key="tax_planner_parent_health",
        )
        parent_is_senior = st.checkbox(
            "Insured parent is a senior citizen (60+)",
            key="tax_planner_parent_senior",
        )
        savings_interest = st.number_input(
            "Savings account interest received during the FY (₹)",
            min_value=0.0,
            value=mapped_interest,
            step=1_000.0,
            key="tax_planner_savings_interest",
        )

    statement, total_claimed = build_deduction_statement(
        transactions=transactions,
        basic_salary=basic_salary,
        hra_received=hra_received,
        rent_paid=rent_paid,
        metro_city=metro_city,
        self_health_premium=self_health_premium,
        parent_health_premium=parent_health_premium,
        parent_is_senior=parent_is_senior,
        savings_interest=savings_interest,
        taxpayer_is_senior=taxpayer_is_senior,
        other_80c=other_80c,
        old_regime=tax_regime == OLD_REGIME,
    )
    taxable_after_deductions = income_after_deductions(
        gross_income,
        total_claimed,
    )

    st.dataframe(
        statement,
        hide_index=True,
        column_config={
            "Maximum limit (INR)": st.column_config.NumberColumn(
                format="₹ %,.2f"
            ),
            "Actual invested / paid (INR)": st.column_config.NumberColumn(
                format="₹ %,.2f"
            ),
            "Eligible deduction (INR)": st.column_config.NumberColumn(
                format="₹ %,.2f"
            ),
        },
        alt="Estimated tax deduction amounts by Indian income-tax section",
    )
    metric_col, reduction_col = st.columns(2)
    metric_col.metric(
        "Total deductions / exemptions",
        money(total_claimed),
    )
    reduction_col.metric(
        "Estimated income after deductions",
        money(taxable_after_deductions),
    )
    if tax_regime == NEW_REGIME:
        st.caption(
            "The listed deductions are excluded from the estimate under "
            "the selected new regime. Verify section-specific eligibility "
            "and current law before filing."
        )

    export = build_tax_export(
        statement,
        f"{fy_start.year}-{fy_end.year}",
        return_form,
        tax_regime,
        gross_income,
        total_claimed,
    )
    export_format = st.segmented_control(
        "Export format",
        ("CSV", "PDF"),
        default="CSV",
        key="tax_planner_export_format",
    )
    if export_format == "CSV":
        export_data = export.to_csv(index=False).encode("utf-8-sig")
        mime_type = "text/csv"
        file_extension = "csv"
    else:
        export_data = _pdf_statement(
            statement,
            f"{fy_start.year}-{fy_end.year}",
            return_form,
            tax_regime,
            gross_income,
            total_claimed,
        )
        mime_type = "application/pdf"
        file_extension = "pdf"

    st.download_button(
        "📄 Download ITR Tax Summary (CSV/PDF)",
        data=export_data,
        file_name=(
            f"itr_tax_summary_FY{fy_start.year}-{fy_end.year}."
            f"{file_extension}"
        ),
        mime=mime_type,
        width="stretch",
    )
