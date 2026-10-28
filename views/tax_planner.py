import math
from datetime import date

import pandas as pd
import streamlit as st

from utils.dates import today_local


SECTION_80C_LIMIT = 150_000.0
SECTION_80TTA_LIMIT = 10_000.0
SECTION_80TTB_LIMIT = 50_000.0

_SECTION_80C_KEYWORDS = (
    "ppf",
    "public provident",
    "elss",
    "equity linked savings",
    "epf",
    "employee provident",
    "provident fund",
    "lic premium",
    "life insurance premium",
    "tuition fee",
    "tuition fees",
)


def _financial_year(today):
    start_year = today.year if today.month >= 4 else today.year - 1
    return date(start_year, 4, 1), date(start_year + 1, 3, 31)


def _amount(value):
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return 0.0
    return amount if math.isfinite(amount) and amount > 0 else 0.0


def _financial_year_transactions(transactions, start, end):
    if transactions is None or transactions.empty:
        return pd.DataFrame(
            columns=[
                "transaction_type",
                "amount",
                "category",
                "description",
                "transaction_date",
            ]
        )

    data = transactions.copy()
    required = {
        "transaction_type",
        "amount",
        "category",
        "description",
        "transaction_date",
    }
    if not required.issubset(data.columns):
        return pd.DataFrame(columns=required)

    data["transaction_date"] = pd.to_datetime(
        data["transaction_date"],
        errors="coerce",
        format="ISO8601",
    )
    dates = data["transaction_date"].dt.date
    data["amount"] = pd.to_numeric(data["amount"], errors="coerce")
    return data.loc[
        dates.between(start, end, inclusive="both")
        & data["amount"].notna()
        & data["amount"].ge(0)
    ].copy()


def _mapped_80c_transactions(transactions):
    if transactions.empty:
        return 0.0

    expenses = transactions.loc[
        transactions["transaction_type"].astype(str).str.casefold().eq("expense")
    ].copy()
    eligible = expenses.loc[
        expenses.apply(
            lambda row: any(
                keyword in (
                    f"{row['category']} {row['description']}".casefold()
                )
                for keyword in _SECTION_80C_KEYWORDS
            ),
            axis=1,
        )
    ]
    return float(eligible["amount"].sum())


def _mapped_80d_transactions(transactions):
    if transactions.empty:
        return 0.0, 0.0

    descriptions = (
        transactions["description"].fillna("").astype(str).str.casefold()
    )
    health_insurance = transactions.loc[
        transactions["transaction_type"].astype(str).str.casefold().eq(
            "expense"
        )
        & descriptions.str.contains(
            r"health insurance|medical insurance|mediclaim|"
            r"health premium|medical premium",
            regex=True,
        )
    ]
    parent_mask = health_insurance["description"].fillna("").astype(
        str
        ).str.casefold().str.contains(
            r"\b(?:parents?|mother|father)\b",
            regex=True,
        )
    return (
        float(health_insurance.loc[~parent_mask, "amount"].sum()),
        float(health_insurance.loc[parent_mask, "amount"].sum()),
    )


def _mapped_savings_interest(transactions):
    if transactions.empty:
        return 0.0

    descriptions = (
        transactions["description"].fillna("").astype(str).str.casefold()
    )
    interest_rows = transactions.loc[
        transactions["transaction_type"].astype(str).str.casefold().eq(
            "income"
        )
        & descriptions.str.contains(
            r"savings account interest|savings interest",
            regex=True,
        )
    ]
    return float(interest_rows["amount"].sum())


def _build_statement(
    transactions,
    basic_salary,
    hra_received,
    rent_paid,
    metro_city,
    self_health_premium,
    parent_health_premium,
    parent_is_senior,
    savings_interest,
    taxpayer_is_senior,
    other_80c,
    old_regime,
):
    invested_80c = _mapped_80c_transactions(transactions) + _amount(other_80c)
    hra_exemption = min(
        _amount(hra_received),
        max(0.0, _amount(rent_paid) - 0.1 * _amount(basic_salary)),
        (0.5 if metro_city else 0.4) * _amount(basic_salary),
    )

    self_health_limit = 50_000.0 if taxpayer_is_senior else 25_000.0
    parent_health_limit = 50_000.0 if parent_is_senior else 25_000.0
    health_deduction = min(
        _amount(self_health_premium), self_health_limit
    ) + min(_amount(parent_health_premium), parent_health_limit)

    interest_limit = (
        SECTION_80TTB_LIMIT if taxpayer_is_senior else SECTION_80TTA_LIMIT
    )
    interest_deduction = min(_amount(savings_interest), interest_limit)

    deductions_enabled = bool(old_regime)
    sections = [
        {
            "Section": "80C",
            "Line item": "PPF, ELSS, EPF, LIC premium, tuition fees",
            "Maximum limit (INR)": SECTION_80C_LIMIT,
            "Actual invested / paid (INR)": invested_80c,
            "Eligible deduction (INR)": min(
                invested_80c, SECTION_80C_LIMIT
            )
            if deductions_enabled
            else 0.0,
        },
        {
            "Section": "80D",
            "Line item": "Health insurance premiums (self/family + parents)",
            "Maximum limit (INR)": self_health_limit + parent_health_limit,
            "Actual invested / paid (INR)": (
                _amount(self_health_premium) + _amount(parent_health_premium)
            ),
            "Eligible deduction (INR)": health_deduction
            if deductions_enabled
            else 0.0,
        },
        {
            "Section": "80TTA / 80TTB",
            "Line item": (
                "Savings account interest exemption "
                "(80TTB for senior citizens)"
            ),
            "Maximum limit (INR)": interest_limit,
            "Actual invested / paid (INR)": _amount(savings_interest),
            "Eligible deduction (INR)": interest_deduction
            if deductions_enabled
            else 0.0,
        },
        {
            "Section": "10(13A)",
            "Line item": "HRA exemption (salary, rent, and city-based limit)",
            "Maximum limit (INR)": hra_exemption,
            "Actual invested / paid (INR)": _amount(rent_paid),
            "Eligible deduction (INR)": hra_exemption
            if deductions_enabled
            else 0.0,
        },
    ]
    statement = pd.DataFrame(sections)
    total_claimed = float(statement["Eligible deduction (INR)"].sum())
    return statement, total_claimed


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
    fy_start, fy_end = _financial_year(today or today_local())
    transactions = _financial_year_transactions(
        financial_year_df,
        fy_start,
        fy_end,
    )
    mapped_80c = _mapped_80c_transactions(transactions)
    mapped_self_health, mapped_parent_health = _mapped_80d_transactions(
        transactions
    )
    mapped_interest = _mapped_savings_interest(transactions)
    rent_recorded = float(
        transactions.loc[
            transactions["transaction_type"].astype(str).str.casefold().eq(
                "expense"
            )
            & transactions["category"].astype(str).str.casefold().eq("rent"),
            "amount",
        ].sum()
    )
    salary_recorded = float(
        transactions.loc[
            transactions["transaction_type"].astype(str).str.casefold().eq(
                "income"
            )
            & transactions["category"].astype(str).str.casefold().eq("salary"),
            "amount",
        ].sum()
    )

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
            ("Old regime", "New regime"),
            default="Old regime",
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

    statement, total_claimed = _build_statement(
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
        old_regime=tax_regime == "Old regime",
    )
    taxable_after_deductions = max(0.0, gross_income - total_claimed)

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
    if tax_regime == "New regime":
        st.caption(
            "The listed deductions are excluded from the estimate under "
            "the selected new regime. Verify section-specific eligibility "
            "and current law before filing."
        )

    export = statement.copy()
    export.insert(0, "Financial year", f"{fy_start.year}-{fy_end.year}")
    export.insert(1, "Return form", return_form)
    export.insert(2, "Tax regime", tax_regime)
    export["Gross total income (INR)"] = gross_income
    export["Total deductions (INR)"] = total_claimed
    export["Estimated income after deductions (INR)"] = (
        taxable_after_deductions
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
