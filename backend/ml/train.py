"""
Basic College-Level Training Pipeline for DenseNet-121 Multi-Label Chest X-Ray Classification.

Intended for educational and research prototype development using the NIH ChestX-ray14 dataset.
- Evaluates on 10 standardized thoracic classes.
- Uses patient-level disjoint train/val/test splits.
- Trains with BCEWithLogitsLoss on multi-label targets.
- Saves checkpoint, disease label mapping, and preprocessing configuration.
- Evaluates on validation data before performing a final test evaluation.

If the dataset has not yet been downloaded, it gracefully prints a clear guidance message.
"""

from __future__ import annotations
import os
import sys
import json
import shutil
import logging
import argparse
import time
import itertools
from datetime import datetime
from pathlib import Path

# Add project root to sys.path to enable backend module imports
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("backend.ml.train")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Train DenseNet-121 on NIH ChestX-ray14 (10-Class Disease Detection)"
    )
    parser.add_argument(
        "--csv-path",
        type=str,
        default="backend/data/Data_Entry_2017.csv",
        help="Path to the NIH ChestX-ray14 metadata CSV (e.g. Data_Entry_2017.csv)",
    )
    parser.add_argument(
        "--img-dir",
        type=str,
        default="backend/data/images",
        help="Path to directory containing the chest radiograph image files",
    )
    parser.add_argument(
        "--labels-path",
        type=str,
        default="backend/ml/disease_labels.json",
        help="Path to the canonical 10-class JSON definition",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="backend/models/weights",
        help="Directory to save the trained model checkpoint (.pt) and config copies",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=5,
        help="Number of training epochs (default: 5)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Mini-batch size (default: 16)",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=1e-4,
        help="Adam optimizer learning rate (default: 0.0001)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        help="Compute device ('cuda', 'cpu', or 'auto')",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=0,
        help="DataLoader worker processes (default: 0 for Windows safety)",
    )
    parser.add_argument(
        "--hf-dataset",
        type=str,
        default=None,
        help="Optional Hugging Face dataset identifier (e.g. 'timm/nih-chest-xray-14').",
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=None,
        help="When using a Hugging Face dataset, limit to this many samples for quick smoke test.",
    )
    return parser.parse_args()


def display_dataset_missing_guide(csv_path: Path, img_dir: Path):
    """Display a clear, helpful message when the NIH ChestX-ray14 dataset is not found."""
    print("\n" + "=" * 80)
    print("              NIH ChestX-ray14 Dataset Not Found -- Training on Standby")
    print("=" * 80)
    print("\nModel training is not yet available because the dataset files were not detected.")
    print("The NIH ChestX-ray14 dataset is downloading separately.\n")
    print("Target paths checked:")
    print(f"  * Metadata CSV:  {csv_path.resolve()} (Exists: {csv_path.exists()})")
    print(f"  * Images Folder: {img_dir.resolve()} (Exists: {img_dir.exists()})\n")
    print("Option A (Local CSV & Images):")
    print("  1. Metadata CSV:   Save 'Data_Entry_2017.csv' to:  backend/data/Data_Entry_2017.csv")
    print("  2. Images Folder:  Extract PNGs into:  backend/data/images/")
    print("  3. Run:  python backend/ml/train.py --csv-path backend/data/Data_Entry_2017.csv --img-dir backend/data/images --epochs 5\n")
    print("Option B (Hugging Face Datasets -- timm/nih-chest-xray-14):")
    print("  * Storage notice: ~45-50 GB of disk space required for cache.")
    print("  * Run:  python backend/ml/train.py --hf-dataset timm/nih-chest-xray-14 --epochs 5\n")
    print("NOTE: The web application (frontend + backend) runs completely fine right now")
    print("      in Demo / Simulation Mode without requiring the dataset!")
    print("=" * 80 + "\n")


def build_model(num_classes: int = 10, pretrained_backbone: bool = True):
    """
    Build a DenseNet-121 model with a custom multi-label classification head.
    Uses ImageNet pre-trained weights for feature extraction when available.
    """
    import torch
    import torch.nn as nn
    import torchvision.models as models

    logger.info("Instantiating DenseNet-121 backbone (pretrained=%s)...", pretrained_backbone)
    try:
        if pretrained_backbone:
            weights = models.DenseNet121_Weights.DEFAULT
            model = models.densenet121(weights=weights)
        else:
            model = models.densenet121(weights=None)
    except Exception as e:
        logger.warning("Could not load online weights (%s). Initializing DenseNet-121 from scratch.", e)
        model = models.densenet121(weights=None)

    # Replace ImageNet 1000-class classifier with 10-class multi-label head
    in_features = model.classifier.in_features
    model.classifier = nn.Linear(in_features, num_classes)
    return model


def train_one_epoch(model, loader, criterion, optimizer, device):
    """Execute one training epoch."""
    import torch

    model.train()
    running_loss = 0.0
    total_samples = 0

    for step, (images, targets) in enumerate(loader):
        images = images.to(device)
        targets = targets.to(device)

        optimizer.zero_grad()
        logits = model(images)
        loss = criterion(logits, targets)
        loss.backward()
        optimizer.step()

        batch_size = images.size(0)
        running_loss += loss.item() * batch_size
        total_samples += batch_size

        if (step + 1) % 20 == 0 or (step + 1) == len(loader):
            current_avg_loss = running_loss / max(1, total_samples)
            logger.info("  Step [%d/%d] - Batch Loss: %.4f - Running Avg Loss: %.4f",
                        step + 1, len(loader), loss.item(), current_avg_loss)

    return running_loss / max(1, total_samples)


def evaluate(model, loader, criterion, device, class_names):
    """Evaluate model on validation or test dataset, handling empty loaders safely."""
    import torch
    import numpy as np
    from backend.ml.evaluation import compute_multilabel_metrics

    if hasattr(loader, 'dataset') and len(loader.dataset) == 0:
        logger.warning("Evaluation dataset is empty; returning zero metrics.")
        zero_metrics = {c:{'auroc':0.0,'sensitivity':0.0,'specificity':0.0,'f1':0.0} for c in class_names}
        return 0.0, 0.0, zero_metrics

    model.eval()
    running_loss = 0.0
    total_samples = 0
    all_targets = []
    all_probs = []
    with torch.no_grad():
        for images, targets in loader:
            images = images.to(device)
            targets = targets.to(device)
            logits = model(images)
            loss = criterion(logits, targets)
            probs = torch.sigmoid(logits)
            batch_size = images.size(0)
            running_loss += loss.item() * batch_size
            total_samples += batch_size
            all_targets.append(targets.cpu().numpy())
            all_probs.append(probs.cpu().numpy())
    if not all_targets:
        logger.warning("No batches processed during evaluation; returning zero metrics.")
        zero_metrics = {c:{'auroc':0.0,'sensitivity':0.0,'specificity':0.0,'f1':0.0} for c in class_names}
        return 0.0, 0.0, zero_metrics
    avg_loss = running_loss / max(1, total_samples)
    y_true = np.vstack(all_targets)
    y_prob = np.vstack(all_probs)
    metrics = compute_multilabel_metrics(y_true, y_prob, class_names)
    mean_auroc = float(np.mean([m["auroc"] for m in metrics.values()]))
    return avg_loss, mean_auroc, metrics


def main():
    args = parse_args()

    csv_path = Path(args.csv_path)
    img_dir = Path(args.img_dir)
    labels_path = Path(args.labels_path)
    output_dir = Path(args.output_dir)

    # ── Pre-flight check: Verify if dataset files exist ───────────────────
    if args.hf_dataset:
        try:
            import datasets
            from datasets import load_dataset
        except ImportError:
            print("\n" + "=" * 80)
            print("         Hugging Face 'datasets' Library Required For This Mode")
            print("=" * 80)
            print(f"\nYou specified '--hf-dataset {args.hf_dataset}'.")
            print("To load data directly from Hugging Face, install the datasets library:")
            print("  pip install datasets\n")
            print("STORAGE ESTIMATE & ADVISORY:")
            print(f"  * Dataset: {args.hf_dataset}")
            print("  * Disk Space Required: ~45-50 GB (Hugging Face cache directory)")
            print("  * Please ensure your target drive has at least 50 GB free space before downloading.")
            print("=" * 80 + "\n")
            return 1
    elif not csv_path.exists() or not img_dir.exists():
        display_dataset_missing_guide(csv_path, img_dir)
        return 0

    # ── PyTorch check ─────────────────────────────────────────────────────
    try:
        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader
        import pandas as pd
        from backend.ml.dataset import (
            load_label_config,
            get_default_transforms,
            create_patient_splits,
            ChestXRayDataset,
            HuggingFaceChestXRayDataset,
        )
    except ImportError as e:
        logger.error(
            "Required ML libraries missing (%s). Please install backend dependencies:\n"
            "  pip install -r backend/requirements.txt", e
        )
        return 1

    # Device selection
    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)
    logger.info("Using compute device: %s", device)

    # Load 10-class label configuration
    label_config = load_label_config(labels_path)
    class_names = [c["name"] for c in label_config]
    num_classes = len(class_names)
    logger.info("Loaded %d target disease classes from %s: %s",
                num_classes, labels_path, class_names)

    # Transforms
    train_transforms = get_default_transforms(input_size=224, is_training=True)
    eval_transforms = get_default_transforms(input_size=224, is_training=False)

    if args.hf_dataset:
        logger.info("Loading Hugging Face dataset '%s' in streaming mode...", args.hf_dataset)
        # Load train split as streaming IterableDataset
        try:
            hf_train = load_dataset(args.hf_dataset, split='train', streaming=True)
        except Exception as e:
            logger.error("Failed to load Hugging Face dataset '%s' (train split): %s", args.hf_dataset, e)
            return 1

        # Materialize records with progress logging
        effective_limit = args.sample_limit or float('inf')
        logger.info("Streaming up to %s records from HF dataset...",
                    str(args.sample_limit) if args.sample_limit else 'ALL')
        hf_train_list = []
        load_start = time.time()
        for i, record in enumerate(hf_train):
            if i >= effective_limit:
                break
            hf_train_list.append(record)
            if (i + 1) % 500 == 0:
                elapsed = time.time() - load_start
                logger.info("  Loaded %d records (%.1fs elapsed, %.1f rec/s)",
                            i + 1, elapsed, (i + 1) / max(elapsed, 0.01))
        load_elapsed = time.time() - load_start
        logger.info("Finished loading %d records in %.1fs", len(hf_train_list), load_elapsed)

        # Patient-level split
        import random
        def patient_split_hf(data, train_ratio=0.70, val_ratio=0.10, test_ratio=0.20, seed=42):
            """Split a list of HF records into train/val/test respecting patient IDs.

            Ensures at least one sample in the training split. Validation and test
            splits may be empty for very small datasets.
            """
            rng = random.Random(seed)
            working = list(data)
            rng.shuffle(working)
            groups = {}
            for item in working:
                pid = item.get('patient_id') or item.get('Patient ID') or str(id(item))
                groups.setdefault(pid, []).append(item)
            patient_ids = list(groups.keys())
            rng.shuffle(patient_ids)
            n_total = len(patient_ids)
            n_train = max(1, int(n_total * train_ratio)) if n_total > 0 else 0
            n_val = int(n_total * val_ratio)
            train_pids = set(patient_ids[:n_train])
            val_pids = set(patient_ids[n_train:n_train + n_val])
            test_pids = set(patient_ids[n_train + n_val:])
            train_items, val_items, test_items = [], [], []
            for pid, items in groups.items():
                if pid in train_pids:
                    train_items.extend(items)
                elif pid in val_pids:
                    val_items.extend(items)
                else:
                    test_items.extend(items)
            return train_items, val_items, test_items, train_pids, val_pids, test_pids

        train_items, val_items, test_items, train_pids, val_pids, test_pids = \
            patient_split_hf(hf_train_list, seed=42)

        if len(train_items) == 0:
            logger.warning("Training split empty after patient split; using all items.")
            train_items = hf_train_list

        # Log split statistics
        logger.info("Patient-level split results:")
        logger.info("  Train: %d samples, %d patients", len(train_items), len(train_pids))
        logger.info("  Val:   %d samples, %d patients", len(val_items), len(val_pids))
        logger.info("  Test:  %d samples, %d patients", len(test_items), len(test_pids))

        # Save split metadata
        split_meta = {
            "timestamp": datetime.now().isoformat(),
            "dataset": args.hf_dataset,
            "sample_limit": args.sample_limit,
            "total_records_loaded": len(hf_train_list),
            "load_time_seconds": round(load_elapsed, 1),
            "split_seed": 42,
            "train": {"samples": len(train_items), "patients": len(train_pids)},
            "val": {"samples": len(val_items), "patients": len(val_pids)},
            "test": {"samples": len(test_items), "patients": len(test_pids)},
            "patient_id_field": "patient_id",
            "patient_ids_verified": all(
                item.get('patient_id') is not None for item in hf_train_list[:10]
            ),
        }
        output_dir.mkdir(parents=True, exist_ok=True)
        split_meta_path = output_dir / "split_metadata.json"
        with open(split_meta_path, 'w') as f:
            json.dump(split_meta, f, indent=2)
        logger.info("Split metadata saved to %s", split_meta_path)

        train_dataset = HuggingFaceChestXRayDataset(train_items, label_config, transform=train_transforms)
        val_dataset = HuggingFaceChestXRayDataset(val_items, label_config, transform=eval_transforms)
        test_dataset = HuggingFaceChestXRayDataset(test_items, label_config, transform=eval_transforms)
        test_df = range(len(test_dataset))
    else:
        # Load dataset metadata CSV
        logger.info("Reading dataset CSV: %s", csv_path)
        df = pd.read_csv(csv_path)
        logger.info("Loaded %d total image records from CSV.", len(df))

        # Patient-level disjoint splitting
        train_df, val_df, test_df = create_patient_splits(
            df=df,
            train_ratio=0.70,
            val_ratio=0.10,
            test_ratio=0.20,
            random_seed=42,
        )

        train_dataset = ChestXRayDataset(train_df, img_dir, label_config, transform=train_transforms)
        val_dataset = ChestXRayDataset(val_df, img_dir, label_config, transform=eval_transforms)
        test_dataset = ChestXRayDataset(test_df, img_dir, label_config, transform=eval_transforms)

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=(device.type == "cuda"),
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=(device.type == "cuda"),
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
    )

    # Build model, loss function, and optimizer
    model = build_model(num_classes=num_classes, pretrained_backbone=True).to(device)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    output_dir.mkdir(parents=True, exist_ok=True)
    best_val_auroc = 0.0
    best_checkpoint_path = output_dir / "densenet121_cxr.pt"
    best_val_checkpoint_path = output_dir / "best_val_auroc.pt"
    final_checkpoint_path = output_dir / "densenet121_cxr_final.pt"

    # Back up existing checkpoint before overwriting
    if best_checkpoint_path.exists():
        backup_path = output_dir / "densenet121_cxr_backup.pt"
        if not backup_path.exists():
            shutil.copy(best_checkpoint_path, backup_path)
            logger.info("Backed up existing checkpoint to %s", backup_path)

    # Training history tracker
    train_history = {
        "start_time": datetime.now().isoformat(),
        "device": str(device),
        "epochs_planned": args.epochs,
        "batch_size": args.batch_size,
        "learning_rate": args.lr,
        "num_classes": num_classes,
        "class_names": class_names,
        "epochs": [],
    }

    logger.info("Starting DenseNet-121 training for %d epochs...", args.epochs)
    train_start = time.time()

    for epoch in range(1, args.epochs + 1):
        epoch_start = time.time()
        logger.info("========== Epoch [%d/%d] ==========", epoch, args.epochs)
        train_loss = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_auroc, val_metrics = evaluate(model, val_loader, criterion, device, class_names)
        epoch_time = time.time() - epoch_start

        logger.info(
            "Epoch [%d/%d] Summary -> Train Loss: %.4f | Val Loss: %.4f | Val Mean AUROC: %.4f | Time: %.1fs",
            epoch, args.epochs, train_loss, val_loss, val_auroc, epoch_time
        )

        # Record history
        train_history["epochs"].append({
            "epoch": epoch,
            "train_loss": round(train_loss, 6),
            "val_loss": round(val_loss, 6),
            "val_auroc": round(val_auroc, 6),
            "epoch_time_seconds": round(epoch_time, 1),
        })

        # Save best checkpoint according to validation AUROC
        if val_auroc > best_val_auroc or epoch == 1:
            best_val_auroc = val_auroc
            logger.info("Saving best model checkpoint to %s (Val AUROC: %.4f)...",
                        best_checkpoint_path, best_val_auroc)
            torch.save(model.state_dict(), best_checkpoint_path)
            torch.save(model.state_dict(), best_val_checkpoint_path)
            shutil.copy(labels_path, output_dir / "disease_labels.json")
            prep_cfg = labels_path.parent / "preprocessing_config.json"
            if prep_cfg.exists():
                shutil.copy(prep_cfg, output_dir / "preprocessing_config.json")

    # Save final-epoch checkpoint
    torch.save(model.state_dict(), final_checkpoint_path)
    logger.info("Final checkpoint saved to %s", final_checkpoint_path)

    total_train_time = time.time() - train_start
    train_history["end_time"] = datetime.now().isoformat()
    train_history["total_training_seconds"] = round(total_train_time, 1)
    train_history["best_val_auroc"] = round(best_val_auroc, 6)

    # Save training history
    history_path = output_dir / "train_history.json"
    with open(history_path, 'w') as f:
        json.dump(train_history, f, indent=2)
    logger.info("Training history saved to %s", history_path)

    # Save loss curves
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        epochs_list = [e["epoch"] for e in train_history["epochs"]]
        train_losses = [e["train_loss"] for e in train_history["epochs"]]
        val_losses = [e["val_loss"] for e in train_history["epochs"]]
        val_aurocs = [e["val_auroc"] for e in train_history["epochs"]]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        ax1.plot(epochs_list, train_losses, 'b-o', label='Train Loss')
        ax1.plot(epochs_list, val_losses, 'r-o', label='Val Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('BCE Loss')
        ax1.set_title('Training & Validation Loss')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        ax2.plot(epochs_list, val_aurocs, 'g-o', label='Val Mean AUROC')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('AUROC')
        ax2.set_title('Validation AUROC')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, 1)

        plt.tight_layout()
        curves_path = output_dir / "loss_curves.png"
        plt.savefig(curves_path, dpi=150)
        plt.close()
        logger.info("Loss curves saved to %s", curves_path)
    except Exception as e:
        logger.warning("Could not save loss curves: %s", e)

    # ── Post-training evaluation on held-out test partition ───────────────
    logger.info("\nEvaluating best checkpoint on held-out test cohort (%d images)...", len(test_df))
    if best_checkpoint_path.exists():
        state_dict = torch.load(best_checkpoint_path, map_location=device)
        model.load_state_dict(state_dict)

    test_loss, test_auroc, test_metrics = evaluate(model, test_loader, criterion, device, class_names)

    # Build evaluation report
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("                     FINAL HELD-OUT TEST EVALUATION REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"Overall Test Loss: {test_loss:.4f} | Mean Test AUROC: {test_auroc:.4f}")
    report_lines.append(f"Test samples: {len(test_df)} | Best Val AUROC: {best_val_auroc:.4f}")
    report_lines.append("")
    header = f"{'Class Name':<20} | {'AUROC':<8} | {'Sens.':<8} | {'Spec.':<8} | {'F1':<8} | {'TP':<5} | {'FP':<5} | {'TN':<5} | {'FN':<5} | {'Support':<7}"
    report_lines.append(header)
    report_lines.append("-" * len(header))
    for cname, m in test_metrics.items():
        support = m.get('tp', 0) + m.get('fn', 0)
        report_lines.append(
            f"{cname:<20} | {m['auroc']:<8.4f} | {m.get('sensitivity', 0):<8.4f} | "
            f"{m.get('specificity', 0):<8.4f} | {m.get('f1', 0):<8.4f} | "
            f"{m.get('tp', 0):<5} | {m.get('fp', 0):<5} | {m.get('tn', 0):<5} | "
            f"{m.get('fn', 0):<5} | {support:<7}"
        )
    report_lines.append("=" * len(header))
    report_lines.append(f"")
    report_lines.append(f"Model checkpoint: {best_checkpoint_path.resolve()}")
    report_lines.append(f"Final checkpoint: {final_checkpoint_path.resolve()}")
    report_lines.append(f"Training history: {history_path.resolve()}")
    report_lines.append("")
    report_lines.append("To serve this trained model, configure backend/.env:")
    report_lines.append("  MODEL_MODE=real")
    report_lines.append(f"  MODEL_PATH={best_checkpoint_path.resolve()}")

    report_text = "\n".join(report_lines)
    print("\n" + report_text + "\n")

    # Save evaluation report
    eval_report_path = output_dir / "evaluation_report.txt"
    with open(eval_report_path, 'w') as f:
        f.write(report_text + "\n")
    logger.info("Evaluation report saved to %s", eval_report_path)

    # Save evaluation metrics as JSON
    eval_json = {
        "timestamp": datetime.now().isoformat(),
        "test_loss": round(test_loss, 6),
        "test_auroc": round(test_auroc, 6),
        "best_val_auroc": round(best_val_auroc, 6),
        "test_samples": len(test_df),
        "per_class": test_metrics,
    }
    eval_json_path = output_dir / "evaluation_results.json"
    with open(eval_json_path, 'w') as f:
        json.dump(eval_json, f, indent=2)
    logger.info("Evaluation JSON saved to %s", eval_json_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
