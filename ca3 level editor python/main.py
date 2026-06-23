# main.py
import os
import sys

# Forzar a Python a buscar módulos locales correctamente desde la raíz del proyecto
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pyray as pr
from src.config import current_cfg, FPS
from src.gui.toolbar import Toolbar
from src.canvas.canvas_manager import CanvasManager
from src.storage.storage import save_level, load_level 
from src.gui.preview_manager import PreviewManager 
from src.gui.config_modal import ConfigModal
from src.localization.localization import tr

def main():
    # Inicializar la ventana de Raylib usando la resolución dinámica actual
    pr.init_window(current_cfg.screen_width, current_cfg.screen_height, "ca3 level editor")
    pr.set_target_fps(FPS)

    # Instanciar componentes del sistema modular
    toolbar = Toolbar()
    canvas = CanvasManager(offset_x=toolbar.width)
    preview = PreviewManager()
    modal = ConfigModal()

    # Variables de estado locales para las nuevas mecánicas
    tile_mirrored = False
    player_start_cell = None  # Almacenará una tupla (grid_x, grid_y)

    while not pr.window_should_close():
        # ---------------------------------------------------------------------
        # 1. ACTUALIZAR ESTADOS
        # ---------------------------------------------------------------------
        modal.update()
        
        # --- NUEVA MECÁNICA: DETECTAR MIRROR HORIZONTAL (ALT) ---
        if not modal.active and toolbar.categories:
            tile_mirrored = pr.is_key_down(pr.KEY_LEFT_ALT) or pr.is_key_down(pr.KEY_RIGHT_ALT)
        else:
            tile_mirrored = False

        canvas.update(toolbar.selected_tile, current_cfg.screen_width, current_cfg.screen_height, modal.active, tile_mirrored)
        
        if not modal.active and toolbar.categories:
            preview.update(canvas.camera, canvas.offset_x, canvas.track_h, canvas.track_v)

            # --- NUEVA MECÁNICA: DETECTAR PLAYER SPAWN (CTRL + CLICK) ---
            ctrl_pressed = pr.is_key_down(pr.KEY_LEFT_CONTROL) or pr.is_key_down(pr.KEY_RIGHT_CONTROL)
            if ctrl_pressed and pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
                mouse_world = pr.get_screen_to_world_2d(pr.get_mouse_position(), canvas.camera)
                grid_x = int(mouse_world.x // current_cfg.tile_size)
                grid_y = int(mouse_world.y // current_cfg.tile_size)
                
                if 0 <= grid_x < current_cfg.map_width and 0 <= grid_y < current_cfg.map_height:
                    player_start_cell = (grid_x, grid_y)

            # --- ATAJOS DE GUARDADO Y CARGA TRADICIONALES ---
            shift_pressed = pr.is_key_down(pr.KEY_LEFT_SHIFT) or pr.is_key_down(pr.KEY_RIGHT_SHIFT)
            if pr.is_key_pressed(pr.KEY_F5):
                if shift_pressed:
                    toolbar._open_save_dialog(canvas.map_data)
                else:
                    save_level(canvas.map_data, "levels/saved_world.json")
            
            if pr.is_key_pressed(pr.KEY_F6):
                if shift_pressed:
                    loaded_map = toolbar._open_load_dialog()
                    if loaded_map is not None:
                        canvas.map_data = loaded_map
                else:
                    loaded_map = load_level("levels/saved_world.json", toolbar)
                    if loaded_map is not None:
                        canvas.map_data = loaded_map

        # ---------------------------------------------------------------------
        # 2. RENDERIZADO / DIBUJO
        # ---------------------------------------------------------------------
        pr.begin_drawing()
        
        if toolbar.categories:
            # 🟢 SOLUCIÓN: Una sola llamada pasándole la textura del fondo de la toolbar
            canvas.draw(current_cfg.screen_width, current_cfg.screen_height, toolbar.bg_texture)
            
            # Dibujado de elementos interactivos dentro del espacio 2D de la cámara
            pr.begin_mode_2d(canvas.camera)
            
            # --- DIBUJAR MARCADOR DEL JUGADOR SI EXISTE ---
            if player_start_cell is not None:
                px = player_start_cell[0] * current_cfg.tile_size
                py = player_start_cell[1] * current_cfg.tile_size
                ts = current_cfg.tile_size
                
                pr.draw_rectangle(px, py, ts, ts, (0, 228, 48, 120))
                pr.draw_rectangle_lines(px, py, ts, ts, pr.GREEN)
                pr.draw_text(tr("player_marker"), px + 2, py - 12, 9, pr.GREEN)
            
            if not modal.active:
                preview.draw_ghost(toolbar.selected_tile, tile_mirrored)
                
            pr.end_mode_2d()
        else:
            # 📚 TUTORIAL INICIAL ACTUALIZADO CON LA CARACTERÍSTICA BACKGROUND.PNG
            pr.clear_background((28, 29, 34, 255))
            start_x = toolbar.width + 50
            pr.draw_text("⚠️ CA3 LEVEL EDITOR - ASSET SETUP REQUIRED", start_x, 80, 22, pr.YELLOW)
            pr.draw_text("The editor could not find valid image folders in your root directory.", start_x, 115, 15, pr.LIGHTGRAY)
            
            # Caja estructural de ejemplo
            pr.draw_rectangle(start_x, 160, 580, 230, (20, 21, 24, 255))
            pr.draw_rectangle_lines(start_x, 160, 580, 230, pr.GRAY)
            
            pr.draw_text("Your project directory must look exactly like this:", start_x + 20, 175, 14, pr.GRAY)
            pr.draw_text("ca3_level_editor/", start_x + 40, 205, 14, pr.WHITE)
            pr.draw_text("├── main binary", start_x + 40, 225, 14, pr.DARKGRAY)
            pr.draw_text("└── assets/                <-- Must be lowercase", start_x + 40, 245, 14, pr.GOLD)
            pr.draw_text("    ├── background.png     <-- Optional reference background image", start_x + 80, 265, 14, pr.GREEN)
            pr.draw_text("    └── blocks/            <-- Category folder name (contains tile PNGs)", start_x + 80, 295, 14, (0, 240, 255, 255))
            
            # Instrucciones breves sobre el comportamiento del fondo
            pr.draw_text("💡 HINT: Put a blueprint or layout image named 'background.png' inside 'assets/'", start_x, 410, 13, pr.GREEN)
            pr.draw_text("to render it as a semi-transparent layer guide under your tiles.", start_x, 430, 13, pr.LIGHTGRAY)
            
        # Dibujar la Toolbar lateral fija
        loaded_from_button = toolbar.draw(current_cfg.screen_height, canvas.map_data)
        if loaded_from_button is not None:
            canvas.map_data = loaded_from_button

        # BARRA SUPERIOR DE INFORMACIÓN FLOTANTE
        pr.draw_rectangle(current_cfg.screen_width - 480, 0, 150, 40, (20, 20, 20, 180))
        pr.draw_text(tr("hint_config"), current_cfg.screen_width - 470, 13, 12, pr.YELLOW)

        pr.draw_rectangle(current_cfg.screen_width - 340, 0, 180, 40, (20, 20, 20, 180))
        pr.draw_text(tr("hint_shortcuts"), current_cfg.screen_width - 330, 14, 11, (0, 240, 255, 255))

        pr.draw_rectangle(current_cfg.screen_width - 150, 0, 134, 40, (20, 20, 20, 180))
        pr.draw_fps(current_cfg.screen_width - 140, 10)

        # BARRA INFERIOR DE NOTIFICACIONES
        bar_h = 30
        bar_y = current_cfg.screen_height - bar_h
        
        pr.draw_rectangle(toolbar.width, bar_y, current_cfg.screen_width - toolbar.width, bar_h, (25, 25, 25, 240))
        pr.draw_line(toolbar.width, bar_y, current_cfg.screen_width, bar_y, (50, 50, 50, 255))
        
        pr.draw_text(tr("hint_mirror"), toolbar.width + 20, bar_y + 9, 11, pr.ORANGE)
        pr.draw_text(tr("hint_player"), toolbar.width + 240, bar_y + 9, 11, pr.LIME)
        
        if tile_mirrored:
            pr.draw_text(tr("hud_mirrored"), current_cfg.screen_width - 130, bar_y + 9, 11, pr.GOLD)

        modal.draw()
        pr.end_drawing()

    toolbar.unload()
    pr.close_window()

if __name__ == "__main__":
    main()
