# """
# model.py — DeepfakeEfficientNet architecture
# Matches exactly the model saved in best_model_v3.pth
# """

# import torch
# import torch.nn as nn
# import torch.nn.functional as F
# import timm


# class DeepfakeEfficientNet(nn.Module):
#     """
#     EfficientNet-B4 backbone with a custom 2-layer classifier head.
#     Input : (B, 3, 380, 380)  — ImageNet-normalised float32
#     Output: (B,)              — raw logit (apply sigmoid for probability)
#     """

#     def __init__(self, cfg: dict):
#         super().__init__()
#         self.backbone = timm.create_model(
#             cfg["model_name"],
#             pretrained=cfg.get("pretrained", False),
#             num_classes=0,       # remove timm's built-in head
#             global_pool="avg",
#         )
#         feat = self.backbone.num_features  # 1792 for EfficientNet-B4

#         self.classifier = nn.Sequential(
#             nn.Dropout(cfg["dropout1"]),
#             nn.Linear(feat, cfg["hidden_units"]),
#             nn.GELU(),
#             nn.BatchNorm1d(cfg["hidden_units"]),
#             nn.Dropout(cfg["dropout2"]),
#             nn.Linear(cfg["hidden_units"], 1),
#         )

#         # Xavier init (same as training notebook)
#         for m in self.classifier.modules():
#             if isinstance(m, nn.Linear):
#                 nn.init.xavier_uniform_(m.weight)
#                 nn.init.zeros_(m.bias)

#     def forward(self, x: torch.Tensor) -> torch.Tensor:
#         return self.classifier(self.backbone(x)).squeeze(1)

#     def freeze_backbone(self):
#         for p in self.backbone.parameters():
#             p.requires_grad = False

#     def unfreeze_backbone(self):
#         for p in self.backbone.parameters():
#             p.requires_grad = True


# # ── Default model config (matches training notebook exactly) ──────────────────
# DEFAULT_MODEL_CONFIG = {
#     "model_name"   : "efficientnet_b4",
#     "pretrained"   : False,   # weights come from the checkpoint, not ImageNet
#     "dropout1"     : 0.4,
#     "dropout2"     : 0.2,
#     "hidden_units" : 512,
#     "image_size"   : 380,
#     "mean"         : [0.485, 0.456, 0.406],
#     "std"          : [0.229, 0.224, 0.225],
#     "use_amp"      : True,
# }


# def load_model(checkpoint_path: str, device: torch.device) -> tuple[nn.Module, float]:
#     """
#     Build the model, load state dict from checkpoint, return (model, optimal_threshold).
#     The checkpoint must contain:
#         - 'model_state'        : state_dict
#         - 'optimal_threshold'  : float  (optional, default 0.46)
#     """
#     model = DeepfakeEfficientNet(DEFAULT_MODEL_CONFIG).to(device)

#     ckpt = torch.load(checkpoint_path, map_location=device)
#     model.load_state_dict(ckpt["model_state"])
#     model.eval()

#     threshold = float(ckpt.get("optimal_threshold", 0.46))
#     return model, threshold



import torch
import torch.nn as nn
import timm


#  MODEL 
class DeepfakeEfficientNet(nn.Module):
    """
    EfficientNet-B4 backbone with custom classifier
    Input : (B, 3, 380, 380)
    Output: (B,) raw logits
    """

    def __init__(self, cfg: dict):
        super().__init__()

        self.backbone = timm.create_model(
            cfg["model_name"],
            pretrained=cfg.get("pretrained", False),
            num_classes=0,
            global_pool="avg",
        )

        feat = self.backbone.num_features  # 1792

        self.classifier = nn.Sequential(
            nn.Dropout(cfg["dropout1"]),
            nn.Linear(feat, cfg["hidden_units"]),
            nn.GELU(),
            nn.BatchNorm1d(cfg["hidden_units"]),
            nn.Dropout(cfg["dropout2"]),
            nn.Linear(cfg["hidden_units"], 1),
        )

        # Xavier init (same as training)
        for m in self.classifier.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.backbone(x)).squeeze(1)

    def freeze_backbone(self):
        for p in self.backbone.parameters():
            p.requires_grad = False

    def unfreeze_backbone(self):
        for p in self.backbone.parameters():
            p.requires_grad = True


#  CONFIG 
DEFAULT_MODEL_CONFIG = {
    "model_name": "efficientnet_b4",
    "pretrained": False,
    "dropout1": 0.4,
    "dropout2": 0.2,
    "hidden_units": 512,
    "image_size": 380,
    "mean": [0.485, 0.456, 0.406],
    "std": [0.229, 0.224, 0.225],
    "use_amp": True,
}


#  LOADER 
def load_model(checkpoint_path: str, device: torch.device):
    """
    Loads model safely from different checkpoint formats

    Supports:
    - {"model_state": ...}
    - {"model_state_dict": ...}
    - raw state_dict
    """

    print(f"🔄 Loading model from: {checkpoint_path}")

    model = DeepfakeEfficientNet(DEFAULT_MODEL_CONFIG).to(device)

    checkpoint = torch.load(checkpoint_path, map_location=device)

    #  HANDLE MULTIPLE FORMATS 
    if isinstance(checkpoint, dict):

        if "model_state" in checkpoint:
            state_dict = checkpoint["model_state"]

        elif "model_state_dict" in checkpoint:
            state_dict = checkpoint["model_state_dict"]

        else:
            state_dict = checkpoint

    else:
        state_dict = checkpoint

    #  FIX PREFIX ISSUE 
    new_state_dict = {}
    for k, v in state_dict.items():
        if not k.startswith("backbone") and "classifier" not in k:
            k = "backbone." + k
        new_state_dict[k] = v

    #  LOAD 
    try:
        model.load_state_dict(new_state_dict)
        print("✅ Model loaded successfully")

    except RuntimeError as e:
        print("⚠️ Strict load failed — retrying with strict=False")
        model.load_state_dict(new_state_dict, strict=False)

    model.eval()

    threshold = float(
        checkpoint.get("optimal_threshold", 0.46)
        if isinstance(checkpoint, dict)
        else 0.46
    )

    print(f"🎯 Threshold: {threshold}")

    return model, threshold