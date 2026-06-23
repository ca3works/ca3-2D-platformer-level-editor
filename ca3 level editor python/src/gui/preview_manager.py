# src/gui/preview_manager.py
import pyray as pr
from src.config import current_cfg

class PreviewManager:
    def __init__(self):
        self.ghost_color = (255, 255, 255, 128)
        self.grid_x = 0
        self.grid_y = 0
        self.should_draw = False

    def update(self, camera, offset_x, track_h, track_v):
        mouse_pos = pr.get_mouse_position()
        self.should_draw = False

        on_scroll_h = (track_h[0] <= mouse_pos.x <= track_h[0] + track_h[2] and 
                       track_h[1] <= mouse_pos.y <= track_h[1] + track_h[3])
        on_scroll_v = (track_v[0] <= mouse_pos.x <= track_v[0] + track_v[2] and \
                       track_v[1] <= mouse_pos.y <= track_v[1] + track_v[3])

        if mouse_pos.x > offset_x and not on_scroll_h and not on_scroll_v:
            world_pos = pr.get_screen_to_world_2d(mouse_pos, camera)
            self.grid_x = int(world_pos.x // current_cfg.tile_size)
            self.grid_y = int(world_pos.y // current_cfg.tile_size)

            if 0 <= self.grid_x < current_cfg.map_width and 0 <= self.grid_y < current_cfg.map_height:
                self.should_draw = True

    def draw_ghost(self, selected_tile, tile_mirrored=False):
        """Dibuja el bloque translúcido debajo del ratón antes de colocarlo."""
        if not self.should_draw or not selected_tile:
            return

        grid_size = current_cfg.tile_size
        px = self.grid_x * grid_size
        py = self.grid_y * grid_size

        source_width = selected_tile["tex"].width
        
        # 💡 SOLUCIÓN: Calculamos el desplazamiento de renderizado en una variable local
        # sin alterar las variables lógicas de posición del cuadro blanco de la rejilla.
        render_x = px
        if tile_mirrored:
            source_width = -source_width

        source_rec = pr.Rectangle(0, 0, source_width, selected_tile["tex"].height)
        dest_rec = pr.Rectangle(render_x, py, grid_size, grid_size)
        origin = pr.Vector2(0, 0)

        # Dibujar textura reflejada correctamente alineada
        pr.draw_texture_pro(
            selected_tile["tex"],
            source_rec,
            dest_rec,
            origin,
            0.0,
            self.ghost_color
        )
        
        # El recuadro sutil se queda EXACTAMENTE sobre la celda que recibirá el clic
        pr.draw_rectangle_lines(px, py, grid_size, grid_size, (255, 255, 255, 100))
