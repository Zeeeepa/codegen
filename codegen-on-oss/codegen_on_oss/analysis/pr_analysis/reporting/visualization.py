"""
Visualization components for PR analysis.

This module provides functions for creating visualizations for analysis reports,
including charts, graphs, and tables.
"""

import logging
from typing import Any, Dict, List, Union

logger = logging.getLogger(__name__)


def create_chart(
    title: str, chart_type: str, labels: List[str], values: List[Union[int, float]]
) -> Dict[str, Any]:
    """
    Create a chart visualization.

    Args:
        title: Chart title
        chart_type: Chart type (pie, bar, line)
        labels: Data labels
        values: Data values

    Returns:
        Chart data
    """
    logger.debug(f"Creating {chart_type} chart: {title}")

    return {
        "type": "chart",
        "chart_type": chart_type,
        "title": title,
        "data": {
            "labels": labels,
            "values": values,
        },
    }


def create_graph(
    title: str, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Create a graph visualization.

    Args:
        title: Graph title
        nodes: Graph nodes
        edges: Graph edges

    Returns:
        Graph data
    """
    logger.debug(f"Creating graph: {title}")

    return {
        "type": "graph",
        "title": title,
        "data": {
            "nodes": nodes,
            "edges": edges,
        },
    }


def create_table(title: str, headers: List[str], rows: List[List[Any]]) -> Dict[str, Any]:
    """
    Create a table visualization.

    Args:
        title: Table title
        headers: Table headers
        rows: Table rows

    Returns:
        Table data
    """
    logger.debug(f"Creating table: {title}")

    return {
        "type": "table",
        "title": title,
        "data": {
            "headers": headers,
            "rows": rows,
        },
    }


def render_chart_as_ascii(chart: Dict[str, Any]) -> str:
    """
    Render a chart as ASCII art.

    Args:
        chart: Chart data

    Returns:
        ASCII art representation of the chart
    """
    title = chart.get("title", "Chart")
    chart_type = chart.get("chart_type", "bar")
    data = chart.get("data", {})
    labels = data.get("labels", [])
    values = data.get("values", [])

    if not labels or not values:
        return f"{title} (No data)"

    if chart_type == "pie":
        return _render_pie_chart_ascii(title, labels, values)
    elif chart_type == "bar":
        return _render_bar_chart_ascii(title, labels, values)
    elif chart_type == "line":
        return _render_line_chart_ascii(title, labels, values)
    else:
        return f"{title} (Unsupported chart type: {chart_type})"


def _render_pie_chart_ascii(title: str, labels: List[str], values: List[Union[int, float]]) -> str:
    """
    Render a pie chart as ASCII art.

    Args:
        title: Chart title
        labels: Data labels
        values: Data values

    Returns:
        ASCII art representation of the pie chart
    """
    total = sum(values)
    if total == 0:
        return f"{title} (No data)"

    result = f"{title}\n\n"

    for _i, (label, value) in enumerate(zip(labels, values, strict=False)):
        percentage = (value / total) * 100
        bar_length = int((percentage / 100) * 20)
        result += f"{label}: {value} ({percentage:.1f}%) {'#' * bar_length}\n"

    return result


def _render_bar_chart_ascii(title: str, labels: List[str], values: List[Union[int, float]]) -> str:
    """
    Render a bar chart as ASCII art.

    Args:
        title: Chart title
        labels: Data labels
        values: Data values

    Returns:
        ASCII art representation of the bar chart
    """
    if not values:
        return f"{title} (No data)"

    max_value = max(values)
    if max_value == 0:
        return f"{title} (No data)"

    result = f"{title}\n\n"

    max_label_length = max(len(label) for label in labels)

    for _i, (label, value) in enumerate(zip(labels, values, strict=False)):
        bar_length = int((value / max_value) * 20)
        result += f"{label.ljust(max_label_length)}: {value} {'#' * bar_length}\n"

    return result


def _render_line_chart_ascii(title: str, labels: List[str], values: List[Union[int, float]]) -> str:
    """
    Render a line chart as ASCII art.

    Args:
        title: Chart title
        labels: Data labels
        values: Data values

    Returns:
        ASCII art representation of the line chart
    """
    if not values:
        return f"{title} (No data)"

    min_value = min(values)
    max_value = max(values)
    if min_value == max_value:
        return f"{title} (Constant value: {min_value})"

    result = f"{title}\n\n"

    height = 10
    width = len(values)

    # Create the chart grid
    grid = [[" " for _ in range(width)] for _ in range(height)]

    # Plot the values
    for i, value in enumerate(values):
        y = height - 1 - int(((value - min_value) / (max_value - min_value)) * (height - 1))
        grid[y][i] = "*"

    # Render the grid
    for row in grid:
        result += "".join(row) + "\n"

    # Add the x-axis labels
    if len(labels) <= width:
        result += "".join(label[0] for label in labels) + "\n"

    return result


def render_table_as_ascii(table: Dict[str, Any]) -> str:
    """
    Render a table as ASCII art.

    Args:
        table: Table data

    Returns:
        ASCII art representation of the table
    """
    title = table.get("title", "Table")
    data = table.get("data", {})
    headers = data.get("headers", [])
    rows = data.get("rows", [])

    if not headers or not rows:
        return f"{title} (No data)"

    result = f"{title}\n\n"

    # Calculate column widths
    col_widths = [len(str(header)) for header in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))

    # Create the header row
    header_row = (
        "| "
        + " | ".join(str(header).ljust(col_widths[i]) for i, header in enumerate(headers))
        + " |"
    )
    separator = "+-" + "-+-".join("-" * col_widths[i] for i in range(len(headers))) + "-+"

    result += separator + "\n"
    result += header_row + "\n"
    result += separator + "\n"

    # Create the data rows
    for row in rows:
        data_row = (
            "| "
            + " | ".join(
                str(cell).ljust(col_widths[i]) if i < len(col_widths) else str(cell)
                for i, cell in enumerate(row)
            )
            + " |"
        )
        result += data_row + "\n"

    result += separator + "\n"

    return result
