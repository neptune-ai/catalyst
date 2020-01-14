from typing import Any, Dict, Mapping, List

import numpy as np

import torch

from catalyst.core import Runner
from catalyst.rl import utils, EnvironmentSpec
from .experiment import RLExperiment
from .state import RLRunnerState

# RLRunner has only one stage - endless training
# each Epoch we recalculate training loader based on current Replay buffer
# then -> typical training on loader with selected algorithm
#


class RLRunner(Runner):
    experiment: RLExperiment
    state: RLRunnerState

    def _fetch_rollouts(self):
        pass

    def _prepare_for_epoch(self, stage: str, epoch: int):
        super()._prepare_for_epoch(stage=stage, epoch=epoch)

        # @TODO: remove this trick
        utils.set_global_seed(self.experiment.initial_seed + epoch)
        loaders = self.experiment.get_loaders(stage=stage, epoch=epoch)
        self.loaders = loaders

    def forward(self, batch: Mapping[str, Any], **kwargs) -> Mapping[str, Any]:
        # should implement different training steps for different algorithms
        metrics: Dict = self.algorithm.train_on_batch(
            batch,
            actor_update=(self.state.step % self.state.actor_grad_period == 0),
            critic_update=(self.state.step % self.state.critic_grad_period == 0),
        ) or {}

        metrics_ = self._update_target_weights(self.state.step) or {}
        metrics.update(**metrics_)
        self.state.metric_manager.add_batch_value(metrics_dict=metrics)

    def forward_infer(
        self,
        batch: Mapping[str, Any],
        **kwargs
    ) -> Mapping[str, Any]:
        pass

    def predict_batch(
        self,
        batch: Mapping[str, Any],
        **kwargs
    ) -> Mapping[str, Any]:
        batch = self._batch2device(batch, self.device)
        output = self.forward_infer(batch, **kwargs)
        return output

    @torch.no_grad()
    def inference(
        self,
        sampler_ids: List[int],
        run_ids: List[int],
        states: np.ndarray,
        rewards: np.ndarray,
    ):
        # looks like production-ready thing
        # @TODO: make a microservice from this method
        batch = None
        actions = self.predict_batch(batch)
        return actions

    def run(self):
        pass

    @classmethod
    def get_from_params(
        cls,
        algorithm_params: Dict,
        env_spec: EnvironmentSpec,
    ):
        pass