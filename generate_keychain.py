"""Gera os arquivos STL prontos para impressao 3D e valida todas as malhas."""

from pathlib import Path
from logo_extractor import load_logo_polygons
from keychain_builder import (
    KeychainSpec,
    build_front_diffuser,
    build_hollow_base,
    build_solid_keychain,
)
from preview_renderer import render_preview_sheet


LOGO_PATH = Path(
    r"C:/Users/Raséc/.gemini/antigravity/brain/bdfb3865-ff3b-4362-aa15-286dbca20411/.user_uploaded/media_1795796779513_933cc167.png"
)
PROJECT_DIR = Path(r"C:\Users\Raséc\.gemini\antigravity\scratch\chaveiro-3d-rasec")
OUT_DIR = PROJECT_DIR / "stl"
ARTIFACT_PREVIEW = Path(
    r"C:/Users/Raséc/.gemini/antigravity/brain/bdfb3865-ff3b-4362-aa15-286dbca20411/preview_chaveiro_3d.png"
)


def _report_mesh(name: str, mesh) -> None:
    ext = mesh.extents
    vol_cm3 = abs(mesh.volume) / 1000.0
    pla_g = vol_cm3 * 1.24  # densidade PLA ~1.24 g/cm3 (estimativa 100% solido)
    print(
        f"[{name}] watertight={mesh.is_watertight} | "
        f"faces={len(mesh.faces)} | "
        f"dims={ext[0]:.1f}x{ext[1]:.1f}x{ext[2]:.1f} mm | "
        f"vol={vol_cm3:.2f} cm3 (~{pla_g:.1f}g PLA)"
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    spec = KeychainSpec()

    print("1/4 Extraindo silhueta vetorial da logo...")
    logo_poly, (lw, lh) = load_logo_polygons(
        LOGO_PATH,
        target_width_mm=31.0,
        min_stroke_boost_mm=0.22,
        simplify_tol_mm=0.08,
    )
    print(f"    Logo extraida: {lw:.1f} x {lh:.1f} mm | area={logo_poly.area:.1f} mm2")

    print("2/4 Construindo malhas 3D manifold...")
    front_mesh = build_front_diffuser(logo_poly, spec)
    base_mesh = build_hollow_base(spec)
    solid_mesh = build_solid_keychain(logo_poly, spec)

    print("3/4 Exportando arquivos STL...")
    exports = [
        ("01_frente_logo_difusor.stl", front_mesh),
        ("02_base_oca_led.stl", base_mesh),
        ("03_chaveiro_macico_simples.stl", solid_mesh),
    ]
    for filename, mesh in exports:
        out_file = OUT_DIR / filename
        mesh.export(out_file)
        _report_mesh(filename, mesh)
        if not mesh.is_watertight:
            raise RuntimeError(f"Malha {filename} nao e estanque (watertight)!")

    print("4/4 Renderizando painel de previa 3D...")
    render_preview_sheet(front_mesh, base_mesh, solid_mesh, PROJECT_DIR / "preview_chaveiro_3d.png")
    render_preview_sheet(front_mesh, base_mesh, solid_mesh, ARTIFACT_PREVIEW)
    print("Concluido com sucesso!")


if __name__ == "__main__":
    main()
