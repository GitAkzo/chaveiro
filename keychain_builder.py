"""Construcao parametrica 3D: Chaveiro estilo Mini Luminaria (Logo em pe + Base Oca LED)."""

from dataclasses import dataclass
import numpy as np
import trimesh
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
from shapely.affinity import translate


@dataclass(frozen=True)
class PedestalKeychainSpec:
    """Dimensoes em mm — estilo base retangular arredondada + logo vertical translúcida."""
    logo_width: float = 36.0           # Largura da logo em pe
    logo_thickness: float = 3.8        # Espessura da logo (rigida + boa conducao de luz)
    tab_depth: float = 3.2             # Espigas de encaixe que entram na base preta
    slot_clearance: float = 0.25       # Folga para encaixe justo da logo na base

    base_w: float = 42.0               # Largura da base preta
    base_d: float = 25.0               # Profundidade da base preta (cabe CR2032 20mm)
    base_h: float = 13.5               # Altura total da base preta
    corner_r: float = 3.5              # Raio de arredondamento dos cantos da base
    wall_t: float = 2.0                # Espessura das paredes laterais da base
    top_t: float = 2.6                 # Espessura do teto da base (segura a logo firme)
    lid_t: float = 1.6                 # Espessura da tampa inferior encaixavel
    lid_clearance: float = 0.25        # Folga da tampa inferior

    battery_d: float = 20.8            # CR2032 (20.0mm) + folga
    ring_hole_d: float = 4.4           # Furo na lateral direita para argola de chaveiro


def extrude_poly(poly, height: float, z0: float = 0.0) -> trimesh.Trimesh:
    """Extruda Polygon ou MultiPolygon Shapely em malha manifold."""
    geoms = list(poly.geoms) if hasattr(poly, "geoms") else [poly]
    meshes = []
    for g in geoms:
        if g.is_empty or g.area < 1e-4:
            continue
        m = trimesh.creation.extrude_polygon(g, height, engine="earcut")
        if z0 != 0.0:
            m.apply_translation([0.0, 0.0, z0])
        meshes.append(m)
    if not meshes:
        raise ValueError("Geometria vazia ao extrudar poligono.")
    if len(meshes) == 1:
        return meshes[0]
    return trimesh.boolean.union(meshes, engine="manifold")


def _rounded_rect(w: float, d: float, r: float) -> Polygon:
    """Retangulo centrado em (0, 0) com cantos arredondados de raio r."""
    return box(-w / 2.0 + r, -d / 2.0 + r, w / 2.0 - r, d / 2.0 - r).buffer(r, resolution=32)


def _normalize_logo_feet(logo_poly) -> tuple[Polygon, tuple[float, float], tuple[float, float]]:
    """Alinha a base inferior da logo em Y=0 e detecta os 2 pes de apoio (esfera esq + perna R)."""
    minx, miny, maxx, maxy = logo_poly.bounds
    cx = (minx + maxx) / 2.0
    shifted = translate(logo_poly, xoff=-cx, yoff=-miny)

    # Faixa inferior (y entre 0 e 3.5 mm) revela exatamente os dois pes que tocam a base
    foot_band = shifted.intersection(box(-50.0, -0.1, 50.0, 3.5))
    geoms = list(foot_band.geoms) if hasattr(foot_band, "geoms") else [foot_band]
    geoms = sorted([g for g in geoms if g.area > 0.5], key=lambda g: g.bounds[0])

    if len(geoms) >= 2:
        left_foot = (geoms[0].bounds[0], geoms[0].bounds[2])
        right_foot = (geoms[-1].bounds[0], geoms[-1].bounds[2])
    else:
        left_foot = (-13.0, -7.0)
        right_foot = (5.0, 15.0)
    return shifted, left_foot, right_foot


def build_standing_logo(logo_poly, spec: PedestalKeychainSpec) -> tuple[trimesh.Trimesh, tuple[float, float], tuple[float, float]]:
    """Peca 01: Logo em pe com 2 espigas de encaixe (imprime deitada, ZERO suportes)."""
    logo_2d, left_foot, right_foot = _normalize_logo_feet(logo_poly)

    # Espigas discretas descendo abaixo de Y=0 para travar na base e captar luz do LED
    lx0, lx1 = left_foot
    rx0, rx1 = right_foot
    l_cx = (lx0 + lx1) / 2.0
    l_hw = max(1.8, min((lx1 - lx0) * 0.42, 3.0))
    left_tab = box(l_cx - l_hw, -spec.tab_depth, l_cx + l_hw, 1.8)

    r_hw_l = rx0 + 0.5
    r_hw_r = rx1 - 0.5
    if r_hw_r - r_hw_l < 3.0:
        r_cx = (rx0 + rx1) / 2.0
        r_hw_l, r_hw_r = r_cx - 2.2, r_cx + 2.2
    right_tab = box(r_hw_l, -spec.tab_depth, r_hw_r, 1.5)

    full_2d = unary_union([logo_2d, left_tab, right_tab]).buffer(0)
    mesh = extrude_poly(full_2d, spec.logo_thickness, z0=0.0)
    return mesh, (l_cx - l_hw, l_cx + l_hw), (r_hw_l, r_hw_r)


def build_pedestal_base(
    left_tab_x: tuple[float, float],
    right_tab_x: tuple[float, float],
    spec: PedestalKeychainSpec,
) -> trimesh.Trimesh:
    """Peca 02: Base oca retangular arredondada com slots no topo, berco CR2032, LED e alca lateral.

    Orientacao de impressao: z=0 e o TOPO da base (imprime de cabeca para baixo, ZERO suportes!).
    Para visualizacao montada, basta inverter no eixo X (180 graus).
    """
    outer_2d = _rounded_rect(spec.base_w, spec.base_d, spec.corner_r)
    outer_mesh = extrude_poly(outer_2d, spec.base_h, z0=0.0)

    # Alca compacta e discreta no canto traseiro direito (z=0..5.5mm na mesa, ZERO suportes)
    ring_x = spec.base_w / 2.0 + 1.8
    ring_y = -2.0
    loop_outer = Point(ring_x, ring_y).buffer(spec.ring_hole_d / 2.0 + 2.4, resolution=48)
    loop_neck = box(spec.base_w / 2.0 - 3.5, ring_y - 4.4, ring_x, ring_y + 4.4)
    loop_hole = Point(ring_x, ring_y).buffer(spec.ring_hole_d / 2.0, resolution=48)
    loop_2d = unary_union([loop_outer, loop_neck]).buffer(0.6).buffer(-0.6).difference(loop_hole)
    loop_mesh = extrude_poly(loop_2d, 5.5, z0=0.0)
    outer_mesh = trimesh.boolean.union([outer_mesh, loop_mesh], engine="manifold")

    # 1. Cavidade interna oca (z vai de top_t ate base_h + 1)
    inner_w = spec.base_w - 2.0 * spec.wall_t
    inner_d = spec.base_d - 2.0 * spec.wall_t
    cavity_2d = _rounded_rect(inner_w, inner_d, max(1.0, spec.corner_r - spec.wall_t))
    cavity_mesh = extrude_poly(cavity_2d, spec.base_h - spec.top_t + 1.0, z0=spec.top_t)

    # 2. Rebaixo no fundo da base (em z = base_h - lid_t) para tampa encaixar rente
    seat_2d = _rounded_rect(
        spec.base_w - 2.0, spec.base_d - 2.0, max(1.2, spec.corner_r - 1.0)
    )
    seat_mesh = extrude_poly(seat_2d, spec.lid_t + 0.8, z0=spec.base_h - spec.lid_t)

    # 3. Slots no topo (z=0..top_t) para encaixe vertical da logo + passagem de luz do LED
    c = spec.slot_clearance
    half_t = spec.logo_thickness / 2.0 + c
    slot_left = box(left_tab_x[0] - c, -half_t, left_tab_x[1] + c, half_t)
    slot_right = box(right_tab_x[0] - c, -half_t, right_tab_x[1] + c, half_t)
    slots_2d = unary_union([slot_left, slot_right])
    slots_mesh = extrude_poly(slots_2d, spec.top_t + 0.6, z0=-0.3)

    shell = trimesh.boolean.difference(
        [outer_mesh, cavity_mesh, seat_mesh, slots_mesh], engine="manifold"
    )

    # 4. Berco interno posicionador da bateria CR2032 (lado esquerdo/centro)
    bat_cx = -6.5
    bat_r_in = spec.battery_d / 2.0
    bat_r_out = bat_r_in + 1.1
    bat_ring = (
        Point(bat_cx, 0.0).buffer(bat_r_out, resolution=64)
        .difference(Point(bat_cx, 0.0).buffer(bat_r_in, resolution=64))
    )
    # Abre o lado direito do berco para os terminais do LED entrarem facilmente
    bat_open = box(bat_cx + 4.5, -12.0, bat_cx + bat_r_out + 2.0, 12.0)
    bat_cradle_2d = bat_ring.difference(bat_open).intersection(
        _rounded_rect(inner_w + 0.4, inner_d + 0.4, 1.2)
    )
    bat_cradle = extrude_poly(bat_cradle_2d, 4.2, z0=spec.top_t - 0.1)

    # 5. Colar guia para LED 5mm/3mm apontando para cima direto na perna direita do "R"
    led_cx = (right_tab_x[0] + right_tab_x[1]) / 2.0
    led_ring = (
        Point(led_cx, 0.0).buffer(4.0, resolution=48)
        .difference(Point(led_cx, 0.0).buffer(2.75, resolution=48))
    )
    led_notch = box(led_cx - 4.5, -1.8, led_cx, 1.8)
    led_holder_2d = led_ring.difference(led_notch).intersection(
        _rounded_rect(inner_w + 0.4, inner_d + 0.4, 1.2)
    )
    led_holder = extrude_poly(led_holder_2d, 5.5, z0=spec.top_t - 0.1)

    return trimesh.boolean.union([shell, bat_cradle, led_holder], engine="manifold")


def build_bottom_lid(spec: PedestalKeychainSpec) -> trimesh.Trimesh:
    """Peca 03: Tampa inferior encaixavel com botao flexivel em U (imprime plana, ZERO suportes)."""
    c = spec.lid_clearance
    lid_2d = _rounded_rect(
        spec.base_w - 2.0 - 2.0 * c,
        spec.base_d - 2.0 - 2.0 * c,
        max(1.0, spec.corner_r - 1.0 - c),
    )

    # Botao flexivel em U posicionado sobre o centro da bateria CR2032 (x = -6.5)
    bx = -6.5
    u_ring = Point(bx, 0.0).buffer(6.2, resolution=48).difference(
        Point(bx, 0.0).buffer(4.9, resolution=48)
    )
    hinge_keep = box(bx - 8.0, -3.5, bx - 4.2, 3.5)
    slot_u = u_ring.difference(hinge_keep)

    # Pequeno chanfro lateral para abrir com a unha na troca de bateria
    pry_notch = Point(spec.base_w / 2.0 - 1.0 - c, 0.0).buffer(1.4, resolution=24)

    plate_2d = lid_2d.difference(unary_union([slot_u, pry_notch]))
    plate_mesh = extrude_poly(plate_2d, spec.lid_t, z0=0.0)

    # Pino atuador interno que pressiona o terminal do LED contra a bateria
    nub = extrude_poly(Point(bx, 0.0).buffer(2.0, resolution=32), 1.4, z0=spec.lid_t - 0.08)

    # Duas travinhas internas de alinhamento nas bordas curtas
    tabs = unary_union([
        box(-spec.base_w / 2.0 + 2.3, -4.5, -spec.base_w / 2.0 + 3.5, 4.5),
        box(spec.base_w / 2.0 - 3.5, -4.5, spec.base_w / 2.0 - 2.3, 4.5),
    ])
    tabs_mesh = extrude_poly(tabs, 1.8, z0=spec.lid_t - 0.08)

    return trimesh.boolean.union([plate_mesh, nub, tabs_mesh], engine="manifold")
