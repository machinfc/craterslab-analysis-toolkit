from __future__ import annotations

from craterslab.ellipse import EllipseVisualConfig
from craterslab.visuals import plot_2D, plot_3D, plot_profile
from matplotlib import pyplot as plt


def profile_supports_slopes(profile) -> bool:
    try:
        profile.slopes()
    except Exception:  # noqa: BLE001
        return False
    return all(hasattr(profile, attr) for attr in ("t1", "t2", "b1", "b2"))


def plot_profile_safe(profile, block: bool = True) -> bool:
    draw_slopes = profile_supports_slopes(profile)
    plot_profile(profile, draw_slopes=draw_slopes, block=block)
    return draw_slopes


def show_review_figures(
    *,
    depth_map,
    profile,
    ellipse_model,
    surface,
    show_2d: bool,
    show_profile: bool,
    show_3d: bool,
    preview_scale: tuple[float, float, float] = (1, 1, 4),
) -> bool:
    """Open all requested figures for a file and block only once.

    This lets the user compare 2D, profile, and 3D views at the same time.
    """
    slopes_drawn = True

    if show_2d:
        plot_2D(depth_map, profile=profile, ellipse=ellipse_model, block=False)

    if show_profile:
        slopes_drawn = plot_profile_safe(profile, block=False)

    if show_3d:
        if (
            surface is not None
            and getattr(surface, "observables", None)
            and "mean_h_rim" in surface.observables
        ):
            ellipse_config = EllipseVisualConfig(
                color="blue",
                fill=True,
                z_val=surface.observables["mean_h_rim"].value,
                alpha=0.5,
            )
            plot_3D(
                depth_map,
                ellipse=surface.em,
                preview_scale=preview_scale,
                ellipse_config=ellipse_config,
                block=False,
            )
        else:
            plot_3D(
                depth_map,
                ellipse=ellipse_model,
                preview_scale=preview_scale,
                block=False,
            )

    if show_2d or show_profile or show_3d:
        plt.show(block=True)

    return slopes_drawn
