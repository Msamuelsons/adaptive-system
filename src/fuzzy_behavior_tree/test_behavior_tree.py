##############################################################################
#                         TESTE                                              #
##############################################################################

import py_trees
from fuzzy_behavior_tree import GameState
from fuzzy_behavior_tree import create_tree

if __name__ == "__main__":
    game_state = GameState()

    # Exemplo: ao iniciar a luta, podemos incrementar a raiva do avatar B
    game_state.state_berserk = True
    game_state.anger = 3  # valor baixo de raiva

    tree = create_tree(game_state)
    behaviour_tree = py_trees.trees.BehaviourTree(root=tree)

    # Simula alguns ciclos de execução da árvore de comportamento
    for tick in range(10):
        print(f"\n--- Tick {tick + 1} ---")
        behaviour_tree.tick()
        # Exemplo: a raiva aumenta a cada tick
        game_state.anger = min(10, game_state.anger + 2)
