"""Matplotlib helpers for rendering ARC-style grids and generated puzzles."""

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import ListedColormap
from matplotlib.figure import Figure

from sparc_agi.features.base import Feature
from sparc_agi.features.scalars.orientation import Orientation
from sparc_agi.range import RangeSpec
from sparc_agi.geometry import Geometry
from sparc_agi.palette import ARC_COLORS

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
    """Draw a sample step: ARC object grid, arrangement index grid, or color swatch."""
    if isinstance(value, Geometry):
        plot_arc_grid(ax, value.to_grid(background=0), title=title)
        return
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
    if isinstance(value, int) and not isinstance(value, bool):
        # Scalar color: swatch so the step row isn't an empty gap.
        plot_arc_grid(ax, [[value] * 3 for _ in range(3)], title=title or f"color {value}")
        return
    ax.axis("off")
    if title:
        ax.set_title(title, fontsize=9, pad=2)

def plot_arc_grid(ax: Axes, grid_data: list[list[int]], title: str = "") -> None:
    """Draw an ARC color grid with light cell borders."""
    if not grid_data or not grid_data[0]:
        ax.axis("off")
        if title:
            ax.set_title(title, fontsize=9, pad=2)
        return

    grid = np.asarray(grid_data, dtype=int)
    display = np.clip(grid, 0, len(ARC_COLORS) - 1)
    ax.imshow(
        display,
        cmap=ARC_CMAP,
        vmin=0,
        vmax=len(ARC_COLORS) - 1,
        interpolation="nearest",
        aspect="equal",
    )
    # Keep cells square even when the gridspec slot is tall/wide.
    ax.set_box_aspect(grid.shape[0] / max(grid.shape[1], 1))
    ax.set_xticks(np.arange(-0.5, grid.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-0.5, grid.shape[0], 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=0.6)
    ax.tick_params(which="both", bottom=False, left=False, labelbottom=False, labelleft=False)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.5)
    if title:
        ax.set_title(title, fontsize=8, pad=1)

def plot_index_grid(ax: Axes, grid_data: list[list[int]], title: str = "") -> None:
    """Draw a small integer grid (e.g. pool indices) with cell labels."""
    if not grid_data or not grid_data[0]:
        ax.axis("off")
        if title:
            ax.set_title(title, fontsize=9, pad=2)
        return

    grid = np.asarray(grid_data, dtype=float)
    masked = np.ma.masked_where(grid < 0, grid)
    present = grid[grid >= 0]
    vmax = float(present.max()) if present.size else 1.0
    ax.imshow(
        masked,
        cmap="Blues",
        vmin=-0.5,
        vmax=max(vmax, 1.0),
        interpolation="nearest",
        aspect="equal",
    )
    ax.set_box_aspect(grid.shape[0] / max(grid.shape[1], 1))
    for y in range(grid.shape[0]):
        for x in range(grid.shape[1]):
            val = int(grid[y, x])
            label = "·" if val < 0 else str(val)
            # Blues: low values are light, high values are dark — pick contrasting ink.
            if val < 0:
                ink = "0.45"
            else:
                ink = "white" if (val / max(vmax, 1.0)) > 0.35 else "black"
            ax.text(x, y, label, ha="center", va="center", fontsize=8, color=ink, fontweight="bold")
    ax.set_xticks(np.arange(-0.5, grid.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-0.5, grid.shape[0], 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=0.6)
    ax.tick_params(which="both", bottom=False, left=False, labelbottom=False, labelleft=False)
    if title:
        ax.set_title(title, fontsize=8, pad=1)

def _orientation_short_label(direction: int) -> str:
    phrase = Orientation(value=RangeSpec(direction)).describe()
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
    if _is_arrangement_step(value) or _is_placement_list(value):
        return "arrangement"
    if _is_int_grid(value):
        return "object"
    return "value"

def _cache_value_empty(value: Any) -> bool:
    return value is None or value == {} or value == [] or value == ()

def cache_value_summary(feature: Feature | None, value: Any) -> str:
    """Short natural-language line under the cache key header."""
    if _cache_value_empty(value):
        return "(empty)"
    if feature is not None and type(feature).__feature_family__ == "orientation":
        if isinstance(value, int) and not isinstance(value, bool):
            return _orientation_short_label(value)
    if feature is not None and type(feature).__feature_family__ == "arrangement":
        return feature.describe()
    if isinstance(value, int) and not isinstance(value, bool):
        return _orientation_short_label(value)
    if _is_arrangement_step(value):
        placements = value.get("placements") or []
        return f"{len(placements)} placements"
    if _is_placement_list(value):
        return f"{len(value)} placements"
    if _is_int_grid(value):
        h = len(value)
        w = len(value[0]) if value else 0
        return f"{w}x{h} grid"
    if feature is not None and type(feature).__feature_family__ == "filter":
        return feature.describe()
    return repr(value)

def plot_cache_visual(ax: Axes, value: Any) -> bool:
    """Draw cache visual content. Returns False when there is nothing visual to show."""
    if _is_int_grid(value):
        plot_arc_grid(ax, value)
        return True
    if _is_arrangement_step(value):
        placements = value.get("placements") or []
        plot_index_grid(
            ax,
            placements_to_index_grid(
                placements,
                width=value.get("width"),
                height=value.get("height"),
            ),
        )
        return True
    if _is_placement_list(value):
        plot_index_grid(ax, placements_to_index_grid(value))
        return True
    ax.axis("off")
    return False

def _cache_has_visual(value: Any) -> bool:
    return (
        value is not None
        and (
            _is_int_grid(value)
            or _is_placement_list(value)
            or _is_arrangement_step(value)
        )
    )

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

    # Cache row tall enough for small glyph grids without horizontal squash.
    cell = 3.4
    label_w = 0.7
    cache_slot = 1.6
    fig_w = max(label_w + cell * n_samples, cache_slot * n_cache, 8.0)
    cache_h = 2.4
    samples_h = cell * n_grid_rows
    desc_h = 1.25
    title_h = 0.28
    fig_h = title_h + cache_h + samples_h + desc_h
    fig = plt.figure(figsize=(fig_w, fig_h), facecolor="white")
    outer = fig.add_gridspec(
        4,
        1,
        height_ratios=[title_h, cache_h, samples_h, desc_h],
        hspace=0.08,
        left=0.045,
        right=0.998,
        top=0.98,
        bottom=0.015,
    )

    title = f"Puzzle {puzzle_id}"
    if generated_at:
        title = f"{title}  ·  {generated_at}"
    fig.suptitle(title, fontsize=15, fontweight="bold", y=0.995)

    # Cache section (subtitle + per-item header/summary/visual)
    cache_block = outer[1].subgridspec(2, 1, height_ratios=[0.14, 1.0], hspace=0.04)
    ax_cache_title = fig.add_subplot(cache_block[0])
    ax_cache_title.axis("off")
    ax_cache_title.set_title("Cache", loc="left", fontsize=13, fontweight="bold", pad=0)

    cache_items = list(cache.items())
    if not cache_items:
        ax_empty = fig.add_subplot(cache_block[1])
        ax_empty.axis("off")
        ax_empty.text(
            0.0,
            1.0,
            "(empty)",
            ha="left",
            va="top",
            fontsize=11,
            transform=ax_empty.transAxes,
        )
    else:
        items_gs = cache_block[1].subgridspec(1, len(cache_items), wspace=0.35)
        for i, (key, value) in enumerate(cache_items):
            feat = cache_features.get(key)
            kind = cache_kind_label(feat, value)
            summary = cache_value_summary(feat, value)
            has_visual = _cache_has_visual(value)

            if has_visual:
                item_gs = items_gs[0, i].subgridspec(2, 1, height_ratios=[0.28, 1.0], hspace=0.08)
                ax_label = fig.add_subplot(item_gs[0])
                ax_vis = fig.add_subplot(item_gs[1])
                plot_cache_visual(ax_vis, value)
            else:
                ax_label = fig.add_subplot(items_gs[0, i])

            ax_label.axis("off")
            ax_label.text(
                0.0,
                1.0,
                f"'{key}' ({kind})\n{summary}",
                ha="left",
                va="top",
                fontsize=11,
                transform=ax_label.transAxes,
                linespacing=1.25,
            )

    # Samples section (subtitle + header row + labeled grid)
    samples_block = outer[2].subgridspec(2, 1, height_ratios=[0.1, samples_h], hspace=0.01)
    ax_samples_title = fig.add_subplot(samples_block[0])
    ax_samples_title.axis("off")
    ax_samples_title.set_title("Samples", loc="left", fontsize=13, fontweight="bold", pad=0)

    sample_gs = samples_block[1].subgridspec(
        n_grid_rows + 1,
        n_samples + 1,
        width_ratios=[0.45] + [1.0] * n_samples,
        height_ratios=[0.18] + [1.0] * n_grid_rows,
        wspace=0.015,
        hspace=0.02,
    )
    row_labels = ["input"]
    for i in range(n_intermediates):
        row_labels.append(f"step {i + 1}")
    row_labels.append("output")

    # Corner + column headers
    ax_corner = fig.add_subplot(sample_gs[0, 0])
    ax_corner.axis("off")
    for col, (sample_name, _, _, _) in enumerate(samples):
        ax_h = fig.add_subplot(sample_gs[0, col + 1])
        ax_h.axis("off")
        ax_h.text(0.5, 0.15, sample_name, ha="center", va="bottom", fontsize=10, transform=ax_h.transAxes)

    for col, (sample_name, inp, sample_steps, out) in enumerate(samples):
        intermediates = sample_steps[:-1] if len(sample_steps) > 1 else []
        final = out if out is not None else (sample_steps[-1] if sample_steps else None)

        row_values: list[Any] = [inp]
        for i in range(n_intermediates):
            row_values.append(intermediates[i] if i < len(intermediates) else None)
        row_values.append(final)

        for row, value in enumerate(row_values):
            if col == 0:
                ax_lab = fig.add_subplot(sample_gs[row + 1, 0])
                ax_lab.axis("off")
                ylabel = row_labels[row]
                if 0 < row < n_grid_rows - 1:
                    step_val = row_values[row]
                    if step_val is not None and (
                        _is_arrangement_step(step_val) or _is_placement_list(step_val)
                    ):
                        ylabel = f"{ylabel} (arr.)"
                ax_lab.text(
                    0.95,
                    0.5,
                    ylabel,
                    ha="right",
                    va="center",
                    fontsize=10,
                    transform=ax_lab.transAxes,
                )

            ax = fig.add_subplot(sample_gs[row + 1, col + 1])
            if value is None:
                ax.axis("off")
                if row == n_grid_rows - 1 and sample_name.startswith("test"):
                    ax.text(
                        0.5,
                        0.5,
                        "(no output)",
                        ha="center",
                        va="center",
                        color="gray",
                        transform=ax.transAxes,
                    )
            else:
                plot_step_visual(ax, value, title="")

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
        fontsize=11,
        wrap=True,
        transform=ax_desc.transAxes,
        family="sans-serif",
    )
    ax_desc.set_title("Description", loc="left", fontsize=13, fontweight="bold", pad=4)

    return fig
