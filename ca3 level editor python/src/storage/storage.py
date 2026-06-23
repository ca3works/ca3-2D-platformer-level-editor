# src/storage.py
import json
import os
import pyray as pr
from src.config import current_cfg

def save_level(map_data, filepath="levels/level_1.json"):
    # Asegurar que exista el directorio destino (útil si el File Picker genera una ruta nueva)
    dir_name = os.path.dirname(filepath)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
        
    serializable_map = []
    current_w = current_cfg.map_width
    current_height = current_cfg.map_height
    
    for x in range(current_w):
        for y in range(current_height):
            # Prevenir desbordes si la matriz de origen es mayor que la configuración actual
            if x >= len(map_data) or y >= len(map_data[x]):
                continue
                
            tile = map_data[x][y]
            if tile is not None:
                serializable_map.append({
                    "x": x,
                    "y": y,
                    "name": tile["name"],
                    "path": tile["path"],
                    "mirrored": tile.get("mirrored", False)  # 💾 Guardamos el estado del flip
                })
                
    level_packet = {
        "metadata": {
            "width": current_w,
            "height": current_height,
            "tile_size": current_cfg.tile_size
        },
        "tiles": serializable_map
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(level_packet, f, indent=4)
    print(f"¡Nivel guardado con éxito en {filepath} ({current_w}x{current_height})!")

def load_level(filepath, toolbar_instance):
    if not os.path.exists(filepath):
        print(f"El archivo de guardado {filepath} no existe todavía.")
        return None
        
    with open(filepath, "r", encoding="utf-8") as f:
        level_packet = json.load(f)
        
    metadata = level_packet.get("metadata", {})
    file_w = metadata.get("width", current_cfg.map_width)
    file_h = metadata.get("height", current_cfg.map_height)
    file_ts = metadata.get("tile_size", current_cfg.tile_size)
    
    # Adaptamos la configuración del editor a las propiedades nativas del nivel cargado
    current_cfg.map_width = file_w
    current_cfg.map_height = file_h
    current_cfg.tile_size = file_ts
        
    # 🟢 OPTIMIZACIÓN: Inicializar la matriz con las dimensiones exactas del archivo JSON
    new_map_data = [[None for _ in range(file_h)] for _ in range(file_w)]
    
    # Indexamos las texturas cargadas en la Toolbar para un acceso rápido O(1)
    texture_cache = {}
    for cat in toolbar_instance.tiles_by_cat:
        for t in toolbar_instance.tiles_by_cat[cat]:
            texture_cache[t["path"]] = t

    for tile_info in level_packet["tiles"]:
        tx = tile_info["x"]
        ty = tile_info["y"]
        path = tile_info["path"]
        
        # Validar límites de la matriz dinámica
        if 0 <= tx < file_w and 0 <= ty < file_h:
            is_mirrored = tile_info.get("mirrored", False)  # 🔄 Recuperamos el estado del flip
            
            if path in texture_cache:
                # 💡 Copiamos los metadatos base para evitar mutar el tile de la Toolbar
                local_tile = texture_cache[path].copy()
                local_tile["mirrored"] = is_mirrored
                new_map_data[tx][ty] = local_tile
            else:
                # Fallback por si el asset no está cargado en la toolbar pero existe en disco
                if os.path.exists(path):
                    tex = pr.load_texture(path)
                    new_map_data[tx][ty] = {
                        "name": tile_info["name"], 
                        "tex": tex, 
                        "path": path,
                        "mirrored": is_mirrored
                    }
                    
    print(f"¡Nivel {filepath} cargado correctamente y adaptado a {file_w}x{file_h}!")
    return new_map_data
