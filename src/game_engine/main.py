import pygame
import os

# Inicializa o Pygame
pygame.init()

# Configurações da tela
SCREEN_WIDTH = 920
SCREEN_HEIGHT = 420
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Adaptive System")

# Configurações de fonte
font = pygame.font.Font(None, 24)  # Usa a fonte padrão com tamanho 24
text_color = (255, 255, 255)  # Branco
text_surface = font.render("Avatar A", True, text_color)

# Carrega o fundo
background = pygame.image.load("resources/sprites/background.png")
background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Configurações de redimensionamento
SCALE_FACTOR = 3.5
PLAYER_SPEED = 5


# Carrega as animações
def load_animation_frames(folder_path, scale):
    frames = []
    for file_name in sorted(os.listdir(folder_path)):
        if file_name.lower().endswith('.png'):
            frame = pygame.image.load(os.path.join(folder_path, file_name)).convert_alpha()
            frame = pygame.transform.scale_by(frame, scale)
            frames.append(frame)
    return frames


# Carrega todos os conjuntos de animação
idle_frames = load_animation_frames("resources/sprites/Idle", SCALE_FACTOR)
run_frames = load_animation_frames("resources/sprites/Run", SCALE_FACTOR)

# Estados do personagem
current_frames = idle_frames
current_frame = 0
facing_right = True
is_running = False

# Configurações de animação
animation_speed = 100  # ms entre frames
last_update = pygame.time.get_ticks()

# Posicionamento inicial
player_rect = idle_frames[0].get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

clock = pygame.time.Clock()
running = True

while running:
    # Eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Controles
    keys = pygame.key.get_pressed()
    move_x = 0

    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        move_x = -PLAYER_SPEED
        facing_right = False
        is_running = True
    elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        move_x = PLAYER_SPEED
        facing_right = True
        is_running = True
    else:
        is_running = False

    # Atualiza posição
    player_rect.x += move_x

    # Mantém o jogador dentro da tela
    player_rect.left = max(0, player_rect.left)
    player_rect.right = min(SCREEN_WIDTH, player_rect.right)

    # Atualiza animação
    now = pygame.time.get_ticks()
    if is_running:
        current_frames = run_frames
    else:
        current_frames = idle_frames

    if now - last_update > animation_speed:
        current_frame = (current_frame + 1) % len(current_frames)
        last_update = now

    # Renderização
    screen.blit(background, (0, 0))

    # Desenha o personagem
    current_image = current_frames[current_frame]
    if not facing_right:
        current_image = pygame.transform.flip(current_image, True, False)
    screen.blit(current_image, player_rect)

    # Desenha o nome do avatar
    text_position = (player_rect.centerx - (text_surface.get_width() // 2),
                     player_rect.top - 30)  # 30 pixels acima do personagem
    screen.blit(text_surface, text_position)

    pygame.display.flip()

    clock.tick(60)

pygame.quit()
