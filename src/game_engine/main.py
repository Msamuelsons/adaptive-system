import math
import pygame
import os
import random
import py_trees
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from py_trees.common import Status

# Inicialização do Pygame
pygame.init()
SCREEN_WIDTH = 1020
SCREEN_HEIGHT = 680
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Autonomous Duel - Fuzzy Logic Edition")
font = pygame.font.Font(None, 24)
text_color = (255, 255, 255)

# Carrega e ajusta o background
background = pygame.image.load("resources/sprites/background.png")
background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))


# ----- Sistema Fuzzy para Danos -----
def create_fuzzy_damage_system():
    # Definindo as variáveis fuzzy
    anger = ctrl.Antecedent(np.arange(0, 16, 0.5), 'anger')
    hp_percentage = ctrl.Antecedent(np.arange(0, 101, 1), 'hp_percentage')
    damage = ctrl.Consequent(np.arange(10, 101, 1), 'damage')

    # Funções de pertinência para a raiva
    anger['low'] = fuzz.trimf(anger.universe, [0, 0, 5])
    anger['medium'] = fuzz.trimf(anger.universe, [0, 5, 10])
    anger['high'] = fuzz.trimf(anger.universe, [5, 10, 15])
    anger['berserk'] = fuzz.trimf(anger.universe, [10, 15, 15])

    # Funções de pertinência para o HP%
    hp_percentage['critical'] = fuzz.trimf(hp_percentage.universe, [0, 0, 30])
    hp_percentage['low'] = fuzz.trimf(hp_percentage.universe, [0, 30, 60])
    hp_percentage['medium'] = fuzz.trimf(hp_percentage.universe, [30, 60, 90])
    hp_percentage['high'] = fuzz.trimf(hp_percentage.universe, [60, 100, 100])

    # Funções de pertinência para o dano
    damage['low'] = fuzz.trimf(damage.universe, [10, 10, 35])
    damage['medium'] = fuzz.trimf(damage.universe, [20, 45, 70])
    damage['high'] = fuzz.trimf(damage.universe, [50, 75, 90])
    damage['critical'] = fuzz.trimf(damage.universe, [70, 100, 100])

    # Regras fuzzy
    rule1 = ctrl.Rule(anger['low'] & hp_percentage['high'], damage['low'])
    rule2 = ctrl.Rule(anger['medium'] & hp_percentage['high'], damage['medium'])
    rule3 = ctrl.Rule(anger['high'] & hp_percentage['high'], damage['high'])
    rule4 = ctrl.Rule(anger['berserk'] & hp_percentage['high'], damage['critical'])

    rule5 = ctrl.Rule(anger['low'] & hp_percentage['medium'], damage['low'])
    rule6 = ctrl.Rule(anger['medium'] & hp_percentage['medium'], damage['medium'])
    rule7 = ctrl.Rule(anger['high'] & hp_percentage['medium'], damage['high'])
    rule8 = ctrl.Rule(anger['berserk'] & hp_percentage['medium'], damage['critical'])

    rule9 = ctrl.Rule(anger['low'] & hp_percentage['low'], damage['medium'])
    rule10 = ctrl.Rule(anger['medium'] & hp_percentage['low'], damage['high'])
    rule11 = ctrl.Rule(anger['high'] & hp_percentage['low'], damage['critical'])
    rule12 = ctrl.Rule(anger['berserk'] & hp_percentage['low'], damage['critical'])

    rule13 = ctrl.Rule(anger['low'] & hp_percentage['critical'], damage['high'])
    rule14 = ctrl.Rule(anger['medium'] & hp_percentage['critical'], damage['high'])
    rule15 = ctrl.Rule(anger['high'] & hp_percentage['critical'], damage['critical'])
    rule16 = ctrl.Rule(anger['berserk'] & hp_percentage['critical'], damage['critical'])

    # Sistema de controle e simulação
    damage_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8,
                                      rule9, rule10, rule11, rule12, rule13, rule14, rule15, rule16])
    damage_sim = ctrl.ControlSystemSimulation(damage_ctrl)

    return damage_sim


# ----- Classe Avatar Estendida com Lógica Fuzzy -----
class FuzzyAvatar:
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

        # Define o dano de ataque padrão do avatar
        self.attack_damage = 10

        # Estado emocional para lógica fuzzy
        self.anger = 0  # Nível de raiva (0-15)
        self.berserk_mode = False
        self.damage_sim = create_fuzzy_damage_system()

        # Contadores de estados emocionais
        self.times_hit = 0
        self.successful_attacks = 0
        self.consecutive_hits = 0
        self.consecutive_misses = 0
        self.last_damage_received = 0

        self.attack_key = attack_key
        self.idle_frames = self.load_animation_frames(idle_folder)
        self.run_frames = self.load_animation_frames(run_folder)
        self.attack_frames = self.load_animation_frames("Attack")

        # Estado e animação
        self.current_frames = self.idle_frames
        self.current_frame = 0
        self.facing_right = True  # Ajusta o flip da imagem
        self.is_attacking = False
        self.is_moving = False
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
        # Controle manual (não é o caso aqui)
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
                        print(f"[DEBUG] {self.name} finalizou ataque")
            else:
                new_frames = self.run_frames if self.is_moving else self.idle_frames
                if new_frames != self.current_frames:
                    self.current_frames = new_frames
                    self.current_frame = 0

                if now - self.last_update > self.animation_speed:
                    self.current_frame = (self.current_frame + 1) % len(self.current_frames)
                    self.last_update = now

            self.is_moving = False

            # Atualização dos estados emocionais
            self.update_anger()
            self.update_berserk_mode()

    def update_anger(self):
        # A raiva aumenta com base em vários fatores

        # Fator 1: HP baixo aumenta a raiva
        hp_percentage = (self.hp / self.max_hp) * 100
        if hp_percentage < 30:
            self.anger = min(15, self.anger + 0.02)  # Aumento gradual quando HP está crítico
        elif hp_percentage < 50:
            self.anger = min(15, self.anger + 0.01)  # Aumento menor quando HP está baixo

        # Fator 2: Sofrer dano recentemente aumenta a raiva
        if self.last_damage_received > 0:
            anger_increase = (self.last_damage_received / self.max_hp) * 2  # Dano proporcional
            self.anger = min(15, self.anger + anger_increase)
            self.last_damage_received = max(0, self.last_damage_received - 0.2)  # Decai com o tempo

        # Fator 3: Ataques sucessivos aumentam a raiva (adrenalina)
        if self.consecutive_hits > 2:
            self.anger = min(15, self.anger + 0.05 * self.consecutive_hits)

        # Fator 4: Tempo sem acertar ataques aumenta a frustração
        if self.consecutive_misses > 3:
            self.anger = min(15, self.anger + 0.02 * self.consecutive_misses)

        # Decaimento natural da raiva ao longo do tempo
        self.anger = max(0, self.anger - 0.005)

    def update_berserk_mode(self):
        # Entra em modo berserk se a raiva for alta
        if self.anger >= 10:
            if not self.berserk_mode:
                print(f"[DEBUG] {self.name} ENTROU EM MODO BERSERK!!!")
                self.berserk_mode = True
        # Sai do modo berserk se a raiva diminuir significativamente
        elif self.anger < 5 and self.berserk_mode:
            print(f"[DEBUG] {self.name} saiu do modo berserk")
            self.berserk_mode = False

    def calculate_fuzzy_damage(self, base_damage=None):
        # Retorna dano calculado com lógica fuzzy
        hp_percentage = (self.hp / self.max_hp) * 100

        # Entrada para o sistema fuzzy
        self.damage_sim.input['anger'] = self.anger
        self.damage_sim.input['hp_percentage'] = hp_percentage

        # Computar o resultado fuzzy
        try:
            self.damage_sim.compute()
            damage = self.damage_sim.output['damage']

            # Converte para inteiro para facilitar a exibição
            return int(damage)
        except:
            # Fallback se o sistema fuzzy falhar
            if self.berserk_mode:
                return 60 if base_damage is None else base_damage * 2
            else:
                return 20 if base_damage is None else base_damage

    def receive_damage(self, damage_amount):
        """Quando o avatar recebe dano"""
        old_hp = self.hp
        self.hp = max(0, self.hp - damage_amount)
        self.times_hit += 1
        self.consecutive_misses = 0
        self.last_damage_received = damage_amount
        print(f"[DEBUG] {self.name} recebeu {damage_amount} de dano. HP: {old_hp} -> {self.hp}")

        # Aumento significativo de raiva ao receber muito dano
        if damage_amount > 50:
            self.anger = min(15, self.anger + 1.5)
        elif damage_amount > 30:
            self.anger = min(15, self.anger + 0.8)
        else:
            self.anger = min(15, self.anger + 0.4)

    def successful_attack(self):
        """Quando o avatar acerta um ataque"""
        self.successful_attacks += 1
        self.consecutive_hits += 1
        self.consecutive_misses = 0

        # Aumento de raiva/confiança ao acertar golpes sucessivos
        if self.consecutive_hits > 2:
            self.anger = min(15, self.anger + 0.3)

    def missed_attack(self):
        """Quando o avatar erra um ataque"""
        self.consecutive_hits = 0
        self.consecutive_misses += 1

        # Aumento de frustração/raiva ao errar
        if self.consecutive_misses > 2:
            self.anger = min(15, self.anger + 0.5)

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

        # Desenhar indicador de raiva
        anger_text = font.render(f"Raiva: {self.anger:.1f}", True,
                                 (255, 165, 0) if not self.berserk_mode else (255, 0, 0))
        anger_rect = anger_text.get_rect(center=(self.rect.centerx, bar_y - 30))
        screen.blit(anger_text, anger_rect)

        # Indicador visual de modo berserk
        if self.berserk_mode:
            berserk_text = font.render("BERSERK!", True, (255, 0, 0))
            berserk_rect = berserk_text.get_rect(center=(self.rect.centerx, bar_y - 50))
            screen.blit(berserk_text, berserk_rect)

    def draw(self, screen):
        current_image = self.current_frames[self.current_frame]
        # Ajuste de flip para que cada avatar use seu lado padrão:
        if self.name == "avatarA":
            if not self.facing_right:
                current_image = pygame.transform.flip(current_image, True, False)
        elif self.name == "avatarB":
            if self.facing_right:
                current_image = pygame.transform.flip(current_image, True, False)

        # Efeito visual para o modo berserk
        if self.berserk_mode:
            # Adiciona um leve brilho vermelho
            red_overlay = pygame.Surface(current_image.get_size(), pygame.SRCALPHA)
            red_overlay.fill((255, 0, 0, 30))  # Vermelho semitransparente
            current_image_copy = current_image.copy()
            current_image_copy.blit(red_overlay, (0, 0))
            screen.blit(current_image_copy, self.rect)
        else:
            screen.blit(current_image, self.rect)

        text_position = (self.rect.centerx - (self.text_surface.get_width() // 2),
                         self.rect.top + self.text_offset)
        screen.blit(self.text_surface, text_position)
        self.draw_health_bar(screen)


# ----- Nós de Comportamento para a IA com Lógica Fuzzy -----
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


class AICheckBerserkMode(py_trees.behaviour.Behaviour):
    def __init__(self, avatar):
        super().__init__(f"CheckBerserk {avatar.name}")
        self.avatar = avatar

    def update(self):
        if self.avatar.berserk_mode:
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

        # Em modo berserk, aproximação mais rápida
        actual_step = self.step_pixels * 2 if self.controlled.berserk_mode else self.step_pixels

        if self.controlled.rect.centerx > self.target.rect.centerx:
            self.controlled.rect.x -= actual_step
            self.controlled.facing_right = False
        else:
            self.controlled.rect.x += actual_step
            self.controlled.facing_right = True

        self.controlled.is_moving = True
        self.controlled.rect.left = max(0, self.controlled.rect.left)
        self.controlled.rect.right = min(SCREEN_WIDTH, self.controlled.rect.right)
        return Status.SUCCESS


class AIAttack(py_trees.behaviour.Behaviour):
    def __init__(self, target, controlled):
        super().__init__("AIAttack")
        self.target = target
        self.controlled = controlled
        self.attack_in_progress = False

    def update(self):
        if self.controlled.rect.centerx > self.target.rect.centerx:
            self.controlled.facing_right = False
        else:
            self.controlled.facing_right = True

        # Iniciando um novo ataque
        if not self.controlled.is_attacking and not self.attack_in_progress:
            self.controlled.is_attacking = True
            self.controlled.current_frames = self.controlled.attack_frames
            self.controlled.current_frame = 0
            self.controlled.last_update = pygame.time.get_ticks()
            self.controlled.has_dealt_damage = False
            self.attack_in_progress = True
            print(f"[DEBUG] {self.controlled.name} iniciou ataque contra {self.target.name}")
            return Status.RUNNING

        # Durante o ataque
        if self.controlled.is_attacking:
            return Status.RUNNING

        # Quando o ataque terminar (animation update vai definir attack_finished como True)
        if self.attack_in_progress and self.controlled.attack_finished and not self.controlled.has_dealt_damage:
            # Calcula o dano com base no sistema fuzzy
            damage_amount = self.controlled.calculate_fuzzy_damage()

            # Aplica o dano
            old_hp = self.target.hp
            self.target.receive_damage(damage_amount)
            self.controlled.has_dealt_damage = True
            self.attack_in_progress = False

            # Registra ataque bem-sucedido
            self.controlled.successful_attack()

            print(f"[DEBUG] {self.controlled.name} causou {damage_amount} de dano em {self.target.name}")
            print(f"[DEBUG] HP de {self.target.name} alterado: {old_hp} -> {self.target.hp}")
            return Status.SUCCESS

        return Status.RUNNING


class AIBerserkAttack(py_trees.behaviour.Behaviour):
    def __init__(self, target, controlled):
        super().__init__("AIBerserkAttack")
        self.target = target
        self.controlled = controlled
        self.attack_in_progress = False
        self.attack_count = 0
        self.max_attacks = 3  # Número de ataques consecutivos em modo berserk

    def update(self):
        if self.controlled.rect.centerx > self.target.rect.centerx:
            self.controlled.facing_right = False
        else:
            self.controlled.facing_right = True

        # Iniciando um novo ataque
        if not self.controlled.is_attacking and not self.attack_in_progress:
            self.controlled.is_attacking = True
            self.controlled.current_frames = self.controlled.attack_frames
            self.controlled.current_frame = 0
            self.controlled.last_update = pygame.time.get_ticks()
            self.controlled.has_dealt_damage = False
            self.attack_in_progress = True
            print(f"[DEBUG] {self.controlled.name} iniciou ataque BERSERK contra {self.target.name}")
            return Status.RUNNING

        # Durante o ataque
        if self.controlled.is_attacking:
            return Status.RUNNING

        # Quando o ataque terminar
        if self.attack_in_progress and self.controlled.attack_finished and not self.controlled.has_dealt_damage:
            # Calcula dano berserk (sempre o maior possível)
            self.controlled.anger = 15  # Força anger máximo para o cálculo
            damage_amount = self.controlled.calculate_fuzzy_damage()

            # Aplica o dano
            old_hp = self.target.hp
            self.target.receive_damage(damage_amount)
            self.controlled.has_dealt_damage = True
            self.attack_in_progress = False

            # Registra ataque bem-sucedido
            self.controlled.successful_attack()

            print(f"[DEBUG] {self.controlled.name} causou {damage_amount} de dano BERSERK em {self.target.name}")
            print(f"[DEBUG] HP de {self.target.name} alterado: {old_hp} -> {self.target.hp}")

            # Incrementa o contador de ataques
            self.attack_count += 1

            if self.attack_count >= self.max_attacks:
                self.attack_count = 0
                return Status.SUCCESS
            else:
                # Reinicia o ataque para o próximo golpe na sequência berserk
                self.attack_in_progress = False
                return Status.RUNNING

        return Status.RUNNING


def create_fuzzy_ai_tree(target, controlled, attack_threshold=40, approach_step=1):
    root = py_trees.composites.Selector("AI Root", memory=False)

    approach_seq = py_trees.composites.Sequence("ApproachSeq", memory=False)
    approach_seq.add_children([
        AICheckDistanceGreaterThan(target, controlled, attack_threshold),
        AIApproach(target, controlled, approach_step)
    ])

    attack_selector = py_trees.composites.Selector("AttackSelector", memory=False)

    # Ramo de ataque berserk
    berserk_seq = py_trees.composites.Sequence("BerserkSeq", memory=False)
    berserk_seq.add_children([
        AICheckBerserkMode(controlled),
        AIBerserkAttack(target, controlled)
    ])

    # Ramo de ataque normal
    normal_attack_seq = py_trees.composites.Sequence("NormalAttackSeq", memory=False)
    normal_attack_seq.add_children([
        AICheckDistanceLessOrEqual(target, controlled, attack_threshold),
        AIAttack(target, controlled)
    ])

    attack_selector.add_children([berserk_seq, normal_attack_seq])

    root.add_children([approach_seq, attack_selector])
    return root


# ----- Criação dos Avatares com Lógica Fuzzy -----
avatarA = FuzzyAvatar(
    name="avatarA",
    x=SCREEN_WIDTH // 2 - 300,
    y=SCREEN_HEIGHT // 2.2,
    left_key=None,
    right_key=None,
    attack_key=None,
    scale=2.0,
    text_offset=70,
    health_bar_offset=50,
    idle_folder="Idle",
    run_folder="Run"
)

avatarB = FuzzyAvatar(
    name="avatarB",
    x=SCREEN_WIDTH // 2 + 300,
    y=SCREEN_HEIGHT // 2,
    left_key=None,
    right_key=None,
    attack_key=None,
    idle_folder="Idle",
    run_folder="walk",
    scale=2.0,
    width=260,
    height=160,
    text_offset=10,
    health_bar_offset=-10
)

# Árvores de comportamento com lógica fuzzy para ambos avatares
ai_tree_A = create_fuzzy_ai_tree(avatarB, avatarA, attack_threshold=100, approach_step=1)
ai_tree_B = create_fuzzy_ai_tree(avatarA, avatarB, attack_threshold=100, approach_step=1)

clock = pygame.time.Clock()
running = True


def draw_debug_info(screen, avatarA, avatarB):
    distance = abs(avatarA.rect.centerx - avatarB.rect.centerx)
    debug_texts = [
        f"Distância: {distance} px",
        f"HP {avatarA.name}: {avatarA.hp}",
        f"HP {avatarB.name}: {avatarB.hp}",
        f"Raiva {avatarA.name}: {avatarA.anger:.1f} {'(BERSERK)' if avatarA.berserk_mode else ''}",
        f"Raiva {avatarB.name}: {avatarB.anger:.1f} {'(BERSERK)' if avatarB.berserk_mode else ''}",
        f"Pos. {avatarA.name}: ({avatarA.rect.x}, {avatarA.rect.y})",
        f"Pos. {avatarB.name}: ({avatarB.rect.x}, {avatarB.rect.y})"
    ]
    for i, text in enumerate(debug_texts):
        debug_surface = font.render(text, True, text_color)
        screen.blit(debug_surface, (10, 10 + i * 20))


def show_victory_screen(screen, winner_name):
    # Cria uma superfície preta semitransparente
    victory_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    victory_overlay.fill((0, 0, 0))
    victory_overlay.set_alpha(200)  # Define transparência (0-255)

    # Adiciona a superfície preta à tela
    screen.blit(victory_overlay, (0, 0))

    # Prepara o texto de vitória
    victory_font = pygame.font.Font(None, 72)
    victory_text = victory_font.render(f"{winner_name} VENCEU!", True, (255, 215, 0))  # Texto dourado

    # Adiciona uma sombra ao texto para destacar
    shadow_text = victory_font.render(f"{winner_name} VENCEU!", True, (128, 0, 0))
    shadow_rect = shadow_text.get_rect(center=(SCREEN_WIDTH // 2 + 3, SCREEN_HEIGHT // 2 + 3))

    # Posiciona o texto no centro da tela
    text_rect = victory_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

    # Desenha a sombra e depois o texto
    screen.blit(shadow_text, shadow_rect)
    screen.blit(victory_text, text_rect)

    # Adiciona instruções para reiniciar ou sair
    restart_font = pygame.font.Font(None, 36)
    restart_text = restart_font.render("Pressione 'R' para reiniciar ou 'ESC' para sair", True, (255, 255, 255))
    restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
    screen.blit(restart_text, restart_rect)


# Modificar o loop while running: para:
game_over = False
winner_name = None

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Adicionando tratamento de teclas para reiniciar o jogo
        if game_over and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:  # Reiniciar o jogo
                # Resetar os avatares
                avatarA.hp = avatarA.max_hp
                avatarA.anger = 0
                avatarA.berserk_mode = False
                avatarA.rect.x = SCREEN_WIDTH // 2 - 300

                avatarB.hp = avatarB.max_hp
                avatarB.anger = 0
                avatarB.berserk_mode = False
                avatarB.rect.x = SCREEN_WIDTH // 2 + 300

                game_over = False
                winner_name = None
            elif event.key == pygame.K_ESCAPE:  # Sair do jogo
                running = False

    keys = pygame.key.get_pressed()

    # Se o jogo não terminou, continua com a lógica normal
    if not game_over:
        # Atualiza os avatares (processa animações e attack_finished)
        avatarA.update(keys)
        avatarB.update(keys)

        # Tica as árvores de comportamento
        ai_tree_A.tick_once()
        ai_tree_B.tick_once()

        # Verifica se algum dos avatares morreu
        if avatarA.hp <= 0:
            game_over = True
            winner_name = avatarB.name
            print(f"Jogo terminado! {winner_name} venceu!")
        elif avatarB.hp <= 0:
            game_over = True
            winner_name = avatarA.name
            print(f"Jogo terminado! {winner_name} venceu!")

    # Renderização
    screen.blit(background, (0, 0))
    avatarA.draw(screen)
    avatarB.draw(screen)
    draw_debug_info(screen, avatarA, avatarB)

    # Se o jogo terminou, mostra a tela de vitória
    if game_over:
        show_victory_screen(screen, winner_name)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()