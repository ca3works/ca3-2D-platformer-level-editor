# src/gui/toolbar.py
import os
import sys
import subprocess
import pyray as pr
from raylib import rl as rg
from src.storage.storage import save_level, load_level
from src.localization.localization import tr # <-- Importamos el traductor
from src.config import current_cfg # <-- Importamos la config para cambiar idioma

class Toolbar:
	def __init__(self):
		self.width = 240
		self.categories = []
		self.tiles_by_cat = {}
		self.active_category_idx = 0
		self.selected_tile = None
		self.bg_texture = None
		
		self.load_assets()
	
	def get_root_dir(self):
		"""Obtiene la raíz del proyecto, sea .py o .exe"""
		if getattr(sys, 'frozen', False):
			# Si es un exe, el directorio base es donde está el .exe
			return os.path.dirname(sys.executable)
		else:
			# Si es script, es la raíz del proyecto
			return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	
	def load_assets(self):
		# 🟢 CORRECCIÓN: Subimos los niveles correctos para encontrar la raíz del proyecto
		# os.path.abspath(__file__) -> .../ca3 level editor/src/gui/toolbar.py
		current_dir = os.path.dirname(os.path.abspath(__file__)) # .../ca3 level editor/src/gui
		src_dir = os.path.dirname(current_dir)                   # .../ca3 level editor/src
		project_root = os.path.dirname(src_dir)                  # .../ca3 level editor
		
		assets_base = os.path.join(self.get_root_dir(), "assets")
		
		if not os.path.exists(assets_base):
			print(f"⚠️ ERROR: No existe la carpeta en la ruta absoluta: {assets_base}")
			return
		
		# Cargar el fondo usando el path absoluto corregido
		bg_path = os.path.join(assets_base, "background.png")
		if os.path.exists(bg_path):
			self.bg_texture = pr.load_texture(bg_path)
			print(f"🖼️ Fondo de referencia cargado correctamente ({self.bg_texture.width}x{self.bg_texture.height})")
		else:
			print(f"❌ BACKGROUND NOT FOUND. Buscado en: {bg_path}")
		
		# El bucle de categorías utilizando la ruta absoluta correcta
		for entry in sorted(os.listdir(assets_base)):
			full_path = os.path.join(assets_base, entry)
			if os.path.isdir(full_path):
				self.categories.append(entry)
				self.tiles_by_cat[entry] = []
				
				for file in sorted(os.listdir(full_path)):
					if file.lower().endswith(('.png', '.jpg', '.jpeg')):
						tile_path = os.path.join(full_path, file)
						tex = pr.load_texture(tile_path)
						tile_name = os.path.splitext(file)[0]
						
						self.tiles_by_cat[entry].append({
							"name": tile_name,
							"tex": tex,
							"path": tile_path
						})
						
		if self.categories:
			first_cat = self.categories[0]
			if self.tiles_by_cat[first_cat]:
				self.selected_tile = self.tiles_by_cat[first_cat][0]

	def _open_save_dialog(self, map_data):
		try:
			cmd = [
				"zenity", "--file-selection", "--save", 
				f"--title={tr('modal_title')}", 
				"--confirm-overwrite", 
				"--file-filter=Archivos JSON (*.json) | *.json"
			]
			result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
			if result.returncode == 0:
				filepath = result.stdout.strip()
				if not filepath.endswith(".json"):
					filepath += ".json"
				save_level(map_data, filepath)
		except Exception as e:
			print(f"Error en File Picker de guardado: {e}")

	def _open_load_dialog(self):
		try:
			cmd = [
				"zenity", "--file-selection", 
				f"--title={tr('open_btn')}", 
				"--file-filter=Archivos JSON (*.json) | *.json"
			]
			result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
			if result.returncode == 0:
				filepath = result.stdout.strip()
				return load_level(filepath, self)
		except Exception as e:
			print(f"Error en File Picker de carga: {e}")
		return None

	def draw(self, screen_height, map_data=None):
		# 1. Fondo de la barra con título traducido
		rg.GuiPanel([0, 0, self.width, screen_height], tr("title").encode('utf-8'))
		
		# --- BOTÓN SELECTOR DE IDIOMA (Arriba a la derecha del panel) ---
		lang_btn_text = f"🌐 {current_cfg.language.upper()}".encode('utf-8')
		if rg.GuiButton([self.width - 65, 4, 55, 18], lang_btn_text):
			curr_idx = current_cfg.languages_list.index(current_cfg.language)
			next_idx = (curr_idx + 1) % len(current_cfg.languages_list)
			current_cfg.language = current_cfg.languages_list[next_idx]
		
		# --- BOTONES DE INTERFAZ NATIVOS ---
		if rg.GuiButton([15, 42, 90, 24], tr("save_btn").encode('utf-8')) and map_data:
			self._open_save_dialog(map_data)
			
		if rg.GuiButton([115, 42, 90, 24], tr("open_btn").encode('utf-8')):
			loaded_map = self._open_load_dialog()
			if loaded_map is not None:
				return loaded_map

		# --- SECTOR DE CATEGORÍAS ---
		if not self.categories:
			# Dibujamos un aviso sutil en la barra lateral
			pr.draw_text("No assets found.", 15, 85, 14, pr.RED)
			pr.draw_text("Check center screen", 15, 105, 12, pr.GRAY)
			pr.draw_text("for setup guide.", 15, 121, 12, pr.GRAY)
			return None

		current_cat_name = self.categories[self.active_category_idx]
		pr.draw_text(tr("category"), 15, 80, 12, pr.GRAY)
		
		button_text = f"{current_cat_name} >".encode('utf-8')
		if rg.GuiButton([15, 95, self.width - 30, 25], button_text):
			self.active_category_idx = (self.active_category_idx + 1) % len(self.categories)
			current_cat_name = self.categories[self.active_category_idx]
			if self.tiles_by_cat[current_cat_name]:
				self.selected_tile = self.tiles_by_cat[current_cat_name][0]

		# --- REJILLA DE ELEMENTOS ---
		pr.draw_text(tr("elements"), 15, 135, 12, pr.GRAY)
		
		start_x = 15
		start_y = 155
		icon_box_size = 36  
		spacing = 6
		columns = max(1, (self.width - 30) // (icon_box_size + spacing))
		
		for idx, tile in enumerate(self.tiles_by_cat[current_cat_name]):
			row = idx // columns
			col = idx % columns
			
			box_x = start_x + col * (icon_box_size + spacing)
			box_y = start_y + row * (icon_box_size + spacing)
			
			mouse_pos = pr.get_mouse_position()
			if pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
				if (box_x <= mouse_pos.x <= box_x + icon_box_size and 
					box_y <= mouse_pos.y <= box_y + icon_box_size):
					self.selected_tile = tile
			is_selected = (self.selected_tile == tile)
			border_color = pr.YELLOW if is_selected else (60, 60, 60, 255)
			bg_color = (45, 45, 45, 255) if is_selected else (35, 35, 35, 255)
			
			pr.draw_rectangle(box_x, box_y, icon_box_size, icon_box_size, bg_color)
			pr.draw_rectangle_lines(box_x, box_y, icon_box_size, icon_box_size, border_color)
			
			margin = 4
			pr.draw_texture_pro(
				tile["tex"],
				pr.Rectangle(0, 0, tile["tex"].width, tile["tex"].height),
				pr.Rectangle(box_x + margin, box_y + margin, icon_box_size - (margin * 2), icon_box_size - (margin * 2)),
				pr.Vector2(0, 0),
				0.0,
				pr.WHITE
			)
			
		return None

	def unload(self):
		
		if self.bg_texture is not None:
			pr.unload_texture(self.bg_texture)
			
		for cat in self.tiles_by_cat:
			for tile in self.tiles_by_cat[cat]:
				pr.unload_texture(tile["tex"])
