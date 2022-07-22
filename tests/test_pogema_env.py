import re

import numpy as np

from pogema import pogema_v0
from pogema import Easy8x8, Normal8x8, Hard8x8, ExtraHard8x8
from pogema import Easy16x16, Normal16x16, Hard16x16, ExtraHard16x16
from pogema import Easy32x32, Normal32x32, Hard32x32, ExtraHard32x32
from pogema import Easy64x64, Normal64x64, Hard64x64, ExtraHard64x64

from pogema.animation import AnimationMonitor
from pogema.grid import GridConfig


class ActionMapping:
    noop: int = 0
    up: int = 1
    down: int = 2
    left: int = 3
    right: int = 4


def test_moving():
    env = pogema_v0(GridConfig(num_agents=2, size=6, obs_radius=2, density=0.3, seed=42))
    ac = ActionMapping()
    env.reset()

    env.step([ac.right, ac.noop])
    env.step([ac.up, ac.noop])
    env.step([ac.left, ac.noop])
    env.step([ac.down, ac.noop])
    env.step([ac.down, ac.noop])
    env.step([ac.left, ac.noop])
    env.step([ac.left, ac.noop])
    env.step([ac.up, ac.noop])
    env.step([ac.up, ac.noop])
    env.step([ac.up, ac.noop])

    env.step([ac.right, ac.noop])
    env.step([ac.up, ac.noop])
    env.step([ac.right, ac.noop])
    env.step([ac.down, ac.noop])
    obs, reward, done, infos = env.step([ac.right, ac.noop])

    assert np.isclose([1.0, 0.0], reward).all()
    assert np.isclose([True, False], done).all()


def test_types():
    env = pogema_v0(GridConfig(num_agents=2, size=6, obs_radius=2, density=0.3, seed=42))
    obs = env.reset()
    assert obs[0].dtype == np.float32


def run_episode(grid_config=None, env=None):
    if env is None:
        env = pogema_v0(grid_config)
    env.reset()

    obs, rewards, dones, infos = env.reset(), [None], [False], [None]

    results = [[obs, rewards, dones, infos]]
    while not all(dones):
        results.append(env.step(env.sample_actions()))
        dones = results[-1][-2]
    return results


def test_metrics():
    _, _, _, infos = run_episode(GridConfig(num_agents=2, seed=5, size=5, max_episode_steps=64))[-1]
    assert np.isclose(infos[0]['metrics']['CSR'], 0.0)
    assert np.isclose(infos[0]['metrics']['ISR'], 0.0)
    assert np.isclose(infos[1]['metrics']['ISR'], 1.0)

    _, _, _, infos = run_episode(GridConfig(num_agents=2, seed=5, size=5, max_episode_steps=512))[-1]
    assert np.isclose(infos[0]['metrics']['CSR'], 1.0)
    assert np.isclose(infos[0]['metrics']['ISR'], 1.0)
    assert np.isclose(infos[1]['metrics']['ISR'], 1.0)

    _, _, _, infos = run_episode(GridConfig(num_agents=5, seed=5, size=5, max_episode_steps=64))[-1]
    assert np.isclose(infos[0]['metrics']['CSR'], 0.0)
    assert np.isclose(infos[0]['metrics']['ISR'], 0.0)
    assert np.isclose(infos[1]['metrics']['ISR'], 0.0)
    assert np.isclose(infos[2]['metrics']['ISR'], 0.0)
    assert np.isclose(infos[3]['metrics']['ISR'], 1.0)
    assert np.isclose(infos[4]['metrics']['ISR'], 0.0)


def test_standard_pogema():
    env = pogema_v0(GridConfig(num_agents=2, size=6, obs_radius=2, density=0.3, seed=42, on_target='finish'))
    env.reset()


def test_standard_pogema_animation():
    env = pogema_v0(GridConfig(num_agents=2, size=6, obs_radius=2, density=0.3, seed=42, on_target='finish'))
    env = AnimationMonitor(env)
    env.reset()


def test_non_disappearing_pogema():
    env = pogema_v0(GridConfig(num_agents=2, size=6, obs_radius=2, density=0.3, seed=42, on_target='nothing'))
    env.reset()


def test_non_disappearing_pogema_animation():
    env = pogema_v0(GridConfig(num_agents=2, size=6, obs_radius=2, density=0.3, seed=42, on_target='nothing'))
    env = AnimationMonitor(env)
    env.reset()


def test_life_long_pogema():
    env = pogema_v0(GridConfig(num_agents=2, size=6, obs_radius=2, density=0.3, seed=42, on_target='restart'))
    env.reset()


def test_life_long_pogema_animation():
    env = pogema_v0(GridConfig(num_agents=2, size=6, obs_radius=2, density=0.3, seed=42, on_target='restart'))
    env = AnimationMonitor(env)
    env.reset()
    run_episode(env=env)


def test_predefined_configurations():
    def get_num_agents_by_target_density(size, agent_density, obstacle_density):
        return round(agent_density * (size * size * (1.0 - obstacle_density)))

    def get_target_density_by_num_agents(size, num_agents, obstacle_density):
        return num_agents / (size * size * (1.0 - obstacle_density))

    predefined_grids = [
        Easy8x8, Normal8x8, Hard8x8, ExtraHard8x8,
        Easy16x16, Normal16x16, Hard16x16, ExtraHard16x16,
        Easy32x32, Normal32x32, Hard32x32, ExtraHard32x32,
        Easy64x64, Normal64x64, Hard64x64, ExtraHard64x64,
    ]

    # checking that the number of agents (agent density) is correct
    for make_grid_config_func in predefined_grids:
        gc = make_grid_config_func(seed=42)
        for difficulty, agent_density in zip(['Easy', 'Normal', 'Hard', 'ExtraHard'],
                                             [0.02232142, 0.04464285, 0.08928571, 0.17857142]):
            if re.match(f'^{difficulty}\d+x\d+', make_grid_config_func.__name__):
                assert np.isclose(get_target_density_by_num_agents(gc.size, gc.num_agents, gc.density), agent_density)

    for make_grid_config_func in predefined_grids:
        gc = make_grid_config_func(seed=42)
        env = pogema_v0(gc)
        env.reset()
