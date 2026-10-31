from datetime import date

import streamlit as st

from analytics import calculate_goal_metrics
from domain.goals import goal_status_label, split_goals
from database import (
    MAX_AMOUNT,
    add_goal,
    contribute_to_goal,
    delete_goal,
    update_goal,
)
from utils.formatting import render_badge


GOAL_CATEGORIES = (
    "Emergency Fund",
    "Vacation",
    "Vehicle",
    "Real Estate",
    "Investment",
    "Other",
)


def _render_header():
    st.markdown(
        '<div class="ss-eyebrow">SPENDSENSE AI · PLAN AHEAD</div>'
        '<div class="ss-page-title">Savings Goals</div>'
        '<div class="ss-subtitle">'
        "Track target savings, emergency funds, and major purchase goals."
        "</div>",
        unsafe_allow_html=True,
    )


def _render_create_goal(today):
    with st.expander("✨ Create New Savings Goal"):
        with st.form("create_savings_goal", clear_on_submit=True):
            name = st.text_input(
                "Goal Name",
                max_chars=100,
                placeholder="e.g., Emergency fund",
            )
            target_amount = st.number_input(
                "Target Amount (₹)",
                min_value=0.01,
                max_value=MAX_AMOUNT,
                value=10000.0,
                step=1000.0,
            )
            current_amount = st.number_input(
                "Initial Savings (₹)",
                min_value=0.0,
                max_value=MAX_AMOUNT,
                value=0.0,
                step=500.0,
            )
            target_date = st.date_input(
                "Target Date",
                value=date(today.year + 1, today.month, min(today.day, 28)),
                min_value=today,
            )
            category = st.selectbox("Category", GOAL_CATEGORIES)

            submitted = st.form_submit_button(
                "Create goal",
                type="primary",
            )

        if not submitted:
            return

        if not name.strip():
            st.error("Enter a name for your savings goal.")
            return
        if current_amount > target_amount:
            st.error("Initial savings cannot exceed the target amount.")
            return
        if target_date < today:
            st.error("Choose a target date that is today or later.")
            return

        try:
            add_goal(
                name=name,
                target_amount=target_amount,
                current_amount=current_amount,
                target_date=target_date,
                category=category,
            )
        except (ValueError, TypeError) as error:
            st.error(f"Could not create the savings goal: {error}")
            return
        except Exception:
            st.error("Could not create the savings goal. Please try again.")
            return

        st.toast("Savings goal created.", icon="🎯")
        st.rerun()


def _render_goal_card(goal, money):
    goal_id = int(goal["id"])
    current_amount = float(goal.get("current_amount") or 0.0)
    target_amount = float(goal["target_amount"])
    goal_name = str(goal.get("name") or "Savings goal")
    category = str(goal.get("category") or "General")
    target_date_value = str(goal.get("target_date") or "")

    try:
        target_date = date.fromisoformat(target_date_value[:10])
        metrics = calculate_goal_metrics(goal)
    except (TypeError, ValueError) as error:
        st.error(f"Could not display “{goal_name}”: {error}")
        return

    with st.container(border=True):
        title_col, badge_col = st.columns([3, 1])
        with title_col:
            st.subheader(goal_name)
        with badge_col:
            st.markdown(
                render_badge(
                    category,
                    bg_color="var(--accent-soft)",
                    text_color="var(--accent)",
                ),
                unsafe_allow_html=True,
            )

        st.caption(f"Target date · {target_date.strftime('%d %b %Y')}")
        status_label = goal_status_label(metrics)
        st.markdown(
            f"""
            <div class="ss-goal-summary">
                <div class="ss-goal-ring"
                    style="--goal-progress:{min(metrics['percent_complete'], 100):.1f}%;">
                    <span>{metrics['percent_complete']:.0f}%</span>
                </div>
                <div>
                    <strong>{status_label}</strong>
                    <span>{money(current_amount)} of {money(target_amount)}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(
            min(metrics["percent_complete"] / 100, 1.0),
            text=f"{metrics['percent_complete']:.1f}% complete",
        )
        st.markdown(
            f"**{money(current_amount)}** of **{money(target_amount)}**"
        )

        if metrics["status"] == "COMPLETED":
            st.success("Goal completed")
        elif metrics["months_remaining"] == 0:
            st.warning(
                f"{money(metrics['remaining_amount'])} remaining; "
                "the target date has passed."
            )
        else:
            st.caption(
                f"Required monthly contribution: "
                f"**{money(metrics['required_monthly_savings'])}** · "
                f"{metrics['months_remaining']} month(s) remaining"
            )

        with st.popover("➕ Add Funds"):
            with st.form(f"goal_contribution_{goal_id}"):
                contribution = st.number_input(
                    "Contribution (₹)",
                    min_value=0.01,
                    max_value=MAX_AMOUNT,
                    value=100.0,
                    step=100.0,
                    key=f"goal_contribution_amount_{goal_id}",
                )
                contribute = st.form_submit_button("Add funds")

            if contribute:
                try:
                    updated = contribute_to_goal(goal_id, contribution)
                except (ValueError, TypeError) as error:
                    st.error(f"Could not add funds: {error}")
                except Exception:
                    st.error("Could not add funds. Please try again.")
                else:
                    if updated:
                        st.toast("Funds added to your goal.", icon="💰")
                        st.rerun()
                    else:
                        st.error("This goal could not be found.")

        with st.popover("Manage goal"):
            st.markdown("**Update goal**")
            edit_categories = list(GOAL_CATEGORIES)
            if category not in edit_categories:
                edit_categories.append(category)
            category_index = edit_categories.index(category)

            with st.form(f"edit_goal_{goal_id}"):
                edited_name = st.text_input(
                    "Goal Name",
                    value=goal_name,
                    max_chars=100,
                    key=f"edit_goal_name_{goal_id}",
                )
                edited_target = st.number_input(
                    "Target Amount (₹)",
                    min_value=0.01,
                    max_value=MAX_AMOUNT,
                    value=min(target_amount, MAX_AMOUNT),
                    step=1000.0,
                    key=f"edit_goal_target_{goal_id}",
                )
                edited_current = st.number_input(
                    "Current Savings (₹)",
                    min_value=0.0,
                    max_value=MAX_AMOUNT,
                    value=min(current_amount, MAX_AMOUNT),
                    step=500.0,
                    key=f"edit_goal_current_{goal_id}",
                )
                edited_date = st.date_input(
                    "Target Date",
                    value=target_date,
                    key=f"edit_goal_date_{goal_id}",
                )
                edited_category = st.selectbox(
                    "Category",
                    edit_categories,
                    index=category_index,
                    key=f"edit_goal_category_{goal_id}",
                )
                save_changes = st.form_submit_button("Save changes")

            if save_changes:
                if not edited_name.strip():
                    st.error("Enter a name for your savings goal.")
                else:
                    try:
                        updated = update_goal(
                            goal_id,
                            edited_name,
                            edited_target,
                            edited_current,
                            edited_date,
                            edited_category,
                        )
                    except (ValueError, TypeError) as error:
                        st.error(f"Could not update the goal: {error}")
                    except Exception:
                        st.error("Could not update the goal. Please try again.")
                    else:
                        if updated:
                            st.toast("Savings goal updated.", icon="🎯")
                            st.rerun()
                        else:
                            st.error("This goal could not be found.")

            st.divider()
            confirm_delete = st.checkbox(
                "I understand this permanently deletes the goal",
                key=f"confirm_delete_goal_{goal_id}",
            )
            if st.button(
                "Delete goal",
                key=f"delete_goal_{goal_id}",
                disabled=not confirm_delete,
            ):
                try:
                    deleted = delete_goal(goal_id)
                except Exception:
                    st.error("Could not delete the goal. Please try again.")
                else:
                    if deleted:
                        st.toast("Savings goal deleted.", icon="🗑️")
                        st.rerun()
                    else:
                        st.error("This goal could not be found.")


def render_goals(goals, money, today):
    """Render the savings goals page."""

    _render_header()
    _render_create_goal(today)

    active_goals, completed_goals = split_goals(goals)

    st.markdown("### Active goals")
    if not active_goals and not completed_goals:
        with st.container(border=True):
            st.info(
                "No savings goals yet. Create one above to start tracking "
                "your progress."
            )
        return

    for start in range(0, len(active_goals), 2):
        columns = st.columns(2, gap="medium")
        for column, goal in zip(columns, active_goals[start:start + 2]):
            with column:
                _render_goal_card(goal, money)

    if completed_goals:
        st.markdown("### Completed goals")
        for start in range(0, len(completed_goals), 2):
            columns = st.columns(2, gap="medium")
            for column, goal in zip(
                columns, completed_goals[start:start + 2]
            ):
                with column:
                    _render_goal_card(goal, money)
