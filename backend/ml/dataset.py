"""
Dataset and DataLoader implementation for NIH ChestX-ray14 (10-Class Subset).
Reads ground truth labels from the dataset metadata CSV.
Implements strict patient-level disjoint train/val/test splitting to prevent data leakage.
"""

from __future__ import annotations
import os
import io
import json
import logging
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
from PIL import Image

try:
    import torch
    from torch.utils.data import Dataset
    from torchvision import transforms
except ImportError:
    torch = None
    Dataset = object
    transforms = None

logger = logging.getLogger("backend.ml.dataset")


def load_label_config(config_path: str | Path | None = None) -> list[dict]:
    """Load the canonical 10-class disease label mapping from disease_labels.json."""
    if config_path is None:
        config_path = Path(__file__).resolve().parent / "disease_labels.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_default_transforms(input_size: int = 224, is_training: bool = False):
    """
    Construct canonical torchvision transforms matching preprocessing_config.json.
    - Resizes to (input_size, input_size).
    - Converts single-channel/RGB to 3-channel float tensor in [0.0, 1.0].
    - Normalizes with standard ImageNet statistics.
    """
    if transforms is None:
        return None

    # Normalization parameters from preprocessing_config.json
    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]

    if is_training:
        return transforms.Compose([
            transforms.Resize((input_size, input_size)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=7),
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std),
        ])
    else:
        return transforms.Compose([
            transforms.Resize((input_size, input_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std),
        ])


def create_patient_splits(
    df: pd.DataFrame,
    patient_col: str | None = None,
    train_ratio: float = 0.70,
    val_ratio: float = 0.10,
    test_ratio: float = 0.20,
    random_seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split the dataset into patient-level disjoint Train, Validation, and Test partitions.
    Guarantees that images belonging to the same patient never leak across splits.
    """
    # Detect patient ID column if not explicitly provided
    if patient_col is None:
        candidate_cols = ["Patient ID", "patient_id", "PatientID", "Patient_ID", "Patient"]
        for col in candidate_cols:
            if col in df.columns:
                patient_col = col
                break

    if patient_col and patient_col in df.columns:
        logger.info("Using patient-level disjoint splitting on column '%s'", patient_col)
        unique_patients = df[patient_col].unique()
        rng = np.random.RandomState(random_seed)
        shuffled_patients = rng.permutation(unique_patients)

        n_total = len(shuffled_patients)
        n_train = int(n_total * train_ratio)
        n_val = int(n_total * val_ratio)

        train_patients = set(shuffled_patients[:n_train])
        val_patients = set(shuffled_patients[n_train : n_train + n_val])
        test_patients = set(shuffled_patients[n_train + n_val :])

        # Assert zero overlap between patient sets
        assert len(train_patients & val_patients) == 0, "Train-Val patient leakage detected!"
        assert len(train_patients & test_patients) == 0, "Train-Test patient leakage detected!"
        assert len(val_patients & test_patients) == 0, "Val-Test patient leakage detected!"

        train_df = df[df[patient_col].isin(train_patients)].copy().reset_index(drop=True)
        val_df = df[df[patient_col].isin(val_patients)].copy().reset_index(drop=True)
        test_df = df[df[patient_col].isin(test_patients)].copy().reset_index(drop=True)

        logger.info(
            "Splits created: Train=%d patients (%d images), Val=%d patients (%d images), Test=%d patients (%d images)",
            len(train_patients), len(train_df),
            len(val_patients), len(val_df),
            len(test_patients), len(test_df),
        )
        return train_df, val_df, test_df
    else:
        logger.warning(
            "No patient ID column found in CSV. Falling back to row-level random shuffle."
        )
        df_shuffled = df.sample(frac=1.0, random_state=random_seed).reset_index(drop=True)
        n_total = len(df_shuffled)
        n_train = int(n_total * train_ratio)
        n_val = int(n_total * val_ratio)

        train_df = df_shuffled.iloc[:n_train].reset_index(drop=True)
        val_df = df_shuffled.iloc[n_train : n_train + n_val].reset_index(drop=True)
        test_df = df_shuffled.iloc[n_train + n_val :].reset_index(drop=True)
        return train_df, val_df, test_df


class ChestXRayDataset(Dataset):
    """
    PyTorch Dataset for multi-label chest X-ray classification.
    Reads ground truth pathology labels from the dataset CSV.
    """

    def __init__(
        self,
        dataframe: pd.DataFrame,
        images_dir: str | Path,
        label_config: list[dict] | None = None,
        transform: Callable | None = None,
        image_col: str | None = None,
        label_col: str | None = None,
    ) -> None:
        self.df = dataframe.copy().reset_index(drop=True)
        self.images_dir = Path(images_dir)
        self.transform = transform

        if label_config is None:
            self.label_config = load_label_config()
        else:
            self.label_config = label_config

        self.num_classes = len(self.label_config)
        self.class_names = [c["name"] for c in self.label_config]
        self.nih_labels = [c.get("nih_label", c["name"]) for c in self.label_config]

        # Auto-detect image column
        if image_col is None:
            for col in ["Image Index", "image_index", "filename", "Image", "image"]:
                if col in self.df.columns:
                    image_col = col
                    break
        self.image_col = image_col or self.df.columns[0]

        # Auto-detect label column
        if label_col is None:
            for col in ["Finding Labels", "finding_labels", "labels", "Label", "Finding"]:
                if col in self.df.columns:
                    label_col = col
                    break
        self.label_col = label_col or self.df.columns[1]

        # Pre-compute multi-label binary target matrix
        self.targets = self._encode_labels()

    def _encode_labels(self) -> np.ndarray:
        """
        Encode the pipe-separated findings (e.g. 'Atelectasis|Effusion') into a
        (N, num_classes) binary float32 numpy array.
        """
        targets = np.zeros((len(self.df), self.num_classes), dtype=np.float32)

        for i, raw_label in enumerate(self.df[self.label_col]):
            label_str = str(raw_label).strip()
            findings = [f.strip() for f in label_str.split("|")]

            for cls_idx, nih_label in enumerate(self.nih_labels):
                if nih_label in findings:
                    targets[i, cls_idx] = 1.0

        return targets

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        img_filename = str(self.df.iloc[idx][self.image_col])
        img_path = self.images_dir / img_filename

        # If not directly in images_dir, check subdirectories (e.g. images_001/images/...)
        if not img_path.exists():
            matches = list(self.images_dir.glob(f"**/{img_filename}"))
            if matches:
                img_path = matches[0]
            else:
                raise FileNotFoundError(
                    f"Radiograph image '{img_filename}' not found under '{self.images_dir}'"
                )

        # Open radiograph and convert to 3-channel RGB (required by DenseNet backbone)
        image = Image.open(img_path).convert("RGB")

        if self.transform is not None:
            image_tensor = self.transform(image)
        else:
            to_tensor = transforms.ToTensor() if transforms else None
            image_tensor = to_tensor(image) if to_tensor else image

        target_tensor = torch.from_numpy(self.targets[idx])
        return image_tensor, target_tensor


# Standard 14-disease taxonomy in timm/nih-chest-xray-14
NIH_14_CLASSES = [
    "Atelectasis",
    "Cardiomegaly",
    "Consolidation",
    "Edema",
    "Effusion",
    "Emphysema",
    "Fibrosis",
    "Hernia",
    "Infiltration",
    "Mass",
    "Nodule",
    "Pleural_Thickening",
    "Pneumonia",
    "Pneumothorax",
]


class HuggingFaceChestXRayDataset(Dataset):
    """
    PyTorch Dataset wrapper for the Hugging Face dataset (e.g. 'timm/nih-chest-xray-14').
    Maps the native 14-label findings to the canonical 10-class project definition.

    Safety & Medical Rules:
      1. Supported target classes (9 diseases + No Finding) are mapped according to
         backend/ml/disease_labels.json.
      2. Excluded pathologies ('Hernia', 'Edema', 'Emphysema', 'Fibrosis', 'Pleural_Thickening')
         are ignored in the 10-class target array, BUT an image containing only excluded
         pathologies is NOT marked as 'No Finding'. 'No Finding' is marked 1.0 ONLY when
         the radiograph is confirmed negative for ALL pathologies.
      3. Applies canonical preprocessing transforms (224x224, ImageNet normalization, no CLAHE).
    """

    def __init__(
        self,
        hf_dataset,
        label_config: list[dict] | None = None,
        transform: Callable | None = None,
    ) -> None:
        self.dataset = hf_dataset
        self.transform = transform or get_default_transforms(is_training=False)

        if label_config is None:
            self.label_config = load_label_config()
        else:
            self.label_config = label_config

        self.num_classes = len(self.label_config)
        self.class_names = [c["name"] for c in self.label_config]
        self.nih_to_idx = {
            c.get("nih_label", c["name"]).strip().lower(): c["index"]
            for c in self.label_config
        }
        self.no_finding_idx = None
        for c in self.label_config:
            if c.get("id") == "no_finding" or c.get("nih_label") == "No Finding":
                self.no_finding_idx = c["index"]
                break

    def __len__(self) -> int:
        return len(self.dataset)

    def _extract_findings(self, item: dict) -> list[str]:
        """Extract finding names as lower-case strings from HF sample."""
        if "label_names" in item and item["label_names"] is not None:
            return [str(name).strip().lower() for name in item["label_names"]]
        if "labels" in item and item["labels"] is not None:
            raw_labels = item["labels"]
            findings = []
            for val in raw_labels:
                if isinstance(val, int) and 0 <= val < len(NIH_14_CLASSES):
                    findings.append(NIH_14_CLASSES[val].lower())
                elif isinstance(val, str):
                    findings.append(val.strip().lower())
            return findings
        if "Finding Labels" in item and item["Finding Labels"] is not None:
            return [f.strip().lower() for f in str(item["Finding Labels"]).split("|")]
        return []

    def encode_target(self, item: dict) -> np.ndarray:
        """Encode finding list into a (num_classes,) float32 target vector."""
        target = np.zeros(self.num_classes, dtype=np.float32)
        findings = self._extract_findings(item)

        if not findings or findings == ["no finding"]:
            if self.no_finding_idx is not None:
                target[self.no_finding_idx] = 1.0
            return target

        for f in findings:
            if f in self.nih_to_idx:
                target[self.nih_to_idx[f]] = 1.0

        return target

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        item = self.dataset[idx]
        image_obj = item["image"]

        if isinstance(image_obj, Image.Image):
            image = image_obj.convert("RGB")
        elif isinstance(image_obj, (str, Path)):
            image = Image.open(image_obj).convert("RGB")
        elif isinstance(image_obj, bytes):
            image = Image.open(io.BytesIO(image_obj)).convert("RGB")
        elif isinstance(image_obj, dict) and "bytes" in image_obj:
            image = Image.open(io.BytesIO(image_obj["bytes"])).convert("RGB")
        else:
            raise TypeError(f"Unsupported image type: {type(image_obj)}")

        if self.transform is not None:
            image_tensor = self.transform(image)
        else:
            to_tensor = transforms.ToTensor() if transforms else None
            image_tensor = to_tensor(image) if to_tensor else image

        target_np = self.encode_target(item)
        target_tensor = torch.from_numpy(target_np)
        return image_tensor, target_tensor

