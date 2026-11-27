"""Extrai a silhueta vetorial da logo em milimetros com reforco para FDM 0.4mm."""

from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from shapely.geometry import Polygon
from shapely.ops import unary_union


def load_logo_polygons(
    image_path: Path,
    target_width_mm: float = 36.0,
    min_stroke_boost_mm: float = 0.20,
    simplify_tol_mm: float = 0.08,
) -> tuple[Polygon, tuple[float, float]]:
    """Converte a logo PNG em poligonos Shapely centrados em (0, 0) em mm."""
    img = Image.open(image_path).convert("RGBA")
    arr = np.array(img)
    alpha = arr[:, :, 3]

    # Mascara binaria limpa com leve suavizacao para evitar serrilhado
    mask = (alpha > 100).astype(np.uint8) * 255
    mask = cv2.GaussianBlur(mask, (5, 5), 0)
    _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

    # Recorta pelo bounding box da logo com margem
    ys, xs = np.where(mask > 0)
    pad = 24
    y0, y1 = max(0, ys.min() - pad), min(mask.shape[0], ys.max() + pad)
    x0, x1 = max(0, xs.min() - pad), min(mask.shape[1], xs.max() + pad)
    crop = mask[y0:y1, x0:x1]

    logo_w_px = float(xs.max() - xs.min())
    logo_h_px = float(ys.max() - ys.min())
    mm_per_px = target_width_mm / logo_w_px
    target_height_mm = logo_h_px * mm_per_px

    # Reforco leve nas hastes finas do grafo para impressao 3D confiavel (bico 0.4mm)
    if min_stroke_boost_mm > 0:
        dilate_px = max(1, int(round(min_stroke_boost_mm / mm_per_px)))
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (2 * dilate_px + 1, 2 * dilate_px + 1)
        )
        crop = cv2.dilate(crop, kernel, iterations=1)

    contours, hierarchy = cv2.findContours(
        crop, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE
    )
    if hierarchy is None:
        raise ValueError("Nenhum contorno encontrado na imagem da logo.")

    hierarchy = hierarchy[0]
    h_crop, w_crop = crop.shape
    cx_px = (xs.min() + xs.max()) / 2.0 - x0
    cy_px = (ys.min() + ys.max()) / 2.0 - y0

    def to_mm_coords(contour: np.ndarray) -> list[tuple[float, float]]:
        pts = contour.reshape(-1, 2)
        return [
            ((float(x) - cx_px) * mm_per_px, (cy_px - float(y)) * mm_per_px)
            for x, y in pts
        ]

    polygons = []
    for idx, hier in enumerate(hierarchy):
        parent = hier[3]
        if parent != -1:
            continue
        shell = to_mm_coords(contours[idx])
        if len(shell) < 4:
            continue
        holes = []
        child = hier[2]
        while child != -1:
            hole_pts = to_mm_coords(contours[child])
            if len(hole_pts) >= 4:
                holes.append(hole_pts)
            child = hierarchy[child][0]

        poly = Polygon(shell, holes).buffer(0)
        if not poly.is_empty and poly.area > 0.5:
            polygons.append(poly)

    merged = unary_union(polygons).buffer(0)
    merged = merged.simplify(simplify_tol_mm, preserve_topology=True).buffer(0)
    return merged, (target_width_mm, target_height_mm)
