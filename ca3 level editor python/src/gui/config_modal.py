# src/gui/config_modal.py
import pyray as pr
from raylib import rl as rg
from src.config import current_cfg
from src.localization.localization import tr

class ConfigModal:
    def __init__(self):
        self.active = False
        self.width = 360
        self.height = 290 # Incrementamos el alto para dar espacio a la resolución
        self.rec = [0, 0, self.width, self.height] # Se calculará dinámicamente
        
        # Variables temporales para no alterar el entorno si el usuario cancela con Esc
        self.temp_tile_size = current_cfg.tile_size
        self.temp_map_width = current_cfg.map_width
        self.temp_map_height = current_cfg.map_height
        self.temp_res_idx = current_cfg.res_idx

    def _center_modal(self):
        """Calcula la posición centrada del modal basándose en la resolución de ventana actual."""
        import src.config as cfg
        self.rec[0] = (current_cfg.screen_width - self.width) // 2
        self.rec[1] = (current_cfg.screen_height - self.height) // 2

    def update(self):
        if pr.is_key_pressed(pr.KEY_ENTER):
            if not self.active:
                # Al abrir, volcamos los estados reales a los temporales
                self.temp_tile_size = current_cfg.tile_size
                self.temp_map_width = current_cfg.map_width
                self.temp_map_height = current_cfg.map_height
                self.temp_res_idx = current_cfg.res_idx
                self._center_modal()
                self.active = True
            else:
                self.apply_changes()

        if self.active and pr.is_key_pressed(pr.KEY_ESCAPE):
            self.active = False

    def apply_changes(self):
        # 1. Aplicar cambios de mapa tradicionales
        current_cfg.tile_size = self.temp_tile_size
        current_cfg.map_width = self.temp_map_width
        current_cfg.map_height = self.temp_map_height
        
        # 2. Aplicar nueva resolución de pantalla si cambió
        if current_cfg.res_idx != self.temp_res_idx:
            current_cfg.res_idx = self.temp_res_idx
            new_w, new_h = current_cfg.resolutions[current_cfg.res_idx]
            
            current_cfg.screen_width = new_w
            current_cfg.screen_height = new_h
            
            # Ordenar a Raylib cambiar el tamaño físico de la ventana de Linux
            pr.set_window_size(new_w, new_h)
            
        self.active = False

    def draw(self):
        if not self.active:
            return

        # Dibujar capa oscura de fondo adaptada al tamaño actual de la pantalla
        pr.draw_rectangle(0, 0, current_cfg.screen_width, current_cfg.screen_height, (15, 15, 15, 180))
        
        # Asegurar centrado correcto antes de pintar por si la ventana mutó
        self._center_modal()
        rg.GuiPanel(self.rec, tr("modal_title").encode('utf-8'))

        bx = self.rec[0] + 30
        by = self.rec[1] + 50

        # Fila 1: Tamaño de Rejilla
        pr.draw_text(f"{tr('modal_grid')} {self.temp_tile_size} px", bx, by, 14, pr.LIGHTGRAY)
        if rg.GuiButton([bx + 230, by - 4, 30, 20], "+".encode('utf-8')):
            self.temp_tile_size = min(64, self.temp_tile_size + 8)
        if rg.GuiButton([bx + 265, by - 4, 30, 20], "-".encode('utf-8')):
            self.temp_tile_size = max(16, self.temp_tile_size - 8)

        # Fila 2: Ancho del Mapa
        pr.draw_text(f"{tr('modal_width')} {self.temp_map_width}", bx, by + 40, 14, pr.LIGHTGRAY)
        if rg.GuiButton([bx + 230, by + 36, 30, 20], "+".encode('utf-8')):
            self.temp_map_width += 10
        if rg.GuiButton([bx + 265, by + 36, 30, 20], "-".encode('utf-8')):
            self.temp_map_width = max(10, self.temp_map_width - 10)

        # Fila 3: Alto del Mapa
        pr.draw_text(f"{tr('modal_height')} {self.temp_map_height}", bx, by + 80, 14, pr.LIGHTGRAY)
        if rg.GuiButton([bx + 230, by + 76, 30, 20], "+".encode('utf-8')):
            self.temp_map_height += 1
        if rg.GuiButton([bx + 265, by + 76, 30, 20], "-".encode('utf-8')):
            self.temp_map_height = max(5, self.temp_map_height - 1)

        # NUEVA Fila 4: Resolución de Ventana
        res_w, res_h = current_cfg.resolutions[self.temp_res_idx]
        pr.draw_text(f"{tr('modal_res')} {res_w}x{res_h}", bx, by + 120, 14, pr.LIGHTGRAY)
        if rg.GuiButton([bx + 230, by + 116, 30, 20], "+".encode('utf-8')):
            self.temp_res_idx = min(len(current_cfg.resolutions) - 1, self.temp_res_idx + 1)
        if rg.GuiButton([bx + 265, by + 116, 30, 20], "-".encode('utf-8')):
            self.temp_res_idx = max(0, self.temp_res_idx - 1)

        # Botones de Acción inferiores
        btn_y = self.rec[1] + self.rec[3] - 45
        if rg.GuiButton([bx, btn_y, 130, 30], tr("modal_accept").encode('utf-8')):
            self.apply_changes()
        if rg.GuiButton([bx + 150, btn_y, 120, 30], tr("modal_cancel").encode('utf-8')):
            self.active = False
