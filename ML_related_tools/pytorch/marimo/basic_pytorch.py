# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "marimo>=0.24.2",
# ]
# ///

import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import itertools
    import random
    import re
    from collections import Counter
    from functools import partial

    import marimo as mo
    import numpy as np
    import polars as pl
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.utils.data import DataLoader, Dataset
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
    from sklearn.model_selection import train_test_split
    from transformers import AutoModel, AutoTokenizer
    import matplotlib.pyplot as plt

    return (
        AutoModel,
        AutoTokenizer,
        Counter,
        DataLoader,
        Dataset,
        F,
        accuracy_score,
        classification_report,
        confusion_matrix,
        itertools,
        mo,
        nn,
        np,
        partial,
        pl,
        plt,
        random,
        re,
        torch,
        train_test_split,
    )


@app.cell
def _(mo):
    mo.md(r"""
    # Text multiclass classification, end to end

    This notebook walks through the full lifecycle of a text multiclass
    classifier in PyTorch, twice over:

    1. **A custom model trained from scratch** — our own vocabulary and a
       trainable embedding table feeding a small feed-forward head.
    2. **Transfer learning** — a pretrained DistilBERT encoder whose
       contextual embeddings feed the *same kind* of classification head.

    Both models share one interface (`forward(input_ids, attention_mask)`)
    so the training loop, evaluation, and inference code are written once
    and reused for both.
    """)
    return


@app.cell
def _(np, random, torch):
    SEED = 42
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    DEVICE = torch.device("cpu")
    return DEVICE, SEED


@app.cell
def _(mo):
    mo.md(r"""
    ## 1. Data
    """)
    return


@app.cell
def _(itertools, random):
    # A small, fully offline, templated dataset: sentences are assembled from
    # per-category (subject, verb, object) word pools, so each class has a
    # distinctive but overlapping vocabulary — enough signal to learn, not so
    # much that the task is trivial.
    CATEGORY_VOCAB = {
        "sports": {
            "subjects": ["The striker", "The goalkeeper", "Our coach", "The tennis champion",
                         "The marathon runner", "The home team", "The rookie point guard", "The Olympic swimmer"],
            "verbs": ["scored a stunning goal in", "won the championship after", "trained hard before",
                      "broke the record during", "celebrated the victory following", "suffered an injury in",
                      "signed a new contract before", "qualified for the finals after"],
            "objects": ["the final match", "last night's game", "the regional tournament",
                        "the world cup qualifier", "this season's opener", "the playoff series",
                        "the away fixture", "the derby against their rivals"],
        },
        "technology": {
            "subjects": ["The startup", "Our engineering team", "The new smartphone", "The software update",
                         "The AI research lab", "The cloud provider", "The chip manufacturer", "The open source project"],
            "verbs": ["released a major update to", "launched a groundbreaking feature in",
                      "fixed a critical bug within", "announced a partnership for", "open sourced the code behind",
                      "patented a new algorithm for", "doubled the battery life of", "reduced the latency of"],
            "objects": ["the mobile application", "the cloud infrastructure", "the machine learning pipeline",
                        "the operating system", "the developer platform", "the neural network model",
                        "the data center", "the user interface"],
        },
        "cooking": {
            "subjects": ["The head chef", "My grandmother", "The bakery", "The food blogger",
                         "The restaurant", "The home cook", "The pastry chef", "The catering team"],
            "verbs": ["prepared a delicious recipe for", "baked a fresh batch of", "seasoned generously the",
                      "simmered for hours the", "garnished beautifully the", "roasted to perfection the",
                      "whisked together the ingredients for", "plated elegantly the"],
            "objects": ["the chocolate cake", "the tomato soup", "sourdough bread", "the roasted vegetables",
                        "the spicy curry", "the seasonal salad", "the homemade pasta", "the grilled salmon"],
        },
        "finance": {
            "subjects": ["The central bank", "The stock market", "Investors", "The hedge fund",
                         "The startup's valuation", "The quarterly earnings report", "The finance minister",
                         "The credit rating agency"],
            "verbs": ["raised interest rates amid", "reported strong growth in", "downgraded the outlook for",
                      "announced a merger involving", "forecasted a decline in", "boosted confidence across",
                      "tightened regulations on", "revised the forecast for"],
            "objects": ["the housing market", "the technology sector", "emerging markets",
                        "the banking industry", "consumer spending", "the bond market",
                        "international trade", "the retail sector"],
        },
    }

    LABEL_NAMES = sorted(CATEGORY_VOCAB.keys())
    label2id = {name: i for i, name in enumerate(LABEL_NAMES)}
    id2label = {i: name for name, i in label2id.items()}
    NUM_CLASSES = len(LABEL_NAMES)

    N_PER_CLASS = 130
    texts, labels = [], []
    for _name in LABEL_NAMES:
        _pools = CATEGORY_VOCAB[_name]
        _combos = list(itertools.product(_pools["subjects"], _pools["verbs"], _pools["objects"]))
        random.shuffle(_combos)
        for _subj, _verb, _obj in _combos[:N_PER_CLASS]:
            texts.append(f"{_subj} {_verb} {_obj}.")
            labels.append(label2id[_name])

    _combined = list(zip(texts, labels))
    random.shuffle(_combined)
    texts = [t for t, _ in _combined]
    labels = [l for _, l in _combined]

    # A little label noise keeps the task from being perfectly separable, so
    # the two models' evaluation numbers below are meaningfully comparable
    # instead of both trivially hitting 100%.
    NOISE_RATE = 0.08
    for _i in range(len(labels)):
        if random.random() < NOISE_RATE:
            labels[_i] = random.choice([l for l in range(NUM_CLASSES) if l != labels[_i]])

    print(f"Generated {len(texts)} examples across {NUM_CLASSES} classes: {LABEL_NAMES}")
    return LABEL_NAMES, NUM_CLASSES, id2label, labels, texts


@app.cell
def _(LABEL_NAMES, labels, pl, texts):
    dataset_preview = pl.DataFrame(
        {"text": texts, "label": [LABEL_NAMES[l] for l in labels]}
    )
    dataset_preview.head(n=10)
    return


@app.cell
def _(SEED, labels, texts, train_test_split):
    train_texts, _temp_texts, train_labels, _temp_labels = train_test_split(
        texts, labels, test_size=0.3, random_state=SEED, stratify=labels
    )
    val_texts, test_texts, val_labels, test_labels = train_test_split(
        _temp_texts, _temp_labels, test_size=0.5, random_state=SEED, stratify=_temp_labels
    )
    print(f"train={len(train_texts)}  val={len(val_texts)}  test={len(test_texts)}")
    return (
        test_labels,
        test_texts,
        train_labels,
        train_texts,
        val_labels,
        val_texts,
    )


@app.cell
def _():
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 2. A custom model, trained from scratch

    We build our own vocabulary from the training data, embed tokens with
    a freshly-initialized (untrained) `nn.Embedding`, mean-pool over the
    real (non-padding) tokens, and classify with a small MLP head.
    """)
    return


@app.cell
def _(Counter, re, train_texts):
    def simple_tokenize(text):
        return re.findall(r"[a-z']+", text.lower())

    def build_vocab(texts, min_freq=1):
        counter = Counter()
        for t in texts:
            counter.update(simple_tokenize(t))
        itos = ["<pad>", "<unk>"] + [w for w, c in counter.most_common() if c >= min_freq]
        return {w: i for i, w in enumerate(itos)}

    vocab = build_vocab(train_texts)
    PAD_IDX = vocab["<pad>"]
    UNK_IDX = vocab["<unk>"]
    VOCAB_SIZE = len(vocab)
    MAX_LEN = 24
    print(f"vocabulary size: {VOCAB_SIZE}")
    return MAX_LEN, PAD_IDX, UNK_IDX, VOCAB_SIZE, simple_tokenize, vocab


@app.cell
def _(Dataset):
    class TextClassificationDataset(Dataset):
        """Wraps raw (text, label) pairs; tokenization happens in collate_fn."""

        def __init__(self, texts, labels):
            self.texts = texts
            self.labels = labels

        def __len__(self):
            return len(self.texts)

        def __getitem__(self, idx):
            return self.texts[idx], self.labels[idx]

    return (TextClassificationDataset,)


@app.cell
def _(
    DataLoader,
    MAX_LEN,
    PAD_IDX,
    TextClassificationDataset,
    UNK_IDX,
    partial,
    simple_tokenize,
    test_labels,
    test_texts,
    torch,
    train_labels,
    train_texts,
    val_labels,
    val_texts,
    vocab,
):
    def encode_custom(batch, vocab, tokenize_fn, max_len, pad_idx, unk_idx):
        batch_texts = [t for t, _ in batch]
        batch_labels = [l for _, l in batch]
        ids_list, mask_list = [], []
        for t in batch_texts:
            toks = tokenize_fn(t)[:max_len]
            ids = [vocab.get(tok, unk_idx) for tok in toks]
            mask = [1] * len(ids)
            pad_len = max_len - len(ids)
            ids = ids + [pad_idx] * pad_len
            mask = mask + [0] * pad_len
            ids_list.append(ids)
            mask_list.append(mask)
        input_ids = torch.tensor(ids_list, dtype=torch.long)
        attention_mask = torch.tensor(mask_list, dtype=torch.long)
        labels_t = torch.tensor(batch_labels, dtype=torch.long)
        return {"input_ids": input_ids, "attention_mask": attention_mask}, labels_t

    custom_collate = partial(
        encode_custom, vocab=vocab, tokenize_fn=simple_tokenize,
        max_len=MAX_LEN, pad_idx=PAD_IDX, unk_idx=UNK_IDX,
    )
    BATCH_SIZE = 16
    custom_train_loader = DataLoader(
        TextClassificationDataset(train_texts, train_labels),
        batch_size=BATCH_SIZE, shuffle=True, collate_fn=custom_collate,
    )
    custom_val_loader = DataLoader(
        TextClassificationDataset(val_texts, val_labels),
        batch_size=BATCH_SIZE, shuffle=False, collate_fn=custom_collate,
    )
    custom_test_loader = DataLoader(
        TextClassificationDataset(test_texts, test_labels),
        batch_size=BATCH_SIZE, shuffle=False, collate_fn=custom_collate,
    )
    return (
        BATCH_SIZE,
        custom_collate,
        custom_test_loader,
        custom_train_loader,
        custom_val_loader,
    )


@app.cell
def _(F, nn):
    class CustomTextClassifier(nn.Module):
        """Trainable embedding table + mean pooling + MLP head."""

        def __init__(self, vocab_size, embed_dim=64, hidden_dim=64, num_classes=4, pad_idx=0):
            super().__init__()
            self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)
            self.fc1 = nn.Linear(embed_dim, hidden_dim)
            self.dropout = nn.Dropout(0.2)
            self.fc2 = nn.Linear(hidden_dim, num_classes)

        def forward(self, input_ids, attention_mask):
            emb = self.embedding(input_ids)
            mask = attention_mask.unsqueeze(-1).float()
            pooled = (emb * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
            x = self.dropout(F.relu(self.fc1(pooled)))
            return self.fc2(x)

    return (CustomTextClassifier,)


@app.cell
def _(F, torch):
    # Generic train/eval helpers shared by both the custom and transfer models,
    # since both expose the same forward(input_ids, attention_mask) interface.

    def run_epoch(model, loader, device, criterion, optimizer=None):
        is_train = optimizer is not None
        model.train() if is_train else model.eval()
        total_loss, total_correct, total_count = 0.0, 0, 0
        with torch.set_grad_enabled(is_train):
            for batch_inputs, batch_labels in loader:
                batch_inputs = {k: v.to(device) for k, v in batch_inputs.items()}
                batch_labels = batch_labels.to(device)
                logits = model(**batch_inputs)
                loss = criterion(logits, batch_labels)
                if is_train:
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()
                total_loss += loss.item() * batch_labels.size(0)
                total_correct += (logits.argmax(1) == batch_labels).sum().item()
                total_count += batch_labels.size(0)
        return total_loss / total_count, total_correct / total_count

    def fit(model, train_loader, val_loader, device, criterion, optimizer, epochs, model_name="model"):
        history = []
        for epoch in range(1, epochs + 1):
            train_loss, train_acc = run_epoch(model, train_loader, device, criterion, optimizer)
            val_loss, val_acc = run_epoch(model, val_loader, device, criterion, optimizer=None)
            history.append({
                "epoch": epoch, "train_loss": train_loss, "train_acc": train_acc,
                "val_loss": val_loss, "val_acc": val_acc,
            })
            print(
                f"[{model_name}] epoch {epoch}/{epochs}  "
                f"train_loss={train_loss:.4f} train_acc={train_acc:.3f}  "
                f"val_loss={val_loss:.4f} val_acc={val_acc:.3f}"
            )
        return history

    def collect_predictions(model, loader, device):
        model.eval()
        all_preds, all_labels = [], []
        with torch.no_grad():
            for batch_inputs, batch_labels in loader:
                batch_inputs = {k: v.to(device) for k, v in batch_inputs.items()}
                logits = model(**batch_inputs)
                all_preds.extend(logits.argmax(dim=1).cpu().tolist())
                all_labels.extend(batch_labels.tolist())
        return all_labels, all_preds

    def predict_single(model, text, encode_fn, device, id2label):
        model.eval()
        batch_inputs, _ = encode_fn([(text, 0)])
        batch_inputs = {k: v.to(device) for k, v in batch_inputs.items()}
        with torch.no_grad():
            logits = model(**batch_inputs)
            probs = F.softmax(logits, dim=1).cpu().numpy()[0]
        pred_id = int(probs.argmax())
        return id2label[pred_id], probs

    return collect_predictions, fit, predict_single


@app.cell
def _(confusion_matrix, plt):
    def plot_history(history, title):
        epochs = [h["epoch"] for h in history]
        fig, axes = plt.subplots(1, 2, figsize=(9, 3.2))
        axes[0].plot(epochs, [h["train_loss"] for h in history], label="train")
        axes[0].plot(epochs, [h["val_loss"] for h in history], label="val")
        axes[0].set_title("Loss")
        axes[0].set_xlabel("epoch")
        axes[0].legend()
        axes[1].plot(epochs, [h["train_acc"] for h in history], label="train")
        axes[1].plot(epochs, [h["val_acc"] for h in history], label="val")
        axes[1].set_title("Accuracy")
        axes[1].set_xlabel("epoch")
        axes[1].legend()
        fig.suptitle(title)
        fig.tight_layout()
        return fig

    def plot_confusion(y_true, y_pred, label_names, title):
        cm = confusion_matrix(y_true, y_pred)
        fig, ax = plt.subplots(figsize=(4.2, 4.2))
        im = ax.imshow(cm, cmap="Blues")
        ax.set_xticks(range(len(label_names)))
        ax.set_xticklabels(label_names, rotation=45, ha="right")
        ax.set_yticks(range(len(label_names)))
        ax.set_yticklabels(label_names)
        ax.set_xlabel("predicted")
        ax.set_ylabel("true")
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                color = "black" if cm[i, j] < cm.max() / 2 else "white"
                ax.text(j, i, str(cm[i, j]), ha="center", va="center", color=color)
        ax.set_title(title)
        fig.colorbar(im, ax=ax, fraction=0.046)
        fig.tight_layout()
        return fig

    return plot_confusion, plot_history


@app.cell
def _(mo):
    custom_epochs_slider = mo.ui.slider(
        start=2, stop=25, step=1, value=12, label="Custom model — training epochs"
    )
    custom_epochs_slider
    return (custom_epochs_slider,)


@app.cell
def _(
    CustomTextClassifier,
    DEVICE,
    NUM_CLASSES,
    PAD_IDX,
    VOCAB_SIZE,
    custom_epochs_slider,
    custom_train_loader,
    custom_val_loader,
    fit,
    nn,
    torch,
):
    custom_model = CustomTextClassifier(
        VOCAB_SIZE, embed_dim=64, hidden_dim=64, num_classes=NUM_CLASSES, pad_idx=PAD_IDX
    ).to(DEVICE)
    custom_criterion = nn.CrossEntropyLoss()
    custom_optimizer = torch.optim.Adam(custom_model.parameters(), lr=1e-3)
    custom_history = fit(
        custom_model, custom_train_loader, custom_val_loader, DEVICE,
        custom_criterion, custom_optimizer, custom_epochs_slider.value, model_name="custom",
    )
    return custom_history, custom_model


@app.cell
def _(custom_history, plot_history):
    fig_custom_hist = plot_history(custom_history, "Custom model (trained from scratch)")
    fig_custom_hist
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Evaluating the custom model
    """)
    return


@app.cell
def _(
    DEVICE,
    LABEL_NAMES,
    accuracy_score,
    classification_report,
    collect_predictions,
    custom_model,
    custom_test_loader,
):
    custom_y_true, custom_y_pred = collect_predictions(custom_model, custom_test_loader, DEVICE)
    custom_test_acc = accuracy_score(custom_y_true, custom_y_pred)
    custom_report = classification_report(
        custom_y_true, custom_y_pred, target_names=LABEL_NAMES, digits=3
    )
    print(f"Custom model test accuracy: {custom_test_acc:.3f}\n")
    print(custom_report)
    return custom_test_acc, custom_y_pred, custom_y_true


@app.cell
def _(LABEL_NAMES, custom_y_pred, custom_y_true, plot_confusion):
    fig_custom_cm = plot_confusion(
        custom_y_true, custom_y_pred, LABEL_NAMES, "Custom model — confusion matrix"
    )
    fig_custom_cm
    return


@app.cell
def _():
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 3. Transfer learning with a pretrained encoder (DistilBERT)

    Instead of learning token embeddings from nothing, we reuse
    `distilbert-base-uncased`'s pretrained contextual embeddings and
    mean-pool + classify on top of them — the same head shape as the
    custom model above, just fed richer representations.
    """)
    return


@app.cell
def _(AutoModel, AutoTokenizer):
    BERT_MODEL_NAME = "distilbert-base-uncased"
    bert_tokenizer = AutoTokenizer.from_pretrained(BERT_MODEL_NAME)
    bert_backbone = AutoModel.from_pretrained(BERT_MODEL_NAME)
    BERT_HIDDEN = bert_backbone.config.hidden_size
    print(f"{BERT_MODEL_NAME}: hidden_size={BERT_HIDDEN}, params={sum(p.numel() for p in bert_backbone.parameters()):,}")
    return BERT_HIDDEN, bert_backbone, bert_tokenizer


@app.cell
def _(
    BATCH_SIZE,
    DataLoader,
    MAX_LEN,
    TextClassificationDataset,
    bert_tokenizer,
    partial,
    test_labels,
    test_texts,
    torch,
    train_labels,
    train_texts,
    val_labels,
    val_texts,
):
    def encode_bert(batch, tokenizer, max_len):
        batch_texts = [t for t, _ in batch]
        batch_labels = [l for _, l in batch]
        enc = tokenizer(
            list(batch_texts), padding="max_length", truncation=True,
            max_length=max_len, return_tensors="pt",
        )
        labels_t = torch.tensor(batch_labels, dtype=torch.long)
        return {"input_ids": enc["input_ids"], "attention_mask": enc["attention_mask"]}, labels_t

    bert_collate = partial(encode_bert, tokenizer=bert_tokenizer, max_len=MAX_LEN)
    bert_train_loader = DataLoader(
        TextClassificationDataset(train_texts, train_labels),
        batch_size=BATCH_SIZE, shuffle=True, collate_fn=bert_collate,
    )
    bert_val_loader = DataLoader(
        TextClassificationDataset(val_texts, val_labels),
        batch_size=BATCH_SIZE, shuffle=False, collate_fn=bert_collate,
    )
    bert_test_loader = DataLoader(
        TextClassificationDataset(test_texts, test_labels),
        batch_size=BATCH_SIZE, shuffle=False, collate_fn=bert_collate,
    )
    return bert_collate, bert_test_loader, bert_train_loader, bert_val_loader


@app.cell
def _(nn):
    class TransferTextClassifier(nn.Module):
        """Pretrained backbone + mean pooling + the same MLP-style head."""

        def __init__(self, backbone, hidden_size, num_classes, freeze_backbone=True):
            super().__init__()
            self.backbone = backbone
            self.dropout = nn.Dropout(0.2)
            self.classifier = nn.Linear(hidden_size, num_classes)
            if freeze_backbone:
                for p in self.backbone.parameters():
                    p.requires_grad = False

        def forward(self, input_ids, attention_mask):
            outputs = self.backbone(input_ids=input_ids, attention_mask=attention_mask)
            hidden = outputs.last_hidden_state
            mask = attention_mask.unsqueeze(-1).float()
            pooled = (hidden * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
            x = self.dropout(pooled)
            return self.classifier(x)

    return (TransferTextClassifier,)


@app.cell
def _(mo):
    freeze_backbone_checkbox = mo.ui.checkbox(
        value=True,
        label="Freeze the pretrained DistilBERT backbone (feature extraction). "
              "Uncheck to fully fine-tune it too — much slower on CPU.",
    )
    freeze_backbone_checkbox
    return (freeze_backbone_checkbox,)


@app.cell
def _(mo):
    transfer_epochs_slider = mo.ui.slider(
        start=1, stop=8, step=1, value=4, label="Transfer model — training epochs"
    )
    transfer_epochs_slider
    return (transfer_epochs_slider,)


@app.cell
def _(
    BERT_HIDDEN,
    DEVICE,
    NUM_CLASSES,
    TransferTextClassifier,
    bert_backbone,
    bert_train_loader,
    bert_val_loader,
    fit,
    freeze_backbone_checkbox,
    nn,
    torch,
    transfer_epochs_slider,
):
    transfer_model = TransferTextClassifier(
        bert_backbone, BERT_HIDDEN, NUM_CLASSES, freeze_backbone=freeze_backbone_checkbox.value
    ).to(DEVICE)
    transfer_criterion = nn.CrossEntropyLoss()
    _trainable_params = [p for p in transfer_model.parameters() if p.requires_grad]
    _lr = 1e-3 if freeze_backbone_checkbox.value else 2e-5
    transfer_optimizer = torch.optim.Adam(_trainable_params, lr=_lr)
    transfer_history = fit(
        transfer_model, bert_train_loader, bert_val_loader, DEVICE,
        transfer_criterion, transfer_optimizer, transfer_epochs_slider.value, model_name="transfer",
    )
    return transfer_history, transfer_model


@app.cell
def _(plot_history, transfer_history):
    fig_transfer_hist = plot_history(transfer_history, "Transfer learning model (DistilBERT)")
    fig_transfer_hist
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Evaluating the transfer learning model
    """)
    return


@app.cell
def _(
    DEVICE,
    LABEL_NAMES,
    accuracy_score,
    bert_test_loader,
    classification_report,
    collect_predictions,
    transfer_model,
):
    transfer_y_true, transfer_y_pred = collect_predictions(transfer_model, bert_test_loader, DEVICE)
    transfer_test_acc = accuracy_score(transfer_y_true, transfer_y_pred)
    transfer_report = classification_report(
        transfer_y_true, transfer_y_pred, target_names=LABEL_NAMES, digits=3
    )
    print(f"Transfer learning model test accuracy: {transfer_test_acc:.3f}\n")
    print(transfer_report)
    return transfer_test_acc, transfer_y_pred, transfer_y_true


@app.cell
def _(LABEL_NAMES, plot_confusion, transfer_y_pred, transfer_y_true):
    fig_transfer_cm = plot_confusion(
        transfer_y_true, transfer_y_pred, LABEL_NAMES, "Transfer model — confusion matrix"
    )
    fig_transfer_cm
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 4. Comparing the two approaches
    """)
    return


@app.cell
def _(custom_model, custom_test_acc, pl, transfer_model, transfer_test_acc):
    comparison_df = pl.DataFrame({
        "model": ["Custom (from scratch)", "Transfer learning (DistilBERT)"],
        "test_accuracy": [custom_test_acc, transfer_test_acc],
        "trainable_params": [
            sum(p.numel() for p in custom_model.parameters() if p.requires_grad),
            sum(p.numel() for p in transfer_model.parameters() if p.requires_grad),
        ],
        "total_params": [
            sum(p.numel() for p in custom_model.parameters()),
            sum(p.numel() for p in transfer_model.parameters()),
        ],
    })
    comparison_df
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 5. Using the models on new text
    """)
    return


@app.cell
def _(mo):
    sample_input = mo.ui.text_area(
        value="The central bank raised interest rates amid fears of inflation.",
        label="Enter a sentence to classify:",
    )
    sample_input
    return (sample_input,)


@app.cell
def _(
    DEVICE,
    LABEL_NAMES,
    bert_collate,
    custom_collate,
    custom_model,
    id2label,
    pl,
    predict_single,
    sample_input,
    transfer_model,
):
    custom_pred_label, custom_probs = predict_single(
        custom_model, sample_input.value, custom_collate, DEVICE, id2label
    )
    transfer_pred_label, transfer_probs = predict_single(
        transfer_model, sample_input.value, bert_collate, DEVICE, id2label
    )
    usage_df = pl.DataFrame({
        "label": LABEL_NAMES,
        "custom_model_prob": custom_probs.tolist(),
        "transfer_model_prob": transfer_probs.tolist(),
    })
    return custom_pred_label, transfer_pred_label, usage_df


@app.cell
def _(custom_pred_label, mo, transfer_pred_label):
    mo.md(f"""
    **Custom model (from scratch) prediction:** `{custom_pred_label}`  \n"
        f"**Transfer learning (DistilBERT) prediction:** `{transfer_pred_label}`
    """)
    return


@app.cell
def _(usage_df):
    usage_df
    return


@app.cell
def _():
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
