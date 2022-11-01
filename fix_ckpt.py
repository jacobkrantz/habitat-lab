import os
from collections import OrderedDict

import torch


def fix_all_ckpts(ckpt_dir: str):
    ckpts = [os.path.join(ckpt_dir, c) for c in os.listdir(ckpt_dir)]
    ckpts = sorted(
        ckpts,
        key=lambda p: int(p.split("/")[-1].split(".")[-2])
        if isinstance(p.split("/")[-1].split(".")[-2], int)
        else 10000,
    )

    for special in [
        ".habitat-resume-state.pth",
        ".habitat-resume-stateeval.pth",
    ]:
        p = os.path.join(ckpt_dir, special)
        if os.path.exists(p):
            ckpts.append(p)

    # fix all that need it
    for ckpt in ckpts[::-1]:
        ckpt_dict = torch.load(ckpt)
        did_change = False

        if "config" in ckpt_dict:
            ckpt_dict["config"]["RL"]["POLICY"]["OBS_TRANSFORMS"][
                "RESIZE_SHORTEST_EDGE"
            ]["SEMANTIC_KEY"] = "semantic"
            did_change = True

        if "state_dict" in ckpt_dict:
            state_dict = ckpt_dict["state_dict"]
            state_dict_changed = False

            new_state_dict = OrderedDict()
            for k, v in state_dict.items():
                old_prefix = "actor_critic.net.iig_"
                new_prefix = "actor_critic.net.instance_imagegoal_"
                if k.startswith(old_prefix):
                    state_dict_changed = True
                    new_k = new_prefix + k[len(old_prefix) :]
                    new_state_dict[new_k] = v
                else:
                    new_state_dict[k] = v

            if state_dict_changed:
                did_change = True
                ckpt_dict["state_dict"] = new_state_dict

        if did_change:
            torch.save(ckpt_dict, ckpt)


fix_all_ckpts("experiments/full_train_1/checkpoints")
