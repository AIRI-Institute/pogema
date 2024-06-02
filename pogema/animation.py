import os
import typing
from itertools import cycle
from gymnasium import logger, Wrapper

from pogema import GridConfig, pogema_v0, BatchAStarAgent
from pogema.animation_drawer import AnimationConfig, AnimationSettings, GridHolder, AnimationDrawer
from pogema.wrappers.persistence import PersistentWrapper, AgentState


class AnimationMonitor(Wrapper):
    """
    Defines the animation, which saves the episode as SVG.
    """

    def __init__(self, env, animation_config=AnimationConfig()):
        self._working_radius = env.grid_config.obs_radius - 1
        env = PersistentWrapper(env, xy_offset=-self._working_radius)

        super().__init__(env)

        self.history = env.get_history()

        self.svg_settings: AnimationSettings = AnimationSettings()
        self.animation_config: AnimationConfig = animation_config

        self._episode_idx = 0

    def step(self, action):
        """
        Saves information about the episode.
        :param action: current actions
        :return: obs, reward, done, info
        """
        obs, reward, terminated, truncated, info = self.env.step(action)

        multi_agent_terminated = isinstance(terminated, (list, tuple)) and all(terminated)
        single_agent_terminated = isinstance(terminated, (bool, int)) and terminated
        multi_agent_truncated = isinstance(truncated, (list, tuple)) and all(truncated)
        single_agent_truncated = isinstance(truncated, (bool, int)) and truncated

        if multi_agent_terminated or single_agent_terminated or multi_agent_truncated or single_agent_truncated:
            save_tau = self.animation_config.save_every_idx_episode
            if save_tau:
                if (self._episode_idx + 1) % save_tau or save_tau == 1:
                    if not os.path.exists(self.animation_config.directory):
                        logger.info(f"Creating pogema monitor directory {self.animation_config.directory}", )
                        os.makedirs(self.animation_config.directory, exist_ok=True)

                    path = os.path.join(self.animation_config.directory,
                                        self.pick_name(self.grid_config, self._episode_idx))
                    self.save_animation(path)

        return obs, reward, terminated, truncated, info

    @staticmethod
    def pick_name(grid_config: GridConfig, episode_idx=None, zfill_ep=5):
        """
        Picks a name for the SVG file.
        :param grid_config: configuration of the grid
        :param episode_idx: idx of the episode
        :param zfill_ep: zfill for the episode number
        :return:
        """
        gc = grid_config
        name = 'pogema'
        if episode_idx is not None:
            name += f'-ep{str(episode_idx).zfill(zfill_ep)}'
        if gc:
            if gc.map_name:
                name += f'-{gc.map_name}'
            if gc.seed is not None:
                name += f'-seed{gc.seed}'
        else:
            name += '-render'
        return name + '.svg'

    def reset(self, **kwargs):
        """
        Resets the environment and resets the current positions of agents and targets
        :param kwargs:
        :return: obs: observation
        """
        obs = self.env.reset(**kwargs)

        self._episode_idx += 1
        self.history = self.env.get_history()

        return obs

    def save_animation(self, name='render.svg', animation_config: typing.Optional[AnimationConfig] = AnimationConfig()):
        """
        Saves the animation.
        :param name: name of the file
        :param animation_config: animation configuration
        :return: None
        """
        # animation = self.create_animation(animation_config)
        wr = self._working_radius
        obstacles = self.env.get_obstacles(ignore_borders=False)[wr:-wr, wr:-wr]
        history: list[list[AgentState]] = self.env.decompress_history(self.history)

        episode_length = len(history[0])
        svg_settings = AnimationSettings()
        colors_cycle = cycle(svg_settings.colors)
        agents_colors = {index: next(colors_cycle) for index in range(self.grid_config.num_agents)}
        grid_holder = GridHolder(
            width=len(obstacles), height=len(obstacles[0]),
            obstacles=obstacles,
            episode_length=episode_length,
            history=history,
            obs_radius=self.grid_config.obs_radius,
            colors=agents_colors,
            on_target=self.grid_config.on_target,
        )

        animation = AnimationDrawer().create_animation(grid_holder, animation_config=animation_config)
        with open(name, "w") as f:
            f.write(animation.render())


def main():
    grid = """
    ...#.
    .#...
    .....
    .....
    ##.#.
    ##.#.
    """
    grid_config = GridConfig(size=32, num_agents=2, obs_radius=2, seed=11, on_target='finish', max_episode_steps=16,
                             density=0.1, map=grid, observation_type="POMAPF")
    env = pogema_v0(grid_config=grid_config)
    env = AnimationMonitor(env)

    obs, _ = env.reset()
    truncated = terminated = [False]

    agent = BatchAStarAgent()
    while not all(terminated) and not all(truncated):
        obs, _, terminated, truncated, _ = env.step(agent.act(obs))

    env.save_animation('out-static.svg', AnimationConfig(static=True, save_every_idx_episode=None))
    env.save_animation('out-static-ego.svg', AnimationConfig(egocentric_idx=0, static=True))
    env.save_animation('out-static-no-agents.svg', AnimationConfig(show_agents=False, static=True))
    env.save_animation("out.svg")
    env.save_animation("out-ego.svg", AnimationConfig(egocentric_idx=0))


if __name__ == '__main__':
    main()
