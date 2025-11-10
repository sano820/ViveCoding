import tkinter as tk
import random
import os

# ====== 설정 ======
WIDTH = 400
HEIGHT = 400
CELL_SIZE = 20
START_SPEED = 150

HIGHSCORE_FILE = "highscore.txt"

# ====== 유틸 ======
def load_highscore():
    if os.path.exists(HIGHSCORE_FILE):
        with open(HIGHSCORE_FILE, "r") as f:
            return int(f.read().strip() or 0)
    return 0

def save_highscore(score):
    with open(HIGHSCORE_FILE, "w") as f:
        f.write(str(score))

# ====== 게임 클래스 ======
class SnakeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("🐍 Snake Game")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="black")
        self.canvas.pack()

        # UI 구성
        self.score_label = tk.Label(root, text="Score: 0", font=("Arial", 14))
        self.score_label.pack()
        self.high_label = tk.Label(root, text=f"High Score: {load_highscore()}", font=("Arial", 12))
        self.high_label.pack()

        # 상태 초기화
        self.reset_game()

        # 시작 화면
        self.show_start_screen()

    def show_start_screen(self):
        self.canvas.delete("all")
        self.canvas.create_text(WIDTH/2, HEIGHT/2 - 40, fill="white", font=("Arial", 24, "bold"),
                                text="🐍 Snake Game 🐍")
        self.canvas.create_text(WIDTH/2, HEIGHT/2 + 10, fill="gray", font=("Arial", 14),
                                text="Press SPACE to Start")
        self.canvas.create_text(WIDTH/2, HEIGHT/2 + 40, fill="gray", font=("Arial", 10),
                                text="Use Arrow Keys to Move")
        self.root.bind("<space>", self.start_game)

    def reset_game(self):
        self.direction = "Right"
        self.snake = [(100, 100), (80, 100), (60, 100)]
        self.food = self.spawn_food()
        self.score = 0
        self.speed = START_SPEED
        self.is_running = False

    def start_game(self, event=None):
        self.reset_game()
        self.root.bind("<KeyPress>", self.change_direction)
        self.is_running = True
        self.update()

    def spawn_food(self):
        while True:
            x = random.randint(0, (WIDTH - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
            y = random.randint(0, (HEIGHT - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
            if (x, y) not in self.snake:
                return (x, y)

    def move(self):
        head_x, head_y = self.snake[0]
        if self.direction == "Up":
            head_y -= CELL_SIZE
        elif self.direction == "Down":
            head_y += CELL_SIZE
        elif self.direction == "Left":
            head_x -= CELL_SIZE
        elif self.direction == "Right":
            head_x += CELL_SIZE

        new_head = (head_x, head_y)

        # 충돌 확인
        if (head_x < 0 or head_x >= WIDTH or head_y < 0 or head_y >= HEIGHT or new_head in self.snake):
            self.game_over()
            return False

        self.snake.insert(0, new_head)
        if new_head == self.food:
            self.score += 10
            self.speed = max(50, self.speed - 3)  # 점점 빨라짐
            self.food = self.spawn_food()
        else:
            self.snake.pop()
        return True

    def draw(self):
        self.canvas.delete("all")

        # 뱀
        for i, (x, y) in enumerate(self.snake):
            color = "lime" if i == 0 else "green"
            self.canvas.create_rectangle(x, y, x + CELL_SIZE, y + CELL_SIZE, fill=color)

        # 먹이
        fx, fy = self.food
        self.canvas.create_oval(fx, fy, fx + CELL_SIZE, fy + CELL_SIZE, fill="red")

        # 점수
        self.score_label.config(text=f"Score: {self.score}")
        self.high_label.config(text=f"High Score: {load_highscore()}")

    def change_direction(self, event):
        if not self.is_running:
            return
        key = event.keysym
        opposite = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}
        if key in opposite and key != opposite[self.direction]:
            self.direction = key

    def update(self):
        if not self.is_running:
            return
        if self.move():
            self.draw()
            self.root.after(self.speed, self.update)

    def game_over(self):
        self.is_running = False
        high = load_highscore()
        if self.score > high:
            save_highscore(self.score)

        self.canvas.create_text(WIDTH/2, HEIGHT/2 - 20, fill="white", font=("Arial", 20, "bold"),
                                text="💀 GAME OVER 💀")
        self.canvas.create_text(WIDTH/2, HEIGHT/2 + 20, fill="gray", font=("Arial", 12),
                                text="Press SPACE to Restart")
        self.root.bind("<space>", self.start_game)

# ====== 실행 ======
if __name__ == "__main__":
    root = tk.Tk()
    SnakeGame(root)
    root.mainloop()
