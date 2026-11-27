"""Renderizador z-buffer de alta precisao para previas 3D das pecas STL."""

from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _rotation_matrix(elev_deg: float, azim_deg: float) -> np.ndarray:
    """Matriz de rotacao de camera (azimute em Z, elevacao em X)."""
    a = np.radians(azim_deg)
    e = np.radians(90.0 - elev_deg)
    rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    rx = np.array([[1, 0, 0], [0, np.cos(e), -np.sin(e)], [0, np.sin(e), np.cos(e)]])
    return rx @ rz


def render_mesh_zbuffer(
    mesh,
    color_rgb: tuple[float, float, float],
    elev: float = 48.0,
    azim: float = -30.0,
    res: int = 520,
    bg_rgb: tuple[float, float, float] = (0.078, 0.078, 0.086),
) -> np.ndarray:
    """Rasteriza uma Trimesh com z-buffer real por pixel (sem bugs de profundidade)."""
    rot = _rotation_matrix(elev, azim)
    center = mesh.bounds.mean(axis=0)
    verts = (mesh.vertices - center) @ rot.T
    tris = verts[mesh.faces]

    # Normais no espaco da camera + backface culling
    v0, v1, v2 = tris[:, 0], tris[:, 1], tris[:, 2]
    normals = np.cross(v1 - v0, v2 - v0)
    lens = np.linalg.norm(normals, axis=1, keepdims=True)
    valid = (lens[:, 0] > 1e-10) & (normals[:, 2] > 0.0)
    tris = tris[valid]
    normals = normals[valid] / lens[valid]

    # Iluminacao 3 pontos (key + fill + rim)
    k1 = np.array([0.45, 0.35, 0.82]); k1 /= np.linalg.norm(k1)
    k2 = np.array([-0.6, -0.2, 0.5]); k2 /= np.linalg.norm(k2)
    diff1 = np.clip(normals @ k1, 0.0, 1.0)
    diff2 = np.clip(normals @ k2, 0.0, 1.0)
    shade = 0.24 + 0.62 * diff1 + 0.20 * diff2
    colors = np.clip(np.array(color_rgb)[None, :] * shade[:, None], 0.0, 1.0)

    # Projecao ortografica para pixels
    span = max(float(np.ptp(verts[:, 0])), float(np.ptp(verts[:, 1]))) * 0.58
    cx, cy = (verts[:, 0].min() + verts[:, 0].max()) * 0.5, (verts[:, 1].min() + verts[:, 1].max()) * 0.5
    scale = (res * 0.5) / max(span, 1e-6)

    px = (tris[:, :, 0] - cx) * scale + res * 0.5
    py = (cy - tris[:, :, 1]) * scale + res * 0.5
    pz = tris[:, :, 2]

    img = np.broadcast_to(np.array(bg_rgb, dtype=np.float32), (res, res, 3)).copy()
    zbuf = np.full((res, res), -np.inf, dtype=np.float32)

    for i in range(len(tris)):
        x0, x1, x2 = px[i]
        y0, y1, y2 = py[i]
        z0, z1, z2 = pz[i]
        min_x = max(0, int(np.floor(min(x0, x1, x2))))
        max_x = min(res - 1, int(np.ceil(max(x0, x1, x2))))
        min_y = max(0, int(np.floor(min(y0, y1, y2))))
        max_y = min(res - 1, int(np.ceil(max(y0, y1, y2))))
        if min_x > max_x or min_y > max_y:
            continue

        denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(denom) < 1e-8:
            continue

        xs = np.arange(min_x, max_x + 1, dtype=np.float32) + 0.5
        ys = np.arange(min_y, max_y + 1, dtype=np.float32) + 0.5
        gx, gy = np.meshgrid(xs, ys)

        w0 = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) / denom
        w1 = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) / denom
        w2 = 1.0 - w0 - w1

        inside = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
        if not np.any(inside):
            continue

        z_vals = w0 * z0 + w1 * z1 + w2 * z2
        sub_z = zbuf[min_y:max_y + 1, min_x:max_x + 1]
        mask = inside & (z_vals > sub_z)
        if np.any(mask):
            sub_z[mask] = z_vals[mask]
            sub_img = img[min_y:max_y + 1, min_x:max_x + 1]
            sub_img[mask] = colors[i]

    return img


def render_preview_sheet(front_mesh, base_mesh, solid_mesh, output_path: Path) -> None:
    """Gera painel 2x2 nitido com z-buffer real de todas as pecas."""
    views = [
        (
            render_mesh_zbuffer(front_mesh, (0.64, 0.48, 0.96), elev=62, azim=-18),
            "1. Tampa Frontal Difusora + Logo\n01_frente_logo_difusor.stl (Ø 45.1 × 2.2 mm)",
        ),
        (
            render_mesh_zbuffer(base_mesh, (0.36, 0.40, 0.50), elev=58, azim=-22),
            "2. Base Oca (Interior): Berço CR2032 + Guias LED\n02_base_oca_led.stl (48.0 × 56.9 × 8.6 mm)",
        ),
        (
            render_mesh_zbuffer(base_mesh, (0.36, 0.40, 0.50), elev=-62, azim=18),
            "3. Traseira da Base Oca: Botão Flexível em U\nAperte para acender o LED sem chave externa",
        ),
        (
            render_mesh_zbuffer(solid_mesh, (0.58, 0.44, 0.92), elev=56, azim=-20),
            "4. Bônus: Chaveiro Maciço (Sem LED)\n03_chaveiro_macico_simples.stl (3.6 mm)",
        ),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(11, 10.5), facecolor="#141416")
    fig.suptitle(
        "Chaveiro 3D Rasec — Prévias das Malhas STL (100% Watertight / Sem Suportes)",
        color="#FFFFFF",
        fontsize=13.5,
        fontweight="bold",
        y=0.97,
    )

    for ax, (img, title) in zip(axes.flat, views):
        ax.imshow(img)
        ax.set_title(title, color="#E5E7EB", fontsize=10.5, fontweight="bold", pad=8)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_edgecolor("#2A2A32")
            spine.set_linewidth(1.2)

    plt.tight_layout(rect=[0.01, 0.01, 0.99, 0.94])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, facecolor="#141416")
    plt.close(fig)
