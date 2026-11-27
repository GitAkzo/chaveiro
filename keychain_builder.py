"""Construcao parametrica 3D (watertight) do chaveiro com cavidade para LED."""

from dataclasses import dataclass
import numpy as np
import trimesh
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union


@dataclass(frozen=True)
class KeychainSpec:
    """Dimensoes em milimetros otimizadas para FDM (bico 0.4mm, camada 0.2mm)."""
    body_radius: float = 24.0          # Medalhao circular/organico 48mm diametro
    wall_thickness: float = 2.4        # Parede lateral resistente
    back_thickness: float = 1.6        # Parede traseira (com botao flexivel)
    cavity_depth: float = 6.2          # Espaco interno para CR2032 (3.2mm) + LED
    lip_height: float = 1.6            # Altura do degrau de encaixe da tampa frontal
    lip_clearance: float = 0.25        # Folga radial para encaixe snap-fit/friccao
    diffuser_thickness: float = 0.8    # Base fina difusora (deixa a luz passar)
    logo_relief: float = 1.4           # Alto-relevo da logo na frente
    ring_hole_d: float = 4.6           # Furo para argola de chaveiro
    ring_outer_d: float = 11.4         # Alca reforcada ao redor do furo
    battery_d: float = 20.8            # CR2032 (20.0mm) + folga 0.8mm
    battery_wall: float = 1.2          # Parede do berco retentor da bateria


def extrude_poly(poly, height: float, z0: float = 0.0) -> trimesh.Trimesh:
    """Extruda Polygon ou MultiPolygon Shapely e posiciona em z0."""
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


def _base_silhouette(spec: KeychainSpec) -> tuple[Polygon, tuple[float, float]]:
    """Cria o contorno circular principal + alca superior para argola."""
    main_disc = Point(0, 0).buffer(spec.body_radius, resolution=96)
    loop_y = spec.body_radius + 3.2
    loop_center = (0.0, loop_y)
    outer_loop = Point(loop_center).buffer(spec.ring_outer_d / 2.0, resolution=64)
    # Pescoço suave conectando a alça ao corpo
    neck = box(-5.2, spec.body_radius - 3.0, 5.2, loop_y)
    silhouette = unary_union([main_disc, outer_loop, neck]).buffer(1.2).buffer(-1.2)
    return silhouette, loop_center


def build_front_diffuser(logo_poly, spec: KeychainSpec) -> trimesh.Trimesh:
    """Peca 01: Tampa frontal difusora + logo em alto-relevo + aba de encaixe.

    Imprimir deitada de costas (z=0 na mesa), ZERO suportes.
    """
    inner_r = spec.body_radius - spec.wall_thickness
    # Disco frontal difusor que cobre o topo do corpo (encaixe rebaixado)
    front_disc = Point(0, 0).buffer(spec.body_radius - 0.15, resolution=96)
    # Aba interna que encaixa dentro da cavidade do corpo
    snap_r_out = inner_r - spec.lip_clearance
    snap_r_in = snap_r_out - 1.4
    snap_ring = (
        Point(0, 0).buffer(snap_r_out, resolution=96)
        .difference(Point(0, 0).buffer(snap_r_in, resolution=96))
    )

    # Orientacao de impressao: aba de encaixe fica voltada para baixo? Nao!
    # Para ZERO suportes, a face traseira do difusor fica em z=0?
    # Se a aba estiver em cima, a logo ficaria embaixo.
    # Solucao ZERO suportes: a tampa encaixa DENTRO do rebaixo frontal do corpo!
    # Entao a tampa e um disco plano de espessura diffuser_thickness (0.8mm)
    # com raio = (body_radius - wall_thickness/2 - clearance), e a LOGO em relevo
    # cresce para cima (+Z)! Sem aba saliente para baixo = 100% plana na mesa!
    seat_r = spec.body_radius - 1.2 - spec.lip_clearance
    plate_2d = Point(0, 0).buffer(seat_r, resolution=96)

    # Pequena borda perimetral (aro fino de 0.8mm) para acabamento premium
    rim_2d = plate_2d.difference(Point(0, 0).buffer(seat_r - 1.0, resolution=96))

    plate_mesh = extrude_poly(plate_2d, spec.diffuser_thickness, z0=0.0)
    ov = 0.08
    rim_mesh = extrude_poly(
        rim_2d, spec.logo_relief * 0.7 + ov, z0=spec.diffuser_thickness - ov
    )
    logo_mesh = extrude_poly(
        logo_poly, spec.logo_relief + ov, z0=spec.diffuser_thickness - ov
    )

    front = trimesh.boolean.union([plate_mesh, rim_mesh, logo_mesh], engine="manifold")
    return front


def build_hollow_base(spec: KeychainSpec) -> trimesh.Trimesh:
    """Peca 02: Base oca com alca, berco CR2032, canal LED e botao flexivel.

    Imprimir com a traseira (z=0) apoiada na mesa, ZERO suportes.
    """
    silhouette, loop_center = _base_silhouette(spec)
    ring_hole = Point(loop_center).buffer(spec.ring_hole_d / 2.0, resolution=64)
    body_2d = silhouette.difference(ring_hole)

    total_h = spec.back_thickness + spec.cavity_depth + spec.diffuser_thickness
    outer_body = extrude_poly(body_2d, total_h, z0=0.0)

    # 1. Cavidade principal oca (para bateria + LED + difusao de luz)
    inner_r = spec.body_radius - spec.wall_thickness
    cavity_2d = Point(0, 0).buffer(inner_r, resolution=96)
    cavity_mesh = extrude_poly(
        cavity_2d, spec.cavity_depth + spec.diffuser_thickness + 1.0, z0=spec.back_thickness
    )

    # 2. Rebaixo frontal (degrau onde a peca 01 encaixa perfeitamente nivelada)
    seat_r = spec.body_radius - 1.2
    seat_2d = Point(0, 0).buffer(seat_r, resolution=96)
    seat_z = spec.back_thickness + spec.cavity_depth
    seat_mesh = extrude_poly(seat_2d, spec.diffuser_thickness + 1.0, z0=seat_z)

    # 3. Fenda em "U" na parede traseira criando botao flexivel (compliant button)
    # Quando pressionado, empurra o terminal do LED contra a bateria CR2032
    btn_r_out = 7.2
    btn_r_in = 5.8
    u_ring = Point(0, -1.5).buffer(btn_r_out, resolution=64).difference(
        Point(0, -1.5).buffer(btn_r_in, resolution=64)
    )
    # Deixa a dobradica conectada na parte inferior (y < -6.5)
    hinge_keep = box(-4.5, -12.0, 4.5, -5.8)
    slot_2d = u_ring.difference(hinge_keep)
    slot_mesh = extrude_poly(slot_2d, spec.back_thickness + 0.6, z0=-0.3)

    shell = trimesh.boolean.difference(
        [outer_body, cavity_mesh, seat_mesh, slot_mesh], engine="manifold"
    )

    # 4. Berco interno para bateria CR2032 (anel aberto para encaixar os terminais)
    bat_cy = -2.0
    bat_r_in = spec.battery_d / 2.0
    bat_r_out = bat_r_in + spec.battery_wall
    cradle_ring = Point(0, bat_cy).buffer(bat_r_out, resolution=64).difference(
        Point(0, bat_cy).buffer(bat_r_in, resolution=64)
    )
    # Aberturas no berco: topo para entrada do LED (5mm/3mm) e laterais para remocao facil
    led_notch = box(-3.6, bat_cy + 5.0, 3.6, bat_cy + bat_r_out + 2.0)
    side_notches = unary_union([
        box(-bat_r_out - 2.0, bat_cy - 3.5, -bat_r_in + 1.0, bat_cy + 3.5),
        box(bat_r_in - 1.0, bat_cy - 3.5, bat_r_out + 2.0, bat_cy + 3.5),
    ])
    cradle_2d = cradle_ring.difference(unary_union([led_notch, side_notches]))
    # Limita dentro da cavidade
    cradle_2d = cradle_2d.intersection(Point(0, 0).buffer(inner_r + 0.4, resolution=96))
    cradle_mesh = extrude_poly(cradle_2d, 3.0, z0=spec.back_thickness - 0.1)

    # 5. Pequeno pino atuador interno no centro do botao flexivel
    nub_2d = Point(0, -1.5).buffer(2.2, resolution=32)
    nub_mesh = extrude_poly(nub_2d, 1.0, z0=spec.back_thickness - 0.1)

    # 6. Clipes guia para o bulbo do LED (3mm ou 5mm) no topo da cavidade
    led_y = 13.5
    led_clip_l = box(-4.4, led_y - 2.2, -2.7, led_y + 2.2)
    led_clip_r = box(2.7, led_y - 2.2, 4.4, led_y + 2.2)
    clips_2d = unary_union([led_clip_l, led_clip_r]).intersection(
        Point(0, 0).buffer(inner_r + 0.4, resolution=96)
    )
    clips_mesh = extrude_poly(clips_2d, 3.6, z0=spec.back_thickness - 0.1)

    base = trimesh.boolean.union(
        [shell, cradle_mesh, nub_mesh, clips_mesh], engine="manifold"
    )
    return base


def build_solid_keychain(logo_poly, spec: KeychainSpec) -> trimesh.Trimesh:
    """Peca 03 (Bonus): Chaveiro macico fino (3.6mm) pronto para troca de cor."""
    silhouette, loop_center = _base_silhouette(spec)
    ring_hole = Point(loop_center).buffer(spec.ring_hole_d / 2.0, resolution=64)
    base_2d = silhouette.difference(ring_hole)

    base_h = 2.2
    rim_2d = Point(0, 0).buffer(spec.body_radius, resolution=96).difference(
        Point(0, 0).buffer(spec.body_radius - 1.4, resolution=96)
    )

    ov = 0.08
    base_mesh = extrude_poly(base_2d, base_h, z0=0.0)
    rim_mesh = extrude_poly(rim_2d, 1.0 + ov, z0=base_h - ov)
    logo_mesh = extrude_poly(logo_poly, 1.4 + ov, z0=base_h - ov)

    return trimesh.boolean.union([base_mesh, rim_mesh, logo_mesh], engine="manifold")
