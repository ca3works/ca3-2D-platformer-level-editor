# src/canvas_manager.py
import pyray as pr
from src.config import current_cfg, COLOR_OUTSIDE, COLOR_CANVAS_BG, COLOR_GRID, SCROLLBAR_SIZE, COLOR_UI_BG

class CanvasManager:
    def __init__(self, offset_x):
        self.offset_x = offset_x
        
        # Inicializamos una matriz sobredimensionada (512x256) para evitar desbordes.
        # Guardaremos diccionarios con metadatos del bloque en vez del objeto tile base.
        self.map_data = [[None for _ in range(256)] for _ in range(512)]
        
        # Configuración inicial de la cámara 2D de Raylib
        self.camera = pr.Camera2D()
        self.camera.target = pr.Vector2(0, 0)
        self.camera.offset = pr.Vector2(self.offset_x + 40, 100)
        self.camera.rotation = 0.0
        self.camera.zoom = 1.0

        # Estados para controlar el arrastre manual de las barras de scroll
        self.dragging_h = False
        self.dragging_v = False

        # Variables de posición en píxeles para los manejadores (thumbs)
        self.thumb_h_x = 0.0
        self.thumb_v_y = 0.0
        self.thumb_h_w = 0
        self.thumb_v_h = 0
        
        # Rectángulos contenedores de los carriles (tracks) de scroll
        self.track_h = [0, 0, 0, 0]
        self.track_v = [0, 0, 0, 0]

    def update(self, selected_tile, screen_width, screen_height, is_modal_active, tile_mirrored=False):
        # REGLA DE ORO: Si el modal está abierto, congelamos el canvas por completo.
        if is_modal_active:
            self.dragging_h = False
            self.dragging_v = False
            return
        
        # ---------------------------------------------------------------------
        # 🟢 FEATURE: ARRASTRE DE CÁMARA ESTILO KRITA (ESPACIO O BOTÓN CENTRAL)
        # ---------------------------------------------------------------------
        is_space_down = pr.is_key_down(pr.KEY_SPACE)
        is_middle_mouse_down = pr.is_mouse_button_down(pr.MOUSE_BUTTON_MIDDLE)

        if is_space_down or is_middle_mouse_down:
            mouse_delta = pr.get_mouse_delta()
            # Mover el target de la cámara inversamente al delta del mouse
            self.camera.target.x -= mouse_delta.x / self.camera.zoom
            self.camera.target.y -= mouse_delta.y / self.camera.zoom
            
            # Cambiar cursor visual a modo arrastre/movimiento
            pr.set_mouse_cursor(pr.MOUSE_CURSOR_RESIZE_ALL)
            
            # 💡 IMPORTANTE: No ejecutamos la lógica de pintar/borrar bloques 
            # mientras arrastramos la cámara para evitar clics accidentales.
            return 
        else:
            # Restauramos el cursor por defecto cuando dejas de arrastrar
            pr.set_mouse_cursor(pr.MOUSE_CURSOR_DEFAULT)

        # Calcular dimensiones actuales del lienzo en píxeles
        canvas_pixel_width = current_cfg.map_width * current_cfg.tile_size
        canvas_pixel_height = current_cfg.map_height * current_cfg.tile_size

        # Calcular límites máximos de movimiento seguro para la cámara
        max_scroll_x = canvas_pixel_width - (screen_width - self.offset_x) + 100
        max_scroll_y = canvas_pixel_height - screen_height + 200
        if max_scroll_x < 0: max_scroll_x = 0
        if max_scroll_y < 0: max_scroll_y = 0

        # Definir las regiones fijas en pantalla de los carriles del scroll
        self.track_h = [self.offset_x, screen_height - SCROLLBAR_SIZE, screen_width - self.offset_x - SCROLLBAR_SIZE, SCROLLBAR_SIZE]
        self.track_v = [screen_width - SCROLLBAR_SIZE, 0, SCROLLBAR_SIZE, screen_height - SCROLLBAR_SIZE]

        # Calcular tamaño proporcional de los Thumbs
        self.thumb_h_w = max(40, int((self.track_h[2] / canvas_pixel_width) * self.track_h[2])) if max_scroll_x > 0 else self.track_h[2]
        self.thumb_v_h = max(40, int((self.track_v[3] / canvas_pixel_height) * self.track_v[3])) if max_scroll_y > 0 else self.track_v[3]

        # Mapear posición de la cámara a ratios de 0.0 a 1.0
        ratio_x = self.camera.target.x / max_scroll_x if max_scroll_x > 0 else 0
        ratio_y = (self.camera.target.y + 50) / (max_scroll_y + 50) if max_scroll_y > 0 else 0

        # Posicionar los manejadores en la pantalla
        self.thumb_h_x = self.track_h[0] + ratio_x * (self.track_h[2] - self.thumb_h_w)
        self.thumb_v_y = self.track_v[1] + ratio_y * (self.track_v[3] - self.thumb_v_h)

        # ---------------- LÓGICA DE INTERACCIÓN (ARRASRTRE CON MOUSE) ----------------
        mouse_pos = pr.get_mouse_position()
        
        if pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
            if (self.thumb_h_x <= mouse_pos.x <= self.thumb_h_x + self.thumb_h_w and 
                self.track_h[1] <= mouse_pos.y <= self.track_h[1] + SCROLLBAR_SIZE):
                self.dragging_h = True
            elif (self.track_v[0] <= mouse_pos.x <= self.track_v[0] + SCROLLBAR_SIZE and 
                  self.thumb_v_y <= mouse_pos.y <= self.thumb_v_y + self.thumb_v_h):
                self.dragging_v = True

        if pr.is_mouse_button_released(pr.MOUSE_BUTTON_LEFT):
            self.dragging_h = False
            self.dragging_v = False

        if self.dragging_h and max_scroll_x > 0:
            relative_x = mouse_pos.x - self.track_h[0] - (self.thumb_h_w / 2)
            new_ratio = max(0.0, min(1.0, relative_x / (self.track_h[2] - self.thumb_h_w)))
            self.camera.target.x = new_ratio * max_scroll_x
            
        if self.dragging_v and max_scroll_y > 0:
            relative_y = mouse_pos.y - self.track_v[1] - (self.thumb_v_h / 2)
            new_ratio = max(0.0, min(1.0, relative_y / (self.track_v[3] - self.thumb_v_h)))
            self.camera.target.y = (new_ratio * (max_scroll_y + 50)) - 50

        # -------------- CONTROLES POR TECLADO, RUEDA Y PINTADO --------------
        if not self.dragging_h and not self.dragging_v:
            if pr.is_key_down(pr.KEY_RIGHT):   self.camera.target.x += 8
            if pr.is_key_down(pr.KEY_LEFT):    self.camera.target.x -= 8
            if pr.is_key_down(pr.KEY_DOWN):    self.camera.target.y += 8
            if pr.is_key_down(pr.KEY_UP):      self.camera.target.y -= 8

            on_scroll_h = (self.track_h[0] <= mouse_pos.x <= self.track_h[0] + self.track_h[2] and 
                           self.track_h[1] <= mouse_pos.y <= self.track_h[1] + self.track_h[3])
            on_scroll_v = (self.track_v[0] <= mouse_pos.x <= self.track_v[0] + self.track_v[2] and 
                           self.track_v[1] <= mouse_pos.y <= self.track_v[1] + self.track_v[3])

            if mouse_pos.x > self.offset_x and not on_scroll_h and not on_scroll_v:
                world_pos = pr.get_screen_to_world_2d(mouse_pos, self.camera)
                tile_x = int(world_pos.x // current_cfg.tile_size)
                tile_y = int(world_pos.y // current_cfg.tile_size)
                
                # Ignorar si se intenta colocar bloque normal usando Ctrl (reservado para Spawn)
                ctrl_pressed = pr.is_key_down(pr.KEY_LEFT_CONTROL) or pr.is_key_down(pr.KEY_RIGHT_CONTROL)

                if 0 <= tile_x < current_cfg.map_width and 0 <= tile_y < current_cfg.map_height:
                    if pr.is_mouse_button_down(pr.MOUSE_BUTTON_LEFT) and selected_tile and not ctrl_pressed:
                        # Guardamos los metadatos estructurados con el estado de la inversión
                        self.map_data[tile_x][tile_y] = {
                            "name": selected_tile["name"],
                            "tex": selected_tile["tex"],
                            "path": selected_tile["path"],
                            "mirrored": tile_mirrored # Captura el flag Alt de este frame
                        }
                    elif pr.is_mouse_button_down(pr.MOUSE_BUTTON_RIGHT):
                        self.map_data[tile_x][tile_y] = None

                wheel = pr.get_mouse_wheel_move()
                if wheel != 0:
                    self.camera.target.y -= wheel * 32

        # Abrazar límites de la cámara
        if self.camera.target.x < 0: self.camera.target.x = 0
        if self.camera.target.y < -50: self.camera.target.y = -50
        if self.camera.target.x > max_scroll_x: self.camera.target.x = max_scroll_x
        if self.camera.target.y > max_scroll_y: self.camera.target.y = max_scroll_y

    def draw(self, screen_width, screen_height, bg_texture=None):
        pr.clear_background(COLOR_OUTSIDE)
        
        # --- MODO CÁMARA 2D ---
        pr.begin_mode_2d(self.camera)
        
        grid_size = current_cfg.tile_size
        canvas_pixel_width = current_cfg.map_width * grid_size
        canvas_pixel_height = current_cfg.map_height * grid_size

        pr.draw_rectangle(0, 0, canvas_pixel_width, canvas_pixel_height, COLOR_CANVAS_BG)
        
        if bg_texture is not None:
            # Dibujamos usando la opacidad en el tinte (100 de 255 es aprox ~40% opaco)
            pr.draw_texture(bg_texture, 0, 0, (255, 255, 255, 100))
        
        # Grid dinámico
        for x in range(current_cfg.map_width + 1):
            pr.draw_line(x * grid_size, 0, x * grid_size, canvas_pixel_height, COLOR_GRID)
        for y in range(current_cfg.map_height + 1):
            pr.draw_line(0, y * grid_size, canvas_pixel_width, y * grid_size, COLOR_GRID)
            
        # Dibujar bloques estables
        for x in range(current_cfg.map_width):
            for y in range(current_cfg.map_height):
                tile = self.map_data[x][y]
                if tile is not None:
                    source_width = tile["tex"].width
                    is_mirrored = tile.get("mirrored", False)
                    
                    # Posicionamiento base en coordenadas del mundo útil
                    dest_x = x * grid_size
                    dest_y = y * grid_size
                    
                    if is_mirrored:
                        source_width = -source_width

                    source_rec = pr.Rectangle(0, 0, source_width, tile["tex"].height)
                    dest_rec = pr.Rectangle(dest_x, dest_y, grid_size, grid_size)
                    
                    pr.draw_texture_pro(
                        tile["tex"],
                        source_rec,
                        dest_rec,
                        pr.Vector2(0, 0),
                        0.0,
                        pr.WHITE
                    )
        pr.end_mode_2d()
        # --- FIN MODO CÁMARA ---

        # --- ENTORNO GRÁFICO FIJO (SCROLLBARS) ---
        carril_color = (45, 45, 45, 255)
        manejador_color = (85, 85, 85, 255) if not (self.dragging_h or self.dragging_v) else (110, 110, 110, 255)
        
        pr.draw_rectangle_rec(self.track_h, carril_color)
        pr.draw_rectangle(int(self.thumb_h_x), int(self.track_h[1] + 2), int(self.thumb_h_w), SCROLLBAR_SIZE - 4, manejador_color)

        pr.draw_rectangle_rec(self.track_v, carril_color)
        pr.draw_rectangle(int(self.track_v[0] + 2), int(self.thumb_v_y), SCROLLBAR_SIZE - 4, int(self.thumb_v_h), manejador_color)

        pr.draw_rectangle(screen_width - SCROLLBAR_SIZE, screen_height - SCROLLBAR_SIZE, SCROLLBAR_SIZE, SCROLLBAR_SIZE, COLOR_UI_BG)
