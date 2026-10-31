"""Indian financial-year deduction mapping and tax planning estimates."""

import math
from datetime import date

import pandas as pd


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

OLD_REGIME = "Old regime"
NEW_REGIME = "New regime"


def financial_year(today):
    start_year = today.year if today.month >= 4 else today.year - 1
    return date(start_year, 4, 1), date(start_year + 1, 3, 31)


def amount(value):
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return 0.0
    return amount if math.isfinite(amount) and amount > 0 else 0.0


def financial_year_transactions(transactions, start, end):
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


def mapped_80c_total(transactions):
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


def mapped_80d_totals(transactions):
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


def mapped_savings_interest(transactions):
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


def build_deduction_statement(
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
    invested_80c = mapped_80c_total(transactions) + amount(other_80c)
    hra_exemption = min(
        amount(hra_received),
        max(0.0, amount(rent_paid) - 0.1 * amount(basic_salary)),
        (0.5 if metro_city else 0.4) * amount(basic_salary),
    )

    self_health_limit = 50_000.0 if taxpayer_is_senior else 25_000.0
    parent_health_limit = 50_000.0 if parent_is_senior else 25_000.0
    health_deduction = min(
        amount(self_health_premium), self_health_limit
    ) + min(amount(parent_health_premium), parent_health_limit)

    interest_limit = (
        SECTION_80TTB_LIMIT if taxpayer_is_senior else SECTION_80TTA_LIMIT
    )
    interest_deduction = min(amount(savings_interest), interest_limit)

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
                amount(self_health_premium) + amount(parent_health_premium)
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
            "Actual invested / paid (INR)": amount(savings_interest),
            "Eligible deduction (INR)": interest_deduction
            if deductions_enabled
            else 0.0,
        },
        {
            "Section": "10(13A)",
            "Line item": "HRA exemption (salary, rent, and city-based limit)",
            "Maximum limit (INR)": hra_exemption,
            "Actual invested / paid (INR)": amount(rent_paid),
            "Eligible deduction (INR)": hra_exemption
            if deductions_enabled
            else 0.0,
        },
    ]
    statement = pd.DataFrame(sections)
    total_claimed = float(statement["Eligible deduction (INR)"].sum())
    return statement, total_claimed


def calculate_80c_headroom(financial_year_df, today):
    """Summarize investment and healthcare spending for the tax tracker."""

    financial_year_start = date(
        today.year if today.month >= 4 else today.year - 1,
        4,
        1,
    )
    financial_year_end = date(financial_year_start.year + 1, 3, 31)
    required_columns = {
        "transaction_date",
        "transaction_type",
        "category",
        "amount",
    }

    if (
        financial_year_df is None
        or financial_year_df.empty
        or not required_columns.issubset(financial_year_df.columns)
    ):
        fy_transactions = pd.DataFrame(columns=required_columns)
    else:
        fy_transactions = financial_year_df.copy()
        dates = pd.to_datetime(
            fy_transactions["transaction_date"],
            errors="coerce",
        ).dt.date
        in_financial_year = dates.between(
            financial_year_start,
            financial_year_end,
            inclusive="both",
        )
        fy_transactions = fy_transactions.loc[in_financial_year]

    expenses = fy_transactions.loc[
        fy_transactions["transaction_type"].eq("Expense")
    ]

    def category_total(category):
        total = 0.0
        for amount in expenses.loc[
            expenses["category"].eq(category), "amount"
        ]:
            try:
                number = float(amount)
            except (TypeError, ValueError):
                continue
            if not math.isnan(number):
                total += number
        return total

    investment_total = category_total("Investment")
    healthcare_total = category_total("Healthcare")
    section_80c_limit = 150_000
    section_80c_total = min(investment_total, section_80c_limit)

    return {
        "investment_total": investment_total,
        "healthcare_total": healthcare_total,
        "section_80c_total": section_80c_total,
        "remaining_headroom": max(
            section_80c_limit - section_80c_total,
            0,
        ),
    }


def financial_year_label(today):
    start, end = financial_year(today)
    return f"{start.year}-{end.year}"


def recorded_category_total(transactions, transaction_type, category):
    """Total of one transaction type and category, case-insensitive."""

    return float(
        transactions.loc[
            transactions["transaction_type"].astype(str).str.casefold().eq(
                transaction_type.casefold()
            )
            & transactions["category"].astype(str).str.casefold().eq(
                category.casefold()
            ),
            "amount",
        ].sum()
    )


def tax_prefill(transactions):
    """Amounts recognized from recorded transactions to prefill inputs."""

    self_health, parent_health = mapped_80d_totals(transactions)
    return {
        "mapped_80c": mapped_80c_total(transactions),
        "self_health_premium": self_health,
        "parent_health_premium": parent_health,
        "savings_interest": mapped_savings_interest(transactions),
        "rent_recorded": recorded_category_total(transactions, "Expense", "Rent"),
        "salary_recorded": recorded_category_total(
            transactions, "Income", "Salary"
        ),
    }


def income_after_deductions(gross_income, total_claimed):
    return max(0.0, gross_income - total_claimed)


def build_tax_export(
    statement,
    financial_year,
    return_form,
    tax_regime,
    gross_income,
    total_claimed,
):
    """Deduction statement with filing context columns for CSV export."""

    export = statement.copy()
    export.insert(0, "Financial year", financial_year)
    export.insert(1, "Return form", return_form)
    export.insert(2, "Tax regime", tax_regime)
    export["Gross total income (INR)"] = gross_income
    export["Total deductions (INR)"] = total_claimed
    export["Estimated income after deductions (INR)"] = (
        income_after_deductions(gross_income, total_claimed)
    )
    return export
