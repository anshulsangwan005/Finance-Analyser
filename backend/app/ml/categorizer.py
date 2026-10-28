"""Transaction categorization: TF-IDF (word + char n-grams) + Logistic Regression."""
import re
from pathlib import Path

import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer

from .synth_data import generate

MODEL_PATH = Path(__file__).parent / "model.joblib"
NOISE = {"upi", "pos", "neft", "imps", "txn", "ref", "payment", "debit", "card", "pvt", "ltd", "to", "okaxis",
         "oksbi", "okhdfcbank", "ybl", "paytm", "order", "bill", "app", "online"}
_model = None


def clean(text: str) -> str:
    t = text.lower()
    t = re.sub(r"@\w+", " ", t)
    t = re.sub(r"\d+", " ", t)
    t = re.sub(r"[^a-z&\s]", " ", t)
    return " ".join(w for w in t.split() if w not in NOISE)


def _build() -> Pipeline:
    feats = FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True)),
    ])
    return Pipeline([("tfidf", feats), ("clf", LogisticRegression(max_iter=2000, C=8, class_weight="balanced"))])


def train(save: bool = True, verbose: bool = False) -> dict:
    texts, labels = generate()
    X = [clean(t) for t in texts]
    Xtr, Xte, ytr, yte = train_test_split(X, labels, test_size=0.2, random_state=1, stratify=labels)
    model = _build().fit(Xtr, ytr)
    pred = model.predict(Xte)
    metrics = {"macro_f1": round(f1_score(yte, pred, average="macro"), 4), "n_test": len(yte)}
    if verbose:
        print(classification_report(yte, pred))
    final = _build().fit(X, labels)  # refit on everything
    if save:
        joblib.dump(final, MODEL_PATH)
    global _model
    _model = final
    return metrics


def get_model() -> Pipeline:
    global _model
    if _model is None:
        if MODEL_PATH.exists():
            _model = joblib.load(MODEL_PATH)
        else:
            train()
    return _model


def predict(descriptions: list[str], rules: dict[str, str] | None = None) -> list[tuple[str, float]]:
    """Return (category, confidence). User rules (merchant keyword -> category) take priority."""
    rules = rules or {}
    cleaned = [clean(d) for d in descriptions]
    out: list[tuple[str, float]] = []
    probs = get_model().predict_proba(cleaned) if cleaned else []
    classes = get_model().classes_ if cleaned else []
    for c, p in zip(cleaned, probs):
        hit = next((cat for kw, cat in rules.items() if kw and kw in c), None)
        if hit:
            out.append((hit, 1.0))
            continue
        i = int(p.argmax())
        conf = float(p[i])
        out.append((str(classes[i]) if conf >= 0.25 else "Other", round(conf, 3)))
    return out


def merchant_keyword(description: str) -> str:
    """First two meaningful words of the cleaned description, used for user correction rules."""
    return " ".join(clean(description).split()[:2])
