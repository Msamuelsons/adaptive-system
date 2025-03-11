import pygame
import os

# Inicialização do Pygame
pygame.init()

# Configurações da tela
SCREEN_WIDTH = 920
SCREEN_HEIGHT = 420
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Adaptive System")

# Configurações de fonte
font = pygame.font.Font(None, 24)
text_color = (255, 255, 255)

# Carrega o fundo
background = pygame.image.load("resources/sprites/background.png")
background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Velocidade base dos avatares
PLAYER_SPEED = 1


class Avatar:
    def __init__(self, name, x, y, left_key, right_key,
                 idle_folder="Idle", run_folder="Run",
                 scale=1.0, width=None, height=None, text_offset=-20):
        self.name = name
        self.scale = scale
        self.custom_width = width
        self.custom_height = height
        self.text_offset = text_offset

        # Carrega as animações
        self.idle_frames = self.load_animation_frames(idle_folder)
        self.run_frames = self.load_animation_frames(run_folder)

        # Configurações iniciais
        self.current_frames = self.idle_frames
        self.current_frame = 0
        self.facing_right = True
        self.is_running = False
        self.rect = self.idle_frames[0].get_rect(center=(x, y))
        self.animation_speed = 100  # ms entre frames
        self.last_update = pygame.time.get_ticks()
        self.left_key = left_key
        self.right_key = right_key
        self.text_surface = font.render(self.name, True, text_color)

    def load_animation_frames(self, folder):
        folder_path = os.path.join("resources/sprites", self.name, folder)
        frames = []
        for file_name in sorted(os.listdir(folder_path)):
            if file_name.lower().endswith('.png'):
                frame = pygame.image.load(os.path.join(folder_path, file_name)).convert_alpha()
                # Redimensionamento
                if self.custom_width and self.custom_height:
                    frame = pygame.transform.scale(frame, (self.custom_width, self.custom_height))
                else:
                    frame = pygame.transform.scale_by(frame, self.scale)
                frames.append(frame)
        return frames

    def update(self, keys):
        move_x = 0
        # Define o estado e os frames de acordo com a tecla pressionada
        if keys[self.left_key]:
            move_x = -PLAYER_SPEED
            self.facing_right = False
            new_running_state = True
            new_frames = self.run_frames
        elif keys[self.right_key]:
            move_x = PLAYER_SPEED
            self.facing_right = True
            new_running_state = True
            new_frames = self.run_frames
        else:
            new_running_state = False
            new_frames = self.idle_frames

        # Atualiza posição
        self.rect.x += move_x
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(SCREEN_WIDTH, self.rect.right)

        # Se houver mudança de animação, reinicia o índice do frame
        if new_frames != self.current_frames:
            self.current_frames = new_frames
            self.current_frame = 0

        self.is_running = new_running_state

        # Atualiza a animação com base no tempo decorrido
        now = pygame.time.get_ticks()
        if now - self.last_update > self.animation_speed:
            self.current_frame = (self.current_frame + 1) % len(self.current_frames)
            self.last_update = now

    def draw(self, screen):
        current_image = self.current_frames[self.current_frame]

        if not self.facing_right:
            if self.name != "avatarB":
                current_image = pygame.transform.flip(current_image, True, False)
        else:
            if self.name == "avatarB":
                current_image = pygame.transform.flip(current_image, True, False)

        screen.blit(current_image, self.rect)
        text_position = (self.rect.centerx - (self.text_surface.get_width() // 2),
                         self.rect.top + self.text_offset)
        screen.blit(self.text_surface, text_position)


# Criação dos avatares
avatar_a = Avatar(
    name="avatarA",
    x=SCREEN_WIDTH // 2 - 100,
    y=SCREEN_HEIGHT // 2,
    left_key=pygame.K_a,
    right_key=pygame.K_d,
    scale=2.0,
    text_offset=70
)

avatar_b = Avatar(
    name="avatarB",
    x=SCREEN_WIDTH // 2 + 100,
    y=SCREEN_HEIGHT // 2,
    left_key=pygame.K_j,
    right_key=pygame.K_l,
    idle_folder="Idle",
    run_folder="walk",
    scale=2.0,
    width=260,
    height=160,
    text_offset=10
)

# Loop principal
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    # Atualiza os avatares
    avatar_a.update(keys)
    avatar_b.update(keys)

    # Renderiza a tela
    screen.blit(background, (0, 0))
    avatar_a.draw(screen)
    avatar_b.draw(screen)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
