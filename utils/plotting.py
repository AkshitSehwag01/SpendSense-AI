from theme import chart_layout


def plotly_template():
    """Return a palette-aware Plotly template for the current rerun."""

    return {"layout": chart_layout()}


# Backwards-compatible import for callers that only need a static template.
PLOTLY_TEMPLATE = plotly_template()
