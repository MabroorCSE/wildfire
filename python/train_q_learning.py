#!/usr/bin/env python3
import csv
import os
import random
import sys
import time
from collections import deque

from tensorboardX import SummaryWriter

import wildfire_env

CONFIG_PATH = "config/train_medium_wind_small.json"
SAMPLE_PERIOD = 1800.0
EPISODES = 100
STEPS_PER_EPISODE = 40
LEARNING_RATE = 0.3
DISCOUNT_FACTOR = 0.9
EPSILON_START = 1.0
EPSILON_END = 0.05
EPSILON_DECAY_EPISODES = 40
PERCENT_BUCKET_SIZE = 5.0
EXTINGUISH_BONUS = 2.0
CELLS_PER_DECISION = 1
ROLLING_AVERAGE_WINDOW = 10

ACTION_NONE = 0
ACTION_EXTINGUISH = 1
ACTIONS = [ACTION_NONE, ACTION_EXTINGUISH]
ACTION_NAMES = {ACTION_NONE: "none", ACTION_EXTINGUISH: "extinguish"}

RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"

RUN_ID = time.strftime("%Y%m%d-%H%M%S")
TENSORBOARD_DIR = f"runs/{RUN_ID}"
EXTINGUISH_LOG_PATH = f"logs/{RUN_ID}_extinguish_log.csv"


def colored(value: float, fmt: str = ".1f") -> str:
    color = GREEN if value >= 0 else RED
    return f"{color}{value:{fmt}}{RESET}"


def epsilon_for_episode(episode: int) -> float:
    progress = min(episode / EPSILON_DECAY_EPISODES, 1.0)
    return EPSILON_START + (EPSILON_END - EPSILON_START) * progress


def percent_to_bucket(percent_ignited: float) -> int:
    return min(int(percent_ignited // PERCENT_BUCKET_SIZE), 19)


def bucket_label(bucket: int) -> str:
    low = bucket * PERCENT_BUCKET_SIZE
    high = low + PERCENT_BUCKET_SIZE
    return f"{low:.0f}-{high:.0f}%"


def choose_action(q_table: dict, bucket: int, epsilon: float) -> int:
    if random.random() < epsilon:
        return random.choice(ACTIONS)
    return max(ACTIONS, key=lambda action: q_table.get((bucket, action), 0.0))


def run_episode(env: wildfire_env.WildfireEnvironment, q_table: dict, epsilon: float, episode: int, extinguish_log: csv.writer) -> tuple[float, float]:
    percent_ignited = env.reset()
    bucket = percent_to_bucket(percent_ignited)
    total_reward = 0.0
    total_training_reward = 0.0

    for step in range(STEPS_PER_EPISODE):
        action = choose_action(q_table, bucket, epsilon)

        target_cell_ids = []
        if action == ACTION_EXTINGUISH:
            target_cell_ids = env.top_dangerous_cells()

        percent_ignited, reward = env.step(target_cell_ids)
        next_bucket = percent_to_bucket(percent_ignited)

        training_reward = reward + EXTINGUISH_BONUS * len(target_cell_ids)

        best_next_value = max(q_table.get((next_bucket, next_action), 0.0) for next_action in ACTIONS)
        current_value = q_table.get((bucket, action), 0.0)
        q_table[(bucket, action)] = current_value + LEARNING_RATE * (training_reward + DISCOUNT_FACTOR * best_next_value - current_value)

        extinguish_log.writerow([episode, step, f"{percent_ignited:.4f}", ACTION_NAMES[action], ";".join(target_cell_ids), reward, training_reward])

        bucket = next_bucket
        total_reward += reward
        total_training_reward += training_reward

    return total_reward, total_training_reward


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else CONFIG_PATH
    env = wildfire_env.WildfireEnvironment(config_path, SAMPLE_PERIOD, CELLS_PER_DECISION)
    q_table = {}

    os.makedirs("logs", exist_ok=True)
    tensorboard_writer = SummaryWriter(TENSORBOARD_DIR)
    recent_rewards = deque(maxlen=ROLLING_AVERAGE_WINDOW)

    with open(EXTINGUISH_LOG_PATH, "w", newline="") as log_file:
        extinguish_log = csv.writer(log_file)
        extinguish_log.writerow(["episode", "step", "percent_ignited", "action", "target_cell_ids", "reward", "training_reward"])

        for episode in range(EPISODES):
            epsilon = epsilon_for_episode(episode)
            total_reward, total_training_reward = run_episode(env, q_table, epsilon, episode, extinguish_log)
            print(f"episode {episode}: epsilon={epsilon:.2f} reward={colored(total_reward)} training_reward={colored(total_training_reward)}")

            recent_rewards.append(total_reward)
            rolling_average_reward = sum(recent_rewards) / len(recent_rewards)

            tensorboard_writer.add_scalar("episode/reward", total_reward, episode)
            tensorboard_writer.add_scalar("episode/reward_rolling_average", rolling_average_reward, episode)
            tensorboard_writer.add_scalar("episode/training_reward", total_training_reward, episode)
            tensorboard_writer.add_scalar("episode/discover", epsilon, episode)
            for bucket in sorted({bucket for bucket, _action in q_table}):
                tensorboard_writer.add_scalar(f"q_none/{bucket_label(bucket)}", q_table.get((bucket, ACTION_NONE), 0.0), episode)
                tensorboard_writer.add_scalar(f"q_extinguish/{bucket_label(bucket)}", q_table.get((bucket, ACTION_EXTINGUISH), 0.0), episode)

    env.close()
    tensorboard_writer.close()

    print("\nlearned Q-table (% of grid on fire: Q[none], Q[extinguish]):")
    for bucket in sorted({bucket for bucket, _action in q_table}):
        none_value = colored(q_table.get((bucket, ACTION_NONE), 0.0), '.2f')
        extinguish_value = colored(q_table.get((bucket, ACTION_EXTINGUISH), 0.0), '.2f')
        print(f"  {bucket_label(bucket)}: {none_value}, {extinguish_value}")

    print(f"\nTensorBoard logs: {TENSORBOARD_DIR}")
    print(f"Extinguish log: {EXTINGUISH_LOG_PATH}")


if __name__ == "__main__":
    main()
