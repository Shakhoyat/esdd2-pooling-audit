"""The two-head component model, ported from the project that produced the scores.

Ported verbatim in structure from `models/heads.py::ComponentHeads` and the
trainer in `r2_04b_two_head.py`; see the PROVENANCE section of the README for
the originating commits. Every hyper-parameter is read from configs/systems.yaml
rather than hard-coded, so a rerun cannot silently differ from the paper.

Component logits are produced for every clip. Masking is the LOSS's job, not the
head's, which is what makes the two arms differ in exactly one line.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class ComponentHeads(nn.Module):
    def __init__(self, in_dim: int, hidden: int = 256, embed: int = 128,
                 dropout: float = 0.1) -> None:
        super().__init__()

        def branch(out_dim: int) -> nn.Sequential:
            return nn.Sequential(
                nn.Linear(in_dim, hidden), nn.BatchNorm1d(hidden), nn.ReLU(),
                nn.Dropout(dropout), nn.Linear(hidden, out_dim))

        self.mixture_branch = branch(1)
        self.speech_trunk = nn.Sequential(
            nn.Linear(in_dim, embed), nn.BatchNorm1d(embed), nn.ReLU())
        self.env_trunk = nn.Sequential(
            nn.Linear(in_dim, embed), nn.BatchNorm1d(embed), nn.ReLU())
        self.speech_out = nn.Linear(embed, 1)
        self.env_out = nn.Linear(embed, 1)

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        z_s, z_e = self.speech_trunk(x), self.env_trunk(x)
        return {"logit_mixture": self.mixture_branch(x).squeeze(-1),
                "logit_speech": self.speech_out(z_s).squeeze(-1),
                "logit_env": self.env_out(z_e).squeeze(-1)}


SPEECH_POS, ENV_POS, MIXTURE = {0, 1, 3}, {0, 1, 2}, {1, 2, 3, 4}


def train_component_heads(x, y, arm: str, seed: int, cfg: dict, device: str = "cuda"):
    """Train one arm. `arm` selects the component loss mask and nothing else."""
    torch.manual_seed(seed)
    x = x.to(device)
    mean, std = x.mean(0, keepdim=True), x.std(0, keepdim=True).clamp_min(1e-6)
    x = (x - mean) / std
    yt = torch.as_tensor(y, device=device)

    t_sp = torch.isin(yt, torch.tensor(sorted(SPEECH_POS), device=device)).float()
    t_en = torch.isin(yt, torch.tensor(sorted(ENV_POS), device=device)).float()
    t_mx = torch.isin(yt, torch.tensor(sorted(MIXTURE), device=device)).float()

    rule = cfg["arms"][arm]["component_loss_mask"]
    mask = t_mx.clone() if rule == "is_mixture" else torch.ones_like(t_mx)

    def pos_weight(t, m):
        p = (t * m).sum().clamp_min(1)
        n = ((1 - t) * m).sum().clamp_min(1)
        return n / p

    pw_sp, pw_en = pos_weight(t_sp, mask), pos_weight(t_en, mask)
    pw_mx = pos_weight(t_mx, torch.ones_like(t_mx))

    net = ComponentHeads(x.shape[1], cfg["hidden"], cfg["embed"], cfg["dropout"]).to(device)
    opt = torch.optim.AdamW(net.parameters(), lr=cfg["lr"], weight_decay=cfg["weight_decay"])
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, cfg["steps"])
    g = torch.Generator().manual_seed(seed)
    net.train()
    for _ in range(cfg["steps"]):
        idx = torch.randint(0, len(x), (cfg["batch"],), generator=g).to(device)
        o, mk = net(x[idx]), mask[idx]
        ls = (F.binary_cross_entropy_with_logits(
            o["logit_speech"], t_sp[idx], pos_weight=pw_sp, reduction="none")
            * mk).sum() / mk.sum().clamp_min(1)
        le = (F.binary_cross_entropy_with_logits(
            o["logit_env"], t_en[idx], pos_weight=pw_en, reduction="none")
            * mk).sum() / mk.sum().clamp_min(1)
        lm = F.binary_cross_entropy_with_logits(
            o["logit_mixture"], t_mx[idx], pos_weight=pw_mx)
        opt.zero_grad(set_to_none=True)
        (ls + le + lm).backward()
        opt.step()
        sch.step()
    return net, (mean, std)


@torch.no_grad()
def score_component_heads(net, norm, x, device: str = "cuda"):
    """Bona-fide-oriented [speech, env] probabilities, the schema scores/ uses."""
    mean, std = norm
    net.eval()
    out = []
    for i in range(0, len(x), 8192):
        o = net(((x[i:i + 8192].to(device)) - mean) / std)
        out.append(torch.stack([torch.sigmoid(o["logit_speech"]),
                                torch.sigmoid(o["logit_env"])], 1).cpu())
    return torch.cat(out).numpy()


def train_linear_probe(x_tr, y_tr, x_ev, seed: int, cfg: dict, device: str = "cuda"):
    """The five-class linear probe behind Table 1's rows."""
    torch.manual_seed(seed)
    x_tr, x_ev = x_tr.to(device), x_ev.to(device)
    yt = torch.as_tensor(y_tr, device=device).long()
    mean, std = x_tr.mean(0, keepdim=True), x_tr.std(0, keepdim=True).clamp_min(1e-6)
    x_tr, x_ev = (x_tr - mean) / std, (x_ev - mean) / std

    head = nn.Linear(x_tr.shape[1], 5).to(device)
    opt = torch.optim.AdamW(head.parameters(), lr=cfg["lr"], weight_decay=cfg["weight_decay"])
    g = torch.Generator().manual_seed(seed)
    head.train()
    for _ in range(cfg["steps"]):
        idx = torch.randint(0, len(x_tr), (min(cfg["batch"], len(x_tr)),),
                            generator=g).to(device)
        loss = F.cross_entropy(head(x_tr[idx]), yt[idx])
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    head.eval()
    with torch.no_grad():
        probs = torch.softmax(head(x_ev), -1).cpu().numpy()
    return probs
