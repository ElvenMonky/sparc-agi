"""Matplotlib helpers for rendering ARC-style grids and generated puzzles."""

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import ListedColormap
from matplotlib.figure import Figure

from sparc_agi.features.base import Feature
from sparc_agi.features.orientation import Orientation
from sparc_agi.features.range import Range

# Standard ARC palette (0–9), plus an extra slot for out-of-range values like 10.
ARC_COLORS = [
    "#000000",  # 0 black
    "#0074D9",  # 1 blue
    "#FF4136",  # 2 red
    "#2ECC40",  # 3 green
    "#FFDC00",  # 4 yellow
    "#AAAAAA",  # 5 grey
    "#F012BE",  # 6 magenta
    "#FF851B",  # 7 orange
    "#7FDBFF",  # 8 teal
    "#870C25",  # 9 maroon
    "#FFFFFF",  # 10+ fallback (white)
]
ARC_CMAP = ListedColormap(ARC_COLORS)


def _is_int_grid(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    if not isinstance(value[0], list):
        return False
    return all(
        isinstance(row, list) and all(isinstance(cell, int) and not isinstance(cell, bool) for cell in row)
        for row in value
    )


def _is_placement_list(value: Any) -> bool:
    """True for arrangement instances: ``[((x, y), pool_index), ...]``."""
    if not isinstance(value, list) or not value:
        return False
    first = value[0]
    if not (isinstance(first, (list, tuple)) and len(first) == 2):
        return False
    coord, idx = first
    return (
        isinstance(coord, (list, tuple))
        and len(coord) == 2
        and all(isinstance(v, int) and not isinstance(v, bool) for v in coord)
        and isinstance(idx, int)
        and not isinstance(idx, bool)
    )


def placements_to_index_grid(
    placements: list[Any],
    *,
    width: int | None = None,
    height: int | None = None,
) -> list[list[int]]:
    if not placements and not (width and height):
        return []
    if width is None:
        width = max(p[0][0] for p in placements) + 1
    if height is None:
        height = max(p[0][1] for p in placements) + 1
    grid = [[-1] * width for _ in range(height)]
    for (x, y), idx in placements:
        if 0 <= x < width and 0 <= y < height:
            grid[y][x] = idx
    return grid


def _is_arrangement_step(value: Any) -> bool:
    """True for recorded arrangement step payloads ``{placements, width?, height?}``."""
    return isinstance(value, dict) and "placements" in value


def plot_step_visual(ax: Axes, value: Any, title: str = "") -> None:
    """Draw a sample step: ARC object grid or arrangement index grid."""
    if _is_arrangement_step(value):
        placements = value.get("placements") or []
        plot_index_grid(
            ax,
            placements_to_index_grid(
                placements,
                width=value.get("width"),
                height=value.get("height"),
            ),
            title=title,
        )
        return
    if _is_placement_list(value):
        plot_index_grid(ax, placements_to_index_grid(value), title=title)
        return
    if _is_int_grid(value):
        plot_arc_grid(ax, value, title=title)
        return
    ax.axis("off")
    if title:
        ax.set_title(title, fontsize=10)


def plot_arc_grid(ax: Axes, grid_data: list[list[int]], title: str = "") -> None:
    """Draw an ARC color grid with light cell borders."""
    if not grid_data or not grid_data[0]:
        ax.axis("off")
        if title:
            ax.set_title(title, fontsize=10)
        return

    grid = np.asarray(grid_data, dtype=int)
    display = np.clip(grid, 0, len(ARC_COLORS) - 1)
    ax.imshow(display, cmap=ARC_CMAP, vmin=0, vmax=len(ARC_COLORS) - 1, interpolation="nearest")
    ax.set_xticks(np.arange(-0.5, grid.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-0.5, grid.shape[0], 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=1.0)
    ax.tick_params(which="both", bottom=False, left=False, labelbottom=False, labelleft=False)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.8)
    if title:
        ax.set_title(title, fontsize=10)


def plot_index_grid(ax: Axes, grid_data: list[list[int]], title: str = "") -> None:
    """Draw a small integer grid (e.g. pool indices) with cell labels."""
    if not grid_data or not grid_data[0]:
        ax.axis("off")
        if title:
            ax.set_title(title, fontsize=10)
        return

    grid = np.asarray(grid_data, dtype=float)
    masked = np.ma.masked_where(grid < 0, grid)
    present = grid[grid >= 0]
    vmax = float(present.max()) if present.size else 1.0
    ax.imshow(masked, cmap="Blues", vmin=-0.5, vmax=max(vmax, 1.0), interpolation="nearest")
    for y in range(grid.shape[0]):
        for x in range(grid.shape[1]):
            val = int(grid[y, x])
            label = "·" if val < 0 else str(val)
            # Blues: low values are light, high values are dark — pick contrasting ink.
            if val < 0:
                ink = "0.45"
            else:
                ink = "white" if (val / max(vmax, 1.0)) > 0.35 else "black"
            ax.text(x, y, label, ha="center", va="center", fontsize=9, color=ink, fontweight="bold")
    ax.set_xticks(np.arange(-0.5, grid.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-0.5, grid.shape[0], 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=1.0)
    ax.tick_params(which="both", bottom=False, left=False, labelbottom=False, labelleft=False)
    if title:
        ax.set_title(title, fontsize=10)


def _orientation_short_label(direction: int) -> str:
    phrase = Orientation(value=Range(direction)).describe()
    if not phrase:
        return "identity"
    if phrase == "flipped horizontally":
        return "horizontal flip"
    if phrase == "flipped vertically":
        return "vertical flip"
    if phrase.startswith("flipped "):
        return phrase
    if phrase.startswith("rotated "):
        return f"{phrase.removeprefix('rotated ')} rotation"
    if phrase == "transposed":
        return "transpose"
    return phrase


def cache_kind_label(feature: Feature | None, value: Any) -> str:
    if feature is not None:
        return feature.__feature_family__
    if isinstance(value, int) and not isinstance(value, bool):
        return "orientation"
    if _is_placement_list(value):
        return "arrangement"
    if _is_int_grid(value):
        return "object"
    return "value"


def cache_value_summary(feature: Feature | None, value: Any) -> str:
    """Short natural-language line under the cache key header."""
    if feature is not None and type(feature).__feature_family__ == "orientation":
        if isinstance(value, int) and not isinstance(value, bool):
            return _orientation_short_label(value)
    if feature is not None and type(feature).__feature_family__ == "arrangement":
        return feature.describe()
    if isinstance(value, int) and not isinstance(value, bool):
        return _orientation_short_label(value)
    if _is_placement_list(value):
        return f"{len(value)} placements"
    if _is_int_grid(value):
        h = len(value)
        w = len(value[0]) if value else 0
        return f"{w}x{h} grid"
    return repr(value)


def plot_cache_visual(ax: Axes, value: Any) -> bool:
    """Draw cache visual content. Returns False when there is nothing visual to show."""
    if _is_int_grid(value):
        plot_arc_grid(ax, value)
        return True
    if _is_placement_list(value):
        plot_index_grid(ax, placements_to_index_grid(value))
        return True
    ax.axis("off")
    return False


def render_generated_puzzle(
    puzzle_id: str,
    puzzle: dict[str, Any],
    *,
    generated_at: str | None = None,
    cache_features: dict[str, Feature] | None = None,
) -> Figure:
    """Build a figure for one generated puzzle dict (from generated JSON)."""
    cache: dict[str, Any] = puzzle.get("cache") or {}
    challenge = puzzle["challenge"]
    solution = puzzle.get("solution") or []
    steps = puzzle.get("steps") or {}
    description = puzzle.get("description") or {}
    cache_features = cache_features or {}

    train = list(challenge.get("train") or [])
    test = list(challenge.get("test") or [])
    train_steps = list(steps.get("train") or [])
    test_steps = list(steps.get("test") or [])

    samples: list[tuple[str, Any, list[Any], Any]] = []
    for i, sample in enumerate(train):
        sample_steps = train_steps[i] if i < len(train_steps) else []
        samples.append((f"train {i + 1}", sample["input"], sample_steps, sample.get("output")))
    for i, sample in enumerate(test):
        sample_steps = test_steps[i] if i < len(test_steps) else []
        out = solution[i] if i < len(solution) else None
        samples.append((f"test {i + 1}", sample["input"], sample_steps, out))

    n_samples = max(len(samples), 1)
    n_intermediates = 0
    for _, _, sample_steps, _ in samples:
        if len(sample_steps) > 1:
            n_intermediates = max(n_intermediates, len(sample_steps) - 1)
    n_grid_rows = 1 + n_intermediates + 1  # input + intermediates + output
    n_cache = max(len(cache), 1)

    fig_w = max(3.2 * n_samples, 3.0 * n_cache, 8)
    fig_h = 1.0 + 2.4 + 0.35 + 2.2 * n_grid_rows + 1.8
    fig = plt.figure(figsize=(fig_w, fig_h), facecolor="white")
    outer = fig.add_gridspec(
        4,
        1,
        height_ratios=[0.3, 2.2, 0.35 + 2.2 * n_grid_rows, 1.6],
        hspace=0.4,
        left=0.08,
        right=0.98,
        top=0.95,
        bottom=0.04,
    )

    title = f"Puzzle {puzzle_id}"
    if generated_at:
        title = f"{title}  ·  {generated_at}"
    fig.suptitle(title, fontsize=14, fontweight="bold", y=0.985)

    # Cache section (subtitle + per-item header/summary/visual)
    cache_block = outer[1].subgridspec(2, 1, height_ratios=[0.18, 1.0], hspace=0.08)
    ax_cache_title = fig.add_subplot(cache_block[0])
    ax_cache_title.axis("off")
    ax_cache_title.set_title("Cache", loc="left", fontsize=11, fontweight="bold", pad=2)

    cache_items = list(cache.items()) or [("∅", None)]
    items_gs = cache_block[1].subgridspec(1, n_cache, wspace=0.45)
    for i, (key, value) in enumerate(cache_items):
        feat = cache_features.get(key)
        kind = cache_kind_label(feat, value)
        summary = cache_value_summary(feat, value) if value is not None else "(empty)"
        has_visual = value is not None and (_is_int_grid(value) or _is_placement_list(value))

        if has_visual:
            item_gs = items_gs[0, i].subgridspec(2, 1, height_ratios=[0.4, 1.0], hspace=0.12)
            ax_label = fig.add_subplot(item_gs[0])
            ax_vis = fig.add_subplot(item_gs[1])
            plot_cache_visual(ax_vis, value)
        else:
            ax_label = fig.add_subplot(items_gs[0, i])
            ax_vis = None

        ax_label.axis("off")
        ax_label.text(
            0.0,
            1.0,
            f"'{key}' ({kind})\n{summary}",
            ha="left",
            va="top",
            fontsize=10,
            transform=ax_label.transAxes,
            linespacing=1.35,
        )

    # Samples section (subtitle + columns for input / intermediates / output)
    samples_block = outer[2].subgridspec(2, 1, height_ratios=[0.18, 2.2 * n_grid_rows], hspace=0.08)
    ax_samples_title = fig.add_subplot(samples_block[0])
    ax_samples_title.axis("off")
    ax_samples_title.set_title("Samples", loc="left", fontsize=11, fontweight="bold", pad=2)

    sample_gs = samples_block[1].subgridspec(n_grid_rows, n_samples, wspace=0.25, hspace=0.35)
    row_labels = ["input"]
    for i in range(n_intermediates):
        row_labels.append(f"step {i + 1}")
    row_labels.append("output")

    for col, (sample_name, inp, sample_steps, out) in enumerate(samples):
        intermediates = sample_steps[:-1] if len(sample_steps) > 1 else []
        final = out if out is not None else (sample_steps[-1] if sample_steps else None)

        row_values: list[Any] = [inp]
        for i in range(n_intermediates):
            row_values.append(intermediates[i] if i < len(intermediates) else None)
        row_values.append(final)

        for row, value in enumerate(row_values):
            ax = fig.add_subplot(sample_gs[row, col])
            sample_title = sample_name if row == 0 else ""
            if value is None:
                ax.axis("off")
                if row == n_grid_rows - 1 and sample_name.startswith("test"):
                    ax.text(0.5, 0.5, "(no output)", ha="center", va="center", color="gray", transform=ax.transAxes)
            else:
                # Intermediate arrangement steps use index-grid style; objects use ARC colors.
                if 0 < row < n_grid_rows - 1 and (
                    _is_arrangement_step(value) or _is_placement_list(value)
                ):
                    label = f"{sample_title}" if sample_title else ""
                    plot_step_visual(ax, value, title=label)
                    if not sample_title:
                        ax.set_title("arrangement", fontsize=9, color="0.35")
                else:
                    plot_step_visual(ax, value, title=sample_title)
            if col == 0:
                ylabel = row_labels[row]
                if 0 < row < n_grid_rows - 1:
                    step_val = row_values[row]
                    if step_val is not None and (
                        _is_arrangement_step(step_val) or _is_placement_list(step_val)
                    ):
                        ylabel = f"{ylabel}\n(arr.)"
                ax.set_ylabel(ylabel, fontsize=10, rotation=0, labelpad=28, va="center")

    # Description
    ax_desc = fig.add_subplot(outer[3])
    ax_desc.axis("off")
    lines: list[str] = []
    for line in description.get("input") or []:
        lines.append(line)
    for i, line in enumerate(description.get("steps") or [], start=1):
        lines.append(f"{i}. {line}")
    text = "\n".join(lines) if lines else "(no description)"
    ax_desc.text(
        0.0,
        1.0,
        text,
        ha="left",
        va="top",
        fontsize=10,
        wrap=True,
        transform=ax_desc.transAxes,
        family="sans-serif",
    )
    ax_desc.set_title("Description", loc="left", fontsize=11, fontweight="bold", pad=8)

    return fig
