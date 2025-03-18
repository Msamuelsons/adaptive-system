import py_trees
from py_trees.common import Status
import pygame


class AICheckDistanceGreaterThan(py_trees.behaviour.Behaviour):
    def __init__(self, avatar_a, avatar_b, threshold_pixels):
        super().__init__("CheckDist > " + str(threshold_pixels))
        self.avatar_a = avatar_a
        self.avatar_b = avatar_b
        self.threshold_pixels = threshold_pixels

    def update(self):
        pixel_distance = abs(self.avatar_a.rect.centerx - self.avatar_b.rect.centerx)
        if pixel_distance > self.threshold_pixels:
            return Status.SUCCESS
        return Status.FAILURE


class AICheckDistanceLessOrEqual(py_trees.behaviour.Behaviour):
    def __init__(self, avatar_a, avatar_b, threshold_pixels):
        super().__init__("CheckDist <= " + str(threshold_pixels))
        self.avatar_a = avatar_a
        self.avatar_b = avatar_b
        self.threshold_pixels = threshold_pixels

    def update(self):
        pixel_distance = abs(self.avatar_a.rect.centerx - self.avatar_b.rect.centerx)
        if pixel_distance <= self.threshold_pixels:
            return Status.SUCCESS
        return Status.FAILURE


class AIApproach(py_trees.behaviour.Behaviour):
    def __init__(self, avatar_a, avatar_b, step_pixels):
        super().__init__("AIApproach")
        self.avatar_a = avatar_a
        self.avatar_b = avatar_b
        self.step_pixels = step_pixels

    def update(self):
        # Move avatarB na direção do avatarA
        if self.avatar_b.rect.centerx > self.avatar_a.rect.centerx:
            self.avatar_b.rect.x -= self.step_pixels
        else:
            self.avatar_b.rect.x += self.step_pixels
        print(f"AIApproach: avatarB moveu {self.step_pixels} pixels")
        return Status.SUCCESS


class AIAttack(py_trees.behaviour.Behaviour):
    def __init__(self, avatar_a, avatar_b, damage=10):
        super().__init__("AIAttack")
        self.avatar_a = avatar_a
        self.avatar_b = avatar_b
        self.damage = damage

    def update(self):
        # Inicia o ataque se ainda não estiver ocorrendo
        if not self.avatar_b.is_attacking:
            self.avatar_b.is_attacking = True
            self.avatar_b.current_frames = self.avatar_b.attack_frames
            self.avatar_b.current_frame = 0
            self.avatar_b.last_update = pygame.time.get_ticks()
            self.avatar_b.has_dealt_damage = False
            self.avatar_b.attack_finished = False
            print("AIAttack: avatarB iniciou ataque")

        # Aplica o dano assim que a animação de ataque terminar
        if self.avatar_b.attack_finished and not self.avatar_b.has_dealt_damage:
            self.avatar_a.hp = max(0, self.avatar_a.hp - self.damage)
            self.avatar_b.has_dealt_damage = True
            print(f"AIAttack: avatarB aplicou {self.damage} de dano em avatarA (HP A: {self.avatar_a.hp})")
        return Status.SUCCESS


def create_ai_tree(avatar_a, avatar_b, threshold_pixels=50, approach_step=50, attack_damage=10):
    """
    Cria uma árvore de comportamento para controlar o avatarB:
      - Se a distância (em pixels) entre avatarA e avatarB for maior que o threshold,
        avatarB se aproxima.
      - Se estiverem próximos (<= threshold), avatarB ataca avatarA.
    """
    root = py_trees.composites.Selector("AI Root")

    # Sequência de aproximação
    approach_seq = py_trees.composites.Sequence("ApproachSeq")
    approach_seq.add_children([
        AICheckDistanceGreaterThan(avatar_a, avatar_b, threshold_pixels),
        AIApproach(avatar_a, avatar_b, approach_step)
    ])

    # Sequência de ataque
    attack_seq = py_trees.composites.Sequence("AttackSeq")
    attack_seq.add_children([
        AICheckDistanceLessOrEqual(avatar_a, avatar_b, threshold_pixels),
        AIAttack(avatar_a, avatar_b, attack_damage)
    ])

    root.add_children([approach_seq, attack_seq])
    return root
