#!/usr/bin/env python3
import random
import sys

import wildfire_env

CONFIG_PATH = "config/map_1.json"
SAMPLE_PERIOD = 1800.0  # 30 min between decisions
EPISODES = 100
STEPS_PER_EPISODE = 40  # 40 x 30min = 20h simulated, same total episode length as before
ALPHA = 0.3
GAMMA = 0.9
EPSILON_START = 1.0
EPSILON_END = 0.05
EPSILON_DECAY_EPISODES = 40  # linearly reaches EPSILON_END by this episode, then stays flat
PERCENT_BUCKET_SIZE = 5.0  # % ignited per state bucket
EXTINGUISH_BONUS = 2.0  # shaped reward for successfully putting out a cell that was burning
CELLS_PER_DECISION = 1

ACTION_NONE = 0
ACTION_EXTINGUISH = 1
ACTIONS = [ACTION_NONE, ACTION_EXTINGUISH]

RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"


def colored(value: float, fmt: str = ".1f") -> str:
    color = GREEN if value >= 0 else RED
    return f"{color}{value:{fmt}}{RESET}"


def epsilon_for_episode(episode: int) -> float:
    progress = min(episode / EPSILON_DECAY_EPISODES, 1.0)
    return EPSILON_START + (EPSILON_END - EPSILON_START) * progress


def state_bucket(percent_ignited: float) -> int:
    return min(int(percent_ignited // PERCENT_BUCKET_SIZE), 19)


def bucket_label(s: int) -> str:
    low = s * PERCENT_BUCKET_SIZE
    high = low + PERCENT_BUCKET_SIZE
    return f"{low:.0f}-{high:.0f}%"


def choose_action(q_table: dict, s: int, epsilon: float) -> int:
    if random.random() < epsilon:
        return random.choice(ACTIONS)
    return max(ACTIONS, key=lambda a: q_table.get((s, a), 0.0))


def run_episode(env: wildfire_env.WildfireEnvironment, q_table: dict, epsilon: float) -> tuple[float, float]:
    percent = env.reset()
    s = state_bucket(percent)
    total_env_reward = 0.0
    total_shaped_reward = 0.0

    for _ in range(STEPS_PER_EPISODE):
        a = choose_action(q_table, s, epsilon)

        target_cell_ids = []
        if a == ACTION_EXTINGUISH:
            target_cell_ids = env.top_dangerous_cells()

        percent, env_reward = env.step(target_cell_ids)
        s_next = state_bucket(percent)

        # env_reward alone rarely differs between actions (see WhatsApp discussion), so the
        # Q-update uses a shaped reward that also credits each successful extinguish immediately.
        shaped_reward = env_reward + EXTINGUISH_BONUS * len(target_cell_ids)

        best_next = max(q_table.get((s_next, a2), 0.0) for a2 in ACTIONS)
        q_table[(s, a)] = q_table.get((s, a), 0.0) + ALPHA * (shaped_reward + GAMMA * best_next - q_table.get((s, a), 0.0))

        s = s_next
        total_env_reward += env_reward
        total_shaped_reward += shaped_reward

    return total_env_reward, total_shaped_reward


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else CONFIG_PATH
    env = wildfire_env.WildfireEnvironment(config_path, SAMPLE_PERIOD, CELLS_PER_DECISION)
    q_table = {}

    for episode in range(EPISODES):
        epsilon = epsilon_for_episode(episode)
        env_reward, shaped_reward = run_episode(env, q_table, epsilon)
        print(f"episode {episode}: epsilon={epsilon:.2f} env_reward={colored(env_reward)} shaped_reward={colored(shaped_reward)}")

    env.close()

    print("\nlearned Q-table (% of grid on fire: Q[none], Q[extinguish]):")
    for s in sorted({s for s, _a in q_table}):
        print(f"  {bucket_label(s)}: {colored(q_table.get((s, ACTION_NONE), 0.0), '.2f')}, {colored(q_table.get((s, ACTION_EXTINGUISH), 0.0), '.2f')}")


if __name__ == "__main__":
    main()
