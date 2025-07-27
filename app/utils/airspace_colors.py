"""Centralized airspace color configuration.

This module defines the color scheme for different airspace classes,
providing a single source of truth for all components (Python, JavaScript, CSS).
"""

from app.utils.logging_utils import debug_log, info_log

# Airspace class color mapping
AIRSPACE_COLORS = {
    "A": "#2196f3",  # Blue
    "B": "#00bcd4",  # Cyan
    "C": "#3f51b5",  # Indigo
    "D": "#9c27b0",  # Purple
    "E": "#e91e63",  # Pink
    "CTR": "#f44336",  # Red
    "Restricted": "#ffc107",  # Amber
    "Danger": "#4caf50",  # Green
    "Prohibited": "#ff5722",  # Deep Orange
    "GliderProhibited": "#ff5722",  # Deep Orange
    "WaveWindow": "#607d8b",  # Blue Grey
}

# Default color for unknown airspace classes
DEFAULT_COLOR = "#999999"  # Grey


def get_airspace_color(airspace_class: str) -> str:
    """Get the color code for a given airspace class.

    Args:
        airspace_class (str): The airspace class identifier (e.g., 'A', 'B', 'CTR').

    Returns:
        str: The corresponding hex color code. Returns the default color if the class is unknown.
    """
    return AIRSPACE_COLORS.get(airspace_class, DEFAULT_COLOR)


def generate_css_classes() -> str:
    """Generate CSS class definitions for airspace colors.

    Returns:
        str: CSS class definitions as a string, with each airspace class mapped to a background color.
    """
    css_lines = []
    for airspace_class, color in AIRSPACE_COLORS.items():
        css_class_name = f"class-{airspace_class}"
        css_lines.append(f".{css_class_name} {{")
        css_lines.append(f"    background-color: {color};")
        if color == "#ffc107":  # Amber needs black text for readability
            css_lines.append("    color: black;")
        css_lines.append("}")
        css_lines.append("")

    # Add default class
    css_lines.append(".class-default {")
    css_lines.append(f"    background-color: {DEFAULT_COLOR};")
    css_lines.append("}")

    info_log(
        "airspace_colors",
        f"Generated {len(AIRSPACE_COLORS)} CSS classes for airspace colors",
    )
    debug_log("airspace_colors", "Generated CSS classes:\n" + "\n".join(css_lines))

    return "\n".join(css_lines)


def generate_javascript_colors() -> str:
    """Generate a JavaScript object definition for airspace colors.

    Returns:
        str: JavaScript code as a string, defining the airspace color mapping and default color.
    """
    js_lines = ["const AIRSPACE_COLORS = {"]
    for airspace_class, color in AIRSPACE_COLORS.items():
        js_lines.append(f"    '{airspace_class}': '{color}',")
    js_lines.append("};")
    js_lines.append("")
    js_lines.append(f"const DEFAULT_AIRSPACE_COLOR = '{DEFAULT_COLOR}';")

    info_log(
        "airspace_colors",
        f"Generated JavaScript object with {len(AIRSPACE_COLORS)} airspace colors",
    )
    debug_log("airspace_colors", "Generated JavaScript colors:\n" + "\n".join(js_lines))

    return "\n".join(js_lines)


def generate_css_variables() -> str:
    """Generate CSS custom properties (variables) for airspace colors.

    Returns:
        str: CSS variable definitions as a string, with each airspace class mapped to a CSS custom property.
    """
    css_lines = [":root {"]
    for airspace_class, color in AIRSPACE_COLORS.items():
        css_var_name = f"--airspace-{airspace_class.lower()}"
        css_lines.append(f"    {css_var_name}: {color};")
    css_lines.append(f"    --airspace-default: {DEFAULT_COLOR};")
    css_lines.append("}")

    info_log(
        "airspace_colors",
        f"Generated {len(AIRSPACE_COLORS)} CSS variables for airspace colors",
    )
    debug_log("airspace_colors", "Generated CSS variables:\n" + "\n".join(css_lines))

    return "\n".join(css_lines)


def generate_complete_css() -> str:
    """Generate complete CSS including variables and classes.

    Returns:
        str: Complete CSS as a string, including CSS variables and class definitions for airspace colors.
    """
    css_parts = [
        "/* Airspace class colors - generated from centralized config */",
        generate_css_variables(),
        "",
        generate_css_classes(),
    ]

    debug_log(
        "airspace_colors",
        f"Generated complete CSS with {len(AIRSPACE_COLORS)} airspace classes",
    )
    debug_log("airspace_colors", "Generated complete CSS:\n" + "\n".join(css_parts))

    return "\n".join(css_parts)


def get_legend_data() -> list:
    """Get legend data for template rendering.

    Returns:
        list: A list of dictionaries, each containing 'class', 'color', and 'name' for an airspace class.
    """
    return [
        {"class": airspace_class, "color": color, "name": f"Class {airspace_class}"}
        for airspace_class, color in AIRSPACE_COLORS.items()
    ]
