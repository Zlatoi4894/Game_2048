import customtkinter as ctk
import tkinter as tk
import time
import json
import os

from logic import Logic


__all__ = ["UI"]


class UI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.logic = Logic()

        self.score_file = "data/score.json"

        self.board_size = 4
        self.cell_size = 100
        self.gap = 9

        self.board_width = (
            self.cell_size * self.board_size
            + self.gap * (self.board_size + 1)
        )

        self.board_height = self.board_width

        # ==========================================================
        # АНИМАЦИЯ
        # ==========================================================

        self.animating = False
        self.animation_duration = 150
        self.animation_start_time = None
        self.animation_after_id = None
        self.animation_tiles = []

        self.game_over = False

        # ==========================================================
        # ЦВЕТА
        # ==========================================================

        self.cell_colors = {
            0: "#cdc1b4",
            2: "#eee4da",
            4: "#ede0c8",
            8: "#f2b179",
            16: "#f59563",
            32: "#f67c5f",
            64: "#f65e3b",
            128: "#edcf72",
            256: "#edcc61",
            512: "#edc850",
            1024: "#edc53f",
            2048: "#edc22e"
        }

        self.text_colors = {
            0: "#776e65",
            2: "#776e65",
            4: "#776e65",
            8: "#f9f6f2",
            16: "#f9f6f2",
            32: "#f9f6f2",
            64: "#f9f6f2",
            128: "#f9f6f2",
            256: "#f9f6f2",
            512: "#f9f6f2",
            1024: "#f9f6f2",
            2048: "#f9f6f2"
        }

        self.best_score = self.load_best_score()

        # ==========================================================
        # ОКНО
        # ==========================================================

        self.title("2048")
        self.geometry("600x700")
        self.minsize(500, 600)
        self.configure(fg_color="#faf8ef")

        # ==========================================================
        # ОБЩАЯ ОБЛАСТЬ ИГРЫ
        # ==========================================================

        self.game_area_width = self.board_width + 80

        self.game_area = ctk.CTkFrame(
            self,
            width=self.game_area_width,
            height=650,
            fg_color="transparent"
        )

        self.game_area.place(
            relx=0.51,
            rely=0.5,
            anchor="center"
        )

        # ==========================================================
        # HEADER
        # ==========================================================

        self.header = ctk.CTkFrame(
            self.game_area,
            width=self.board_width,
            fg_color="transparent"
        )

        self.header.place(
            x=20,
            y=0
        )

        # ----------------------------------------------------------
        # Левая часть header
        # ----------------------------------------------------------

        self.title_frame = ctk.CTkFrame(
            self.header,
            fg_color="transparent"
        )

        self.title_frame.pack(
            side="left"
        )

        self.title_label = ctk.CTkLabel(
            self.title_frame,
            text="2048",
            font=ctk.CTkFont(
                size=48,
                weight="bold"
            ),
            text_color="#776e65"
        )

        self.title_label.pack(
            anchor="w"
        )

        self.subtitle_label = ctk.CTkLabel(
            self.title_frame,
            text="Соединяйте числа и доберитесь до 2048!",
            font=ctk.CTkFont(size=14),
            text_color="#776e65"
        )

        self.subtitle_label.pack(
            anchor="w",
            pady=(2, 0)
        )

        # ----------------------------------------------------------
        # Правая часть header
        # ----------------------------------------------------------

        self.header_right = ctk.CTkFrame(
            self.header,
            fg_color="transparent"
        )

        self.header_right.pack(
            side="right",
            anchor="n"
        )

        self.score_frame = ctk.CTkFrame(
            self.header_right,
            fg_color="transparent"
        )

        self.score_frame.pack(
            anchor="e"
        )

        self.score_label = ctk.CTkLabel(
            self.score_frame,
            text="Очки: 0",
            width=80,
            height=48,
            corner_radius=9,
            fg_color="#bbada0",
            text_color="#f9f6f2",
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            )
        )

        self.score_label.pack(
            side="left",
            padx=(0, 5)
        )

        self.best_score_label = ctk.CTkLabel(
            self.score_frame,
            text=f"Рекорд: {self.best_score}",
            width=80,
            height=48,
            corner_radius=6,
            fg_color="#bbada0",
            text_color="#f9f6f2",
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            )
        )

        self.best_score_label.pack(
            side="left"
        )

        self.restart_button = ctk.CTkButton(
            self.header_right,
            text="Новая игра",
            width=120,
            height=40,
            corner_radius=8,
            command=self.restart,
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            )
        )

        self.restart_button.pack(
            anchor="e",
            pady=(8, 0)
        )

        # ==========================================================
        # BOARD — CANVAS
        # ==========================================================

        self.board = tk.Canvas(
            self.game_area,
            width=self.board_width,
            height=self.board_height,
            bg="#bbada0",
            highlightthickness=0,
            bd=0
        )

        self.board.place(
            relx=0.49,
            rely=0.52,
            anchor="center"
        )

        # ==========================================================
        # ФОНОВЫЕ КЛЕТКИ
        # ==========================================================

        self.background_cells = []

        for y in range(self.board_size):
            row = []

            for x in range(self.board_size):

                x1 = self.cell_x(x)
                y1 = self.cell_y(y)

                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                cell = self.board.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=self.cell_colors[0],
                    outline=""
                )

                row.append(cell)

            self.background_cells.append(row)

        # ==========================================================
        # ТАЙЛЫ
        # ==========================================================

        # Каждый элемент содержит:
        #
        # {
        #     "rectangle": id прямоугольника,
        #     "text": id текста
        # }
        #
        # Всего максимум 16 тайлов.

        self.tile_widgets = []

        for _ in range(self.board_size * self.board_size):

            rectangle = self.board.create_rectangle(
                -self.cell_size * 2,
                -self.cell_size * 2,
                -self.cell_size,
                -self.cell_size,
                fill=self.cell_colors[0],
                outline=""
            )

            text = self.board.create_text(
                -self.cell_size * 2,
                -self.cell_size * 2,
                text="",
                fill=self.text_colors[0],
                font=("Arial", 32, "bold")
            )

            self.tile_widgets.append(
                {
                    "rectangle": rectangle,
                    "text": text
                }
            )

        # Позиция → тайл
        #
        # Например:
        #
        # {
        #     (0, 1): 0,
        #     (2, 3): 1
        # }

        self.tiles = {}

        self.update_board()

        # ==========================================================
        # GAME OVER
        # ==========================================================

        self.game_over_label = ctk.CTkLabel(
            self.game_area,
            text="",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            ),
            text_color="#d32f2f"
        )

        self.game_over_label.place(
            relx=0.5,
            rely=0.94,
            anchor="center"
        )

        # ==========================================================
        # CONTROLS
        # ==========================================================

        self.controls_label = ctk.CTkLabel(
            self.game_area,
            text="Используйте стрелки или WASD",
            font=ctk.CTkFont(size=16),
            text_color="#776e65"
        )

        self.controls_label.place(
            relx=0.5,
            rely=0.90,
            anchor="center"
        )

        # ==========================================================
        # УПРАВЛЕНИЕ
        # ==========================================================

        self.bind(
            "<Left>",
            lambda event: self.move("left")
        )

        self.bind(
            "<Right>",
            lambda event: self.move("right")
        )

        self.bind(
            "<Up>",
            lambda event: self.move("top")
        )

        self.bind(
            "<Down>",
            lambda event: self.move("bottom")
        )

        self.bind(
            "<a>",
            lambda event: self.move("left")
        )

        self.bind(
            "<d>",
            lambda event: self.move("right")
        )

        self.bind(
            "<w>",
            lambda event: self.move("top")
        )

        self.bind(
            "<s>",
            lambda event: self.move("bottom")
        )

        self.bind(
            "<A>",
            lambda event: self.move("left")
        )

        self.bind(
            "<D>",
            lambda event: self.move("right")
        )

        self.bind(
            "<W>",
            lambda event: self.move("top")
        )

        self.bind(
            "<S>",
            lambda event: self.move("bottom")
        )

        self.update_score()

    def load_best_score(self):
        try:
            with open(
                self.score_file,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

                return int(
                    data.get(
                        "best_score",
                        0
                    )
                )

        except (
            FileNotFoundError,
            json.JSONDecodeError,
            ValueError,
            TypeError
        ):
            return 0

    def save_best_score(self):
        os.makedirs("data", exist_ok=True)

        data = {
            "best_score": self.best_score
        }

        with open(
            self.score_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4
            )

    def update_score(self):
        current_score = self.logic.score

        self.score_label.configure(
            text=f"Очки: {current_score}"
        )

        if current_score > self.best_score:
            self.best_score = current_score

            self.save_best_score()

        self.best_score_label.configure(
            text=f"Рекорд: {self.best_score}"
        )

    def cell_x(self, x):
        return (
            self.gap + x * (self.cell_size + self.gap)
        )

    def cell_y(self, y):
        return (
            self.gap + y * (self.cell_size + self.gap)
        )

    def move_tile(self, tile, x, y):
        rectangle = self.tile_widgets[tile]["rectangle"]
        text = self.tile_widgets[tile]["text"]

        self.board.coords(rectangle, x, y, x + self.cell_size, y + self.cell_size)

        self.board.coords(text, x + self.cell_size / 2, y + self.cell_size / 2)

    def configure_tile(self, tile, value):
        if value >= 1024:
            font_size = 24

        elif value >= 128:
            font_size = 28

        else:
            font_size = 32

        rectangle = self.tile_widgets[tile]["rectangle"]
        text = self.tile_widgets[tile]["text"]

        self.board.itemconfigure(rectangle, fill=self.get_cell_color(value))

        self.board.itemconfigure(text, text=str(value), fill=self.get_text_color(value), font=("Arial", font_size, "bold"))

    def get_cell_color(self, value):
        if value in self.cell_colors:
            return self.cell_colors[value]

        return "#3c3a32"

    def get_text_color(self, value):
        if value in self.text_colors:
            return self.text_colors[value]

        return "#f9f6f2"

    def lift_tile(self, tile):
        self.board.tag_raise(self.tile_widgets[tile]["rectangle"])

        self.board.tag_raise(self.tile_widgets[tile]["text"])

    def hide_tile(self, tile):
        self.move_tile(tile, -self.cell_size * 2, -self.cell_size * 2)

    def move(self, direction):
        if self.animating:
            return

        if self.game_over:
            return

        changed, moves = self.logic.slide(direction)

        if not changed:
            return

        self.update_score()

        self.animating = True
        self.animation_tiles = []

        for move in moves:

            old_position = (move["old_y"], move["old_x"])

            tile = self.tiles.get(old_position)

            if tile is None:
                continue

            self.animation_tiles.append(
                {
                    "tile": tile,

                    "old_x": self.cell_x(move["old_x"]),

                    "old_y": self.cell_y(move["old_y"]),

                    "new_x": self.cell_x(move["new_x"]),

                    "new_y": self.cell_y(move["new_y"]),

                    "new_position": (move["new_y"], move["new_x"]),

                    "value": move["value"],

                    "merged": move["merged"]
                }
            )

        self.animation_start_time = time.perf_counter()

        self.animate_tiles()

    def animate_tiles(self):
        current_time = time.perf_counter()

        elapsed = current_time - self.animation_start_time

        progress = elapsed * 1000 / self.animation_duration

        progress = max(0.0, min(progress, 1.0))

        progress = progress * progress * (3 - 2 * progress)

        for animation in self.animation_tiles:

            old_x = animation["old_x"]
            old_y = animation["old_y"]

            new_x = animation["new_x"]
            new_y = animation["new_y"]

            x = old_x + (new_x - old_x) * progress

            y = old_y + (new_y - old_y) * progress

            self.move_tile(animation["tile"], x, y)

        if progress < 1.0:
            self.animation_after_id = self.after(8, self.animate_tiles)

            return

        self.finish_animation()

    def finish_animation(self):
        new_tiles = {}

        animated_widgets = set()

        for animation in self.animation_tiles:
            animated_widgets.add(animation["tile"])

        for animation in self.animation_tiles:
            tile = animation["tile"]

            position = animation["new_position"]

            value = self.logic.matrix[position[0]][position[1]]

            if position not in new_tiles:
                new_tiles[position] = tile

                self.configure_tile(tile, value)

                self.move_tile(tile, self.cell_x(position[1]), self.cell_y(position[0]))

                self.lift_tile(tile)

            else:
                survivor = new_tiles[position]

                self.configure_tile(survivor, value)

                self.hide_tile(tile)

        for position, tile in self.tiles.items():
            if tile not in animated_widgets:
                new_tiles[position] = tile

        self.tiles = new_tiles

        spawned = self.logic.spawn_tile()

        if spawned is not None:
            position = (spawned["y"], spawned["x"])

            tile = self.get_free_tile()

            self.configure_tile(tile, spawned["value"])

            self.tiles[position] = tile

            self.move_tile(tile, self.cell_x(position[1]), self.cell_y(position[0]))

            self.lift_tile(tile)

        if self.logic.is_game_over():
            self.game_over = True

            self.game_over_label.configure(text="Игра окончена!")

            self.game_over_label.lift()

        self.animation_tiles.clear()

        self.animating = False
        self.animation_start_time = None
        self.animation_after_id = None

    def get_free_tile(self):
        used_tiles = set(self.tiles.values())

        for tile in range(len(self.tile_widgets)):
            if tile not in used_tiles:
                return tile

        raise RuntimeError("Не найден свободный тайл.")

    def update_board(self):
        self.tiles.clear()

        for tile in range(len(self.tile_widgets)):
            self.hide_tile(tile)

        tile_index = 0

        for y in range(self.board_size):
            for x in range(self.board_size):
                value = self.logic.matrix[y][x]

                if value == 0:
                    continue

                tile = tile_index

                tile_index += 1

                self.configure_tile(tile, value)

                self.move_tile(tile, self.cell_x(x), self.cell_y(y))

                self.lift_tile(tile)

                self.tiles[(y, x)] = tile

    def restart(self):
        if self.animating:
            return

        self.logic = Logic()

        self.game_over = False

        self.game_over_label.configure(text="")

        self.update_board()

        self.update_score()