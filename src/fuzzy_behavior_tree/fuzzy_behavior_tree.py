import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import py_trees
from py_trees.common import Status


##############################################################################
#                              ESTADO DO JOGO                                #
##############################################################################
class GameState:
    def __init__(self):
        self.player_a_hp = 200
        self.player_b_hp = 200
        self.distance = 20  # Começam distantes
        self.state_berserk = False
        self.anger = 0  # Valor de raiva para o avatar B (0 a 10)


##############################################################################
#                          SISTEMA FUZZY PARA DANOS                          #
##############################################################################
# Definindo as variáveis fuzzy
anger = ctrl.Antecedent(np.arange(0, 16, 0.5), 'anger')
damage = ctrl.Consequent(np.arange(10, 41, 1), 'damage')

# Funções de pertinência para a raiva
anger['low'] = fuzz.trimf(anger.universe, [0, 0, 5])
anger['medium'] = fuzz.trimf(anger.universe, [0, 5, 10])
anger['high'] = fuzz.trimf(anger.universe, [5, 10, 10])

# Funções de pertinência para o dano
damage['low'] = fuzz.trimf(damage.universe, [10, 10, 25])
damage['medium'] = fuzz.trimf(damage.universe, [10, 25, 40])
damage['high'] = fuzz.trimf(damage.universe, [25, 40, 40])

# Regras fuzzy
rule1 = ctrl.Rule(anger['low'], damage['low'])
rule2 = ctrl.Rule(anger['medium'], damage['medium'])
rule3 = ctrl.Rule(anger['high'], damage['high'])

# Sistema de controle e simulação
damage_ctrl = ctrl.ControlSystem([rule1, rule2, rule3])
damage_sim = ctrl.ControlSystemSimulation(damage_ctrl)


##############################################################################
#                              COMPORTAMENTOS                                #
##############################################################################
class CheckDistanceGreaterThan(py_trees.behaviour.Behaviour):
    """
    Retorna SUCCESS se a distância for maior que 'threshold'.
    Caso contrário, retorna FAILURE.
    """

    def __init__(self, game_state, threshold):
        super().__init__(name=f"CheckDist > {threshold}")
        self.game_state = game_state
        self.threshold = threshold

    def update(self):
        if self.game_state.distance > self.threshold:
            return Status.SUCCESS
        return Status.FAILURE


class CheckDistanceLessOrEqual(py_trees.behaviour.Behaviour):
    """
    Retorna SUCCESS se a distância for menor ou igual a 'threshold'.
    Caso contrário, retorna FAILURE.
    """

    def __init__(self, game_state, threshold):
        super().__init__(name=f"CheckDist <= {threshold}")
        self.game_state = game_state
        self.threshold = threshold

    def update(self):
        if self.game_state.distance <= self.threshold:
            return Status.SUCCESS
        return Status.FAILURE


class Approach(py_trees.behaviour.Behaviour):
    """
    Aproxima os jogadores em 'step' unidades.
    """

    def __init__(self, game_state, step):
        super().__init__("Approach")
        self.game_state = game_state
        self.step = step

    def update(self):
        # Reduz a distância, mas não deixa ficar negativa
        self.game_state.distance = max(0, self.game_state.distance - self.step)
        print(f"Jogadores se aproximando (Distância: {self.game_state.distance})")
        return Status.SUCCESS


class Attack(py_trees.behaviour.Behaviour):
    """
    Ataque normal, causando 10 de dano ao alvo (A ou B).
    """

    def __init__(self, game_state, target):
        super().__init__(name=f"Ataque {target}")
        self.game_state = game_state
        self.target = target

    def update(self):
        damage = 10
        if self.target == 'A':
            self.game_state.player_a_hp -= damage
            remaining = self.game_state.player_a_hp
        else:
            self.game_state.player_b_hp -= damage
            remaining = self.game_state.player_b_hp

        print(f"Ataque normal em {self.target} (HP restante: {remaining})")
        return Status.SUCCESS


class CheckBerserk(py_trees.behaviour.Behaviour):
    """
    Verifica se o estado Berserk está ativo (para o jogador B).
    """

    def __init__(self, game_state):
        super().__init__("CheckBerserk")
        self.game_state = game_state

    def update(self):
        return Status.SUCCESS if self.game_state.state_berserk else Status.FAILURE


class BerserkAttackFuzzy(py_trees.behaviour.Behaviour):
    """
    Ataque Berserk do jogador B utilizando lógica fuzzy para definir o dano.
    O dano varia de acordo com o valor de 'anger' no game_state.
    """

    def __init__(self, game_state):
        super().__init__("BerserkAttackFuzzy B")
        self.game_state = game_state

    def update(self):
        # Usa o valor de raiva para calcular o dano fuzzy
        damage_sim.input['anger'] = self.game_state.anger
        damage_sim.compute()
        computed_damage = damage_sim.output['damage']
        self.game_state.player_b_hp -= computed_damage
        print(
            f"ATAQUE BERSERK Fuzzy em B! (Anger: {self.game_state.anger:.2f}, Dano: {computed_damage:.2f}, HP restante: {self.game_state.player_b_hp:.2f})")
        return Status.SUCCESS


##############################################################################
#                              MONTAGEM DA ÁRVORE                            #
##############################################################################
def create_tree(game_state):
    """
    Cria a árvore de comportamento:
      1) Se a distância for maior que 5, faz Approach (aproximação).
      2) Caso contrário (<= 5), faz ataque corpo a corpo em paralelo (A e B).
         - Jogador B faz um Selector: se berserk, ataca com BerserkAttackFuzzy; senão, Attack normal.
    """

    # Raiz: Selector
    root = py_trees.composites.Selector(name="Root", memory=False)

    # -----------------------------------------------------------------------
    # 1) SEQUÊNCIA DE APROXIMAÇÃO (caso a distância seja maior que 5)
    # -----------------------------------------------------------------------
    approach_seq = py_trees.composites.Sequence(name="ApproachSeq", memory=True)
    check_medium = CheckDistanceGreaterThan(game_state, threshold=5)
    approach = Approach(game_state, step=5)
    approach_seq.add_children([check_medium, approach])

    # -----------------------------------------------------------------------
    # 2) SEQUÊNCIA DE ATAQUE PRÓXIMO (<= 5)
    # -----------------------------------------------------------------------
    close_attack_seq = py_trees.composites.Sequence(name="CloseAttackSeq", memory=True)

    check_close = CheckDistanceLessOrEqual(game_state, threshold=5)

    # Ataque em paralelo: A ataca e B ataca simultaneamente
    parallel_attack = py_trees.composites.Parallel(
        name="ParallelAttack",
        policy=py_trees.common.ParallelPolicy.SuccessOnAll()
    )

    # Ataque normal do jogador A
    attack_a = Attack(game_state, 'A')

    # Para o jogador B, criamos um Selector:
    #   - Se Berserk estiver ativo -> BerserkAttackFuzzy (com lógica fuzzy)
    #   - Caso contrário -> Attack normal
    attack_b_selector = py_trees.composites.Selector(name="AttackBSelector", memory=True)
    berserk_seq = py_trees.composites.Sequence(name="BerserkSeq", memory=True)
    berserk_seq.add_children([
        CheckBerserk(game_state),
        BerserkAttackFuzzy(game_state)
    ])
    attack_b = Attack(game_state, 'B')
    attack_b_selector.add_children([berserk_seq, attack_b])

    # Adiciona ao Parallel
    parallel_attack.add_children([attack_a, attack_b_selector])

    close_attack_seq.add_children([check_close, parallel_attack])

    # -----------------------------------------------------------------------
    # Monta a árvore na raiz
    #   - Primeiro tenta ApproachSeq
    #   - Se falhar (ou seja, se a distância não for > 5), faz CloseAttackSeq
    # -----------------------------------------------------------------------
    root.add_children([approach_seq, close_attack_seq])

    return root
