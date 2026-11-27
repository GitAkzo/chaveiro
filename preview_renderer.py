"""Renderizador z-buffer de alta precisao para previas 3D do chaveiro pedestal LED."""

from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _rotation_matrix(elev_deg: float, azim_deg: float) -> np.ndarray:
    a = np.radians(azim_deg)
    e = np.radians(90.0 - elev_deg)
    rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    # Rx(-e) projeta +Z para +Y na tela (em pe / upright)
    rx = np.array([[1, 0, 0], [0, np.cos(-e), -np.sin(-e)], [0, np.sin(-e), np.cos(-e)]])
    return rx @ rz


def render_scene_zbuffer(
    items: list[tuple[object, tuple[float, float, float]]],
    elev: float = 22.0,
    azim: float = -24.0,
    res: int = 520,
    bg_rgb: tuple[float, float, float] = (0.078, 0.078, 0.086),
) -> np.ndarray:
    """Rasteriza uma ou mais Trimesh juntas com z-buffer real por pixel."""
    rot = _rotation_matrix(elev, azim)
    all_pts = np.vstack([m.vertices for m, _ in items])
    center = (all_pts.min(axis=0) + all_pts.max(axis=0)) * 0.5

    # Calcula span global no espaco da camera
    rot_all = (all_pts - center) @ rot.T
    span = max(float(np.ptp(rot_all[:, 0])), float(np.ptp(rot_all[:, 1]))) * 0.58
    cx = (rot_all[:, 0].min() + rot_all[:, 0].max()) * 0.5
    cy = (rot_all[:, 1].min() + rot_all[:, 1].max()) * 0.5
    scale = (res * 0.5) / max(span, 1e-6)

    k1 = np.array([0.42, 0.35, 0.84]); k1 /= np.linalg.norm(k1)
    k2 = np.array([-0.60, -0.25, 0.50]); k2 /= np.linalg.norm(k2)

    img = np.broadcast_to(np.array(bg_rgb, dtype=np.float32), (res, res, 3)).copy()
    zbuf = np.full((res, res), -np.inf, dtype=np.float32)

    for mesh, color_rgb in items:
        verts = (mesh.vertices - center) @ rot.T
        tris = verts[mesh.faces]
        v0, v1, v2 = tris[:, 0], tris[:, 1], tris[:, 2]
        normals = np.cross(v1 - v0, v2 - v0)
        lens = np.linalg.norm(normals, axis=1, keepdims=True)
        valid = (lens[:, 0] > 1e-10) & (normals[:, 2] > 0.0)
        tris = tris[valid]
        normals = normals[valid] / lens[valid]

        diff1 = np.clip(normals @ k1, 0.0, 1.0)
        diff2 = np.clip(normals @ k2, 0.0, 1.0)
        shade = 0.24 + 0.62 * diff1 + 0.20 * diff2
        colors = np.clip(np.array(color_rgb)[None, :] * shade[:, None], 0.0, 1.0)

        px = (tris[:, :, 0] - cx) * scale + res * 0.5
        py = (cy - tris[:, :, 1]) * scale + res * 0.5
        pz = tris[:, :, 2]

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


def _pose_assembled(logo_mesh, base_mesh, lid_mesh, base_h: float, logo_t: float, explode: float = 0.0):
    """Posiciona as 3 pecas em pe (como na foto de referencia) ou explodidas."""
    # Base: na impressao z=0 e o topo; gira 180 em X e sobe base_h para ficar em pe (z=0..base_h)
    base_up = base_mesh.copy()
    rot_x180 = np.array([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, base_h], [0, 0, 0, 1]], dtype=float)
    base_up.apply_transform(rot_x180)

    # Logo: na impressao esta deitada em XY (espessura em Z=0..logo_t); gira +90 em X para ficar em pe em XZ
    logo_up = logo_mesh.copy()
    logo_up.apply_translation([0.0, 0.0, -logo_t / 2.0])
    rot_x90 = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=float)
    logo_up.apply_transform(rot_x90)
    logo_up.apply_translation([0.0, 0.0, base_h + explode])

    # Tampa inferior: encaixa em z=0 da base
    lid_up = lid_mesh.copy()
    lid_up.apply_translation([0.0, 0.0, -explode * 0.7])
    return logo_up, base_up, lid_up


def render_preview_sheet(logo_mesh, base_mesh, lid_mesh, spec, output_path: Path) -> None:
    """Gera painel 2x2: Montado (frente), Explodido 3D, Interior da Base Oca e Tampa Inferior."""
    logo_m, base_m, lid_m = _pose_assembled(
        logo_mesh, base_mesh, lid_mesh, spec.base_h, spec.logo_thickness, explode=0.0
    )
    logo_e, base_e, lid_e = _pose_assembled(
        logo_mesh, base_mesh, lid_mesh, spec.base_h, spec.logo_thickness, explode=10.0
    )

    purple = (0.76, 0.42, 0.98)
    charcoal = (0.24, 0.25, 0.29)
    slate = (0.34, 0.36, 0.42)

    views = [
        (
            render_scene_zbuffer([(base_m, charcoal), (logo_m, purple), (lid_m, slate)], elev=16, azim=-18),
            "1. Montado (Frente 3/4 — Estilo Referência)\nLogo Translúcida em Pé + Base Oca Preta + Alça Lateral",
        ),
        (
            render_scene_zbuffer([(base_e, charcoal), (logo_e, purple), (lid_e, slate)], elev=24, azim=-34),
            "2. Vista Explodida das 3 Peças (Zero Suportes)\nLogo (Espigas) + Base Oca (Slots) + Tampa com Botão",
        ),
        (
            render_scene_zbuffer([(base_mesh, slate)], elev=58, azim=-24),
            "3. Interior da Base Oca (02_base_pedestal_led.stl)\nBerço CR2032 + Colar Guia LED 5mm/3mm sob o 'R'",
        ),
        (
            render_scene_zbuffer([(lid_mesh, slate)], elev=54, azim=-24),
            "4. Tampa Inferior (03_tampa_inferior_botao.stl)\nBotão Flexível em U + Pino Atuador + Travas Laterais",
        ),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(11, 10.5), facecolor="#141416")
    fig.suptitle(
        "Chaveiro 3D Rasec v2 — Estilo Mini Luminária LED (Base Oca + Logo em Pé)",
        color="#FFFFFF",
        fontsize=13.5,
        fontweight="bold",
        y=0.97,
    )

    for ax, (img, title) in zip(axes.flat, views):
        ax.imshow(img)
        ax.set_title(title, color="#E5E7EB", fontsize=10.2, fontweight="bold", pad=8)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_edgecolor("#2A2A32")
            spine.set_linewidth(1.2)

    plt.tight_layout(rect=[0.01, 0.01, 0.99, 0.94])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, facecolor="#141416")
    plt.close(fig)
