# src/config.py

# Dimensiones de la ventana
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Tamaño de la rejilla (en píxeles)
TILE_SIZE = 32

# Dimensiones por defecto del nivel (en cantidad de tiles)
MAP_WIDTH = 50
MAP_HEIGHT = 15  # Altura estándar de una pantalla de NES Mario

# Colores estilo Krita / Interfaz Oscura
COLOR_OUTSIDE = (30, 30, 30, 255)      # Gris muy oscuro para el fondo exterior
COLOR_CANVAS_BG = (50, 50, 50, 255)    # Gris medio para el área de trabajo
COLOR_GRID = (70, 70, 70, 100)         # Líneas de la rejilla (con transparencia)

SCROLLBAR_SIZE = 16
COLOR_UI_BG = (40, 40, 40, 255)

class EditorConfig:
    def __init__(self):
        self.tile_size = 32
        self.map_width = 50
        self.map_height = 15
        
        self.language = "en" # Idioma por defecto
        self.languages_list = ["es", "en", "fr", "de", "pt", "it"]
        
        self.screen_width = 1280
        self.screen_height = 720
        self.resolutions = [
            (800, 600),
            (1280, 720),
            (1600, 900),
            (1920, 1080)
        ]
        
        self.res_idx = 1

# Instancia global que compartirán todos los scripts
current_cfg = EditorConfig()
