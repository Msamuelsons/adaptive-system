import math
import pygame
import os
import random
import py_trees
from py_trees.common import Status

# Inicialização do Pygame
pygame.init()
SCREEN_WIDTH = 920
SCREEN_HEIGHT = 420
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Autonomous Duel")
font = pygame.font.Font(None, 24)
text_color = (255, 255, 255)

# Carrega e ajusta o background
background = pygame.image.load("resources/sprites/background.png")
background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))


# ----- Classe Avatar -----
class Avatar:
    def __init__(self, name, x, y, left_key, right_key, attack_key=None,
                 idle_folder="Idle", run_folder="Run",
                 scale=1.0, width=None, height=None, text_offset=-20,
                 health_bar_offset=-10):
        self.name = name
        self.scale = scale
        self.custom_width = width
        self.custom_height = height
        self.text_offset = text_offset
        self.health_bar_offset = health_bar_offset

        # Barra de vida
        self.max_hp = 500
        self.hp = 500

        self.attack_key = attack_key
        self.idle_frames = self.load_animation_frames(idle_folder)
        self.run_frames = self.load_animation_frames(run_folder)
        self.attack_frames = self.load_animation_frames("Attack")

        # Estado e animação
        self.current_frames = self.idle_frames
        self.current_frame = 0
        self.facing_right = True  # Valor definido pela AI: True significa "olhar para a direita"
        self.is_attacking = False
        self.is_moving = False  # flag para animação de corrida (usada pela IA)
        self.rect = self.idle_frames[0].get_rect(center=(x, y))
        self.animation_speed = 120  # ms entre frames
        self.last_update = pygame.time.get_ticks()
        self.left_key = left_key
        self.right_key = right_key
        self.text_surface = font.render(self.name, True, text_color)
        self.has_dealt_damage = False
        self.attack_finished = False

    def load_animation_frames(self, folder):
        folder_path = os.path.join("resources/sprites", self.name, folder)
        frames = []
        for file_name in sorted(os.listdir(folder_path)):
            if file_name.lower().endswith('.png'):
                frame = pygame.image.load(os.path.join(folder_path, file_name)).convert_alpha()
                if self.custom_width and self.custom_height:
                    frame = pygame.transform.scale(frame, (self.custom_width, self.custom_height))
                else:
                    frame = pygame.transform.scale_by(frame, self.scale)
                frames.append(frame)
        return frames

    def update(self, keys):
        now = pygame.time.get_ticks()
        # Se houver controle manual (não é o caso aqui)
        if self.left_key is not None and self.right_key is not None:
            if not self.is_attacking and self.attack_key is not None and keys[self.attack_key]:
                self.is_attacking = True
                self.current_frames = self.attack_frames
                self.current_frame = 0
                self.last_update = now
                self.has_dealt_damage = False
                self.attack_finished = False

            if self.is_attacking:
                if now - self.last_update > self.animation_speed:
                    self.current_frame += 1
                    self.last_update = now
                    if self.current_frame >= len(self.attack_frames):
                        self.is_attacking = False
                        self.current_frames = self.idle_frames
                        self.current_frame = 0
                        self.attack_finished = True
            else:
                move_x = 0
                if keys[self.left_key]:
                    move_x = -2
                    self.facing_right = False
                    new_frames = self.run_frames
                elif keys[self.right_key]:
                    move_x = 2
                    self.facing_right = True
                    new_frames = self.run_frames
                else:
                    new_frames = self.idle_frames

                self.rect.x += move_x
                self.rect.left = max(0, self.rect.left)
                self.rect.right = min(SCREEN_WIDTH, self.rect.right)

                if new_frames != self.current_frames:
                    self.current_frames = new_frames
                    self.current_frame = 0

                if now - self.last_update > self.animation_speed:
                    self.current_frame = (self.current_frame + 1) % len(self.current_frames)
                    self.last_update = now
        else:
            # Controle autônomo (IA)
            if self.is_attacking:
                if now - self.last_update > self.animation_speed:
                    self.current_frame += 1
                    self.last_update = now
                    if self.current_frame >= len(self.attack_frames):
                        self.is_attacking = False
                        self.current_frames = self.idle_frames
                        self.current_frame = 0
                        self.attack_finished = True
            else:
                new_frames = self.run_frames if self.is_moving else self.idle_frames
                if new_frames != self.current_frames:
                    self.current_frames = new_frames
                    self.current_frame = 0

                if now - self.last_update > self.animation_speed:
                    self.current_frame = (self.current_frame + 1) % len(self.current_frames)
                    self.last_update = now

            self.is_moving = False

    def draw_health_bar(self, screen):
        bar_width = 60
        bar_height = 10 / math.pi
        fill = (self.hp / self.max_hp) * bar_width
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.top + self.health_bar_offset

        background_bar = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(screen, (60, 60, 60), background_bar)
        health_bar = pygame.Rect(bar_x, bar_y, fill, bar_height)
        pygame.draw.rect(screen, (255, 0, 0), health_bar)
        hp_text = font.render(f"HP: {self.hp}", True, text_color)
        text_rect = hp_text.get_rect(center=(self.rect.centerx, bar_y - 10))
        screen.blit(hp_text, text_rect)

    def draw(self, screen):
        current_image = self.current_frames[self.current_frame]
        # Ajuste de flip para que cada avatar use seu lado padrão:
        if self.name == "avatarA":
            # avatarA é originalmente desenhado com face RIGHT
            if not self.facing_right:
                current_image = pygame.transform.flip(current_image, True, False)
        elif self.name == "avatarB":
            # avatarB é originalmente desenhado com face LEFT
            if self.facing_right:
                current_image = pygame.transform.flip(current_image, True, False)
        screen.blit(current_image, self.rect)
        text_position = (self.rect.centerx - (self.text_surface.get_width() // 2),
                         self.rect.top + self.text_offset)
        screen.blit(self.text_surface, text_position)
        self.draw_health_bar(screen)


# ----- Nós de Comportamento para a IA -----
# Cada nó recebe um "alvo" e um "controlado". Eles operam de forma simétrica.

class AICheckDistanceGreaterThan(py_trees.behaviour.Behaviour):
    def __init__(self, target, controlled, attack_threshold):
        super().__init__(f"CheckDist > {attack_threshold}")
        self.target = target
        self.controlled = controlled
        self.attack_threshold = attack_threshold

    def update(self):
        pixel_distance = abs(self.target.rect.centerx - self.controlled.rect.centerx)
        if pixel_distance > self.attack_threshold:
            return Status.SUCCESS
        return Status.FAILURE


class AICheckDistanceLessOrEqual(py_trees.behaviour.Behaviour):
    def __init__(self, target, controlled, attack_threshold):
        super().__init__(f"CheckDist <= {attack_threshold}")
        self.target = target
        self.controlled = controlled
        self.attack_threshold = attack_threshold

    def update(self):
        pixel_distance = abs(self.target.rect.centerx - self.controlled.rect.centerx)
        if pixel_distance <= self.attack_threshold:
            return Status.SUCCESS
        return Status.FAILURE


class AIApproach(py_trees.behaviour.Behaviour):
    def __init__(self, target, controlled, step_pixels):
        super().__init__("AIApproach")
        self.target = target
        self.controlled = controlled
        self.step_pixels = step_pixels

    def update(self):
        self.controlled.is_attacking = False
        self.controlled.current_frames = self.controlled.run_frames

        if self.controlled.rect.centerx > self.target.rect.centerx:
            self.controlled.rect.x -= self.step_pixels
            self.controlled.facing_right = False
        else:
            self.controlled.rect.x += self.step_pixels
            self.controlled.facing_right = True

        self.controlled.is_moving = True
        self.controlled.rect.left = max(0, self.controlled.rect.left)
        self.controlled.rect.right = min(SCREEN_WIDTH, self.controlled.rect.right)
        return Status.SUCCESS


class AIAttack(py_trees.behaviour.Behaviour):
    def __init__(self, target, controlled, damage=10):
        super().__init__("AIAttack")
        self.target = target
        self.controlled = controlled
        self.damage = damage
        self.min_attack_distance = 40  # distância mínima para iniciar o ataque

    def update(self):
        current_distance = abs(self.target.rect.centerx - self.controlled.rect.centerx)
        if current_distance < self.min_attack_distance:
            diff = self.min_attack_distance - current_distance
            if self.controlled.rect.centerx > self.target.rect.centerx:
                self.controlled.rect.x += diff
            else:
                self.controlled.rect.x -= diff

        if self.controlled.rect.centerx > self.target.rect.centerx:
            self.controlled.facing_right = False
        else:
            self.controlled.facing_right = True

        if not self.controlled.is_attacking:
            self.controlled.is_attacking = True
            self.controlled.current_frames = self.controlled.attack_frames
            self.controlled.current_frame = 0
            self.controlled.last_update = pygame.time.get_ticks()
            self.controlled.has_dealt_damage = False
            self.controlled.attack_finished = False
            print(f"AIAttack: {self.controlled.name} iniciou ataque")
        if self.controlled.attack_finished and not self.controlled.has_dealt_damage:
            if self.controlled.rect.colliderect(self.target.rect):
                self.target.hp = max(0, self.target.hp - self.damage)
                self.controlled.has_dealt_damage = True
                print(
                    f"AIAttack: {self.controlled.name} aplicou {self.damage} de dano em {self.target.name} (HP {self.target.name}: {self.target.hp})")
        return Status.SUCCESS


def create_ai_tree(target, controlled, attack_threshold=40, approach_step=1, attack_damage=10):
    root = py_trees.composites.Selector("AI Root", memory=True)

    approach_seq = py_trees.composites.Sequence("ApproachSeq", memory=True)
    approach_seq.add_children([
        AICheckDistanceGreaterThan(target, controlled, attack_threshold),
        AIApproach(target, controlled, approach_step)
    ])

    attack_seq = py_trees.composites.Sequence("AttackSeq", memory=True)
    attack_seq.add_children([
        AICheckDistanceLessOrEqual(target, controlled, attack_threshold),
        AIAttack(target, controlled, attack_damage)
    ])

    root.add_children([approach_seq, attack_seq])
    return root


# ----- Criação dos Avatares (controle autônomo para ambos) -----
avatarA = Avatar(
    name="avatarA",
    x=SCREEN_WIDTH // 2 - 300,
    y=SCREEN_HEIGHT // 2,
    left_key=None,
    right_key=None,
    attack_key=None,
    scale=2.0,
    text_offset=70,
    health_bar_offset=50,
    idle_folder="Idle",
    run_folder="Run"
)

avatarB = Avatar(
    name="avatarB",
    x=SCREEN_WIDTH // 2 + 300,
    y=SCREEN_HEIGHT // 2,
    left_key=None,
    right_key=None,
    attack_key=None,
    idle_folder="Idle",
    run_folder="walk",  # para corrida, utiliza a pasta "walk"
    scale=2.0,
    width=260,
    height=160,
    text_offset=10,
    health_bar_offset=-10
)

ai_tree_A = create_ai_tree(avatarB, avatarA, attack_threshold=40, approach_step=1, attack_damage=10)
ai_tree_B = create_ai_tree(avatarA, avatarB, attack_threshold=40, approach_step=1, attack_damage=10)

# ----- Loop Principal do Jogo -----
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    ai_tree_A.tick_once()
    ai_tree_B.tick_once()

    avatarA.update(keys)
    avatarB.update(keys)

    screen.blit(background, (0, 0))
    avatarA.draw(screen)
    avatarB.draw(screen)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
