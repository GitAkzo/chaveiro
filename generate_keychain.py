"""Gera os arquivos STL (v2 - estilo mini luminaria LED) e valida todas as malhas."""

from pathlib import Path
from logo_extractor import load_logo_polygons
from keychain_builder import (
    PedestalKeychainSpec,
    build_standing_logo,
    build_pedestal_base,
    build_bottom_lid,
)
from preview_renderer import render_preview_sheet


PROJECT_DIR = Path(__file__).resolve().parent
LOGO_PATH = PROJECT_DIR / "assets" / "logo_rasec.png"
OUT_DIR = PROJECT_DIR / "stl"


def _report_mesh(name: str, mesh) -> None:
    ext = mesh.extents
    vol_cm3 = abs(mesh.volume) / 1000.0
    pla_g = vol_cm3 * 1.24
    print(
        f"[{name}] watertight={mesh.is_watertight} | "
        f"faces={len(mesh.faces)} | "
        f"dims={ext[0]:.1f}x{ext[1]:.1f}x{ext[2]:.1f} mm | "
        f"vol={vol_cm3:.2f} cm3 (~{pla_g:.1f}g PLA)"
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    spec = PedestalKeychainSpec()

    print("1/4 Extraindo silhueta vetorial da logo com reforco estrutural...")
    logo_poly, (lw, lh) = load_logo_polygons(
        LOGO_PATH,
        target_width_mm=spec.logo_width,
        min_stroke_boost_mm=0.35,
        simplify_tol_mm=0.08,
    )
    print(f"    Logo extraida: {lw:.1f} x {lh:.1f} mm | area={logo_poly.area:.1f} mm2")

    print("2/4 Construindo malhas 3D manifold (v2 Pedestal LED)...")
    logo_mesh, left_tab_x, right_tab_x = build_standing_logo(logo_poly, spec)
    base_mesh = build_pedestal_base(left_tab_x, right_tab_x, spec)
    lid_mesh = build_bottom_lid(spec)

    print("3/4 Exportando arquivos STL...")
    exports = [
        ("01_logo_translucida_vertical.stl", logo_mesh),
        ("02_base_pedestal_led.stl", base_mesh),
        ("03_tampa_inferior_botao.stl", lid_mesh),
    ]
    for filename, mesh in exports:
        out_file = OUT_DIR / filename
        mesh.export(out_file)
        _report_mesh(filename, mesh)
        if not mesh.is_watertight:
            raise RuntimeError(f"Malha {filename} nao e estanque (watertight)!")

    print("4/4 Renderizando painel de previa 3D...")
    render_preview_sheet(logo_mesh, base_mesh, lid_mesh, spec, PROJECT_DIR / "preview_chaveiro_3d_v2.png")
    print("Concluido com sucesso!")


if __name__ == "__main__":
    main()
