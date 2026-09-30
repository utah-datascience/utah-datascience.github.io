#!/usr/bin/env python3
"""Suggest topic tags for talk records from a small controlled vocabulary.

Tags are what the /talks/ page filters on, so they are kept to a short, stable
list (see VOCABULARY below) rather than free-form keywords. This script scores
each talk's title and abstract against the vocabulary and writes the winners
into the `tags` field of its TOML record.

It only fills in records whose `tags` are empty, so hand-picked tags are never
clobbered; pass --overwrite to re-tag everything.

Usage:
    python3 scripts/tag_talks.py                 # fill in missing tags
    python3 scripts/tag_talks.py --dry-run       # show what it would do
    python3 scripts/tag_talks.py --report        # tag counts across the corpus
    python3 scripts/tag_talks.py --overwrite     # re-tag every record
"""

from __future__ import annotations

import argparse
import collections
import glob
import os
import re
import sys
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "_data", "talks")

MAX_TAGS = 4  # a talk with a dozen tags is not searchable, it is noise

# tag -> patterns that suggest it. Patterns are matched case-insensitively on
# word boundaries against the title (weighted x3) and the abstract.
VOCABULARY: dict[str, list[str]] = {
    "machine learning": [
        "machine learning", "supervised learning", "unsupervised", "classifier",
        "classification", "random forests?", "boosting", "training data",
        "generalization", "few-shot", "transfer learning", "reinforcement learning",
    ],
    "deep learning": [
        "deep learning", "deep neural", "neural networks?", "transformers?",
        "convolutional", "autoencoders?", "diffusion models?", "embeddings?",
        "backpropagation", "gradient descent",
    ],
    "large language models": [
        "large language models?", "\\bllms?\\b", "\\bgpt\\b", "foundation models?",
        "chatgpt", "prompt(ing|s)?", "generative ai", "instruction(-| )tuning",
        "\\bagentic\\b", "\\bagents?\\b",
    ],
    "natural language processing": [
        "natural language", "\\bnlp\\b", "language models?", "text (classification|data)",
        "question answering", "semantic parsing", "summari(z|s)ation", "translation",
        "word (vectors?|representations?|embeddings?)", "linguistic",
    ],
    "computer vision": [
        "computer vision", "image (classification|recognition|generation|data)",
        "object detection", "segmentation", "visual recognition", "\\bpixels?\\b",
        "video", "multimodal",
    ],
    "robotics": [
        "robots?", "robotic", "manipulation", "autonomous (vehicles?|driving|navigation)",
        "grasping", "sim-to-real", "embodied",
    ],
    "visualization": [
        "visuali(z|s)ation", "visual analytics", "charts?", "dashboards?",
        "\\bplots?\\b", "data stories", "narrative visuali", "topological features",
    ],
    "human-centered computing": [
        "human-cent(er|re)ed", "human-computer", "\\bhci\\b", "user study",
        "participants", "interface", "usability", "human-ai", "crowdworkers?",
        "designers?", "practitioners?",
    ],
    "statistics": [
        "statistical", "statistics", "regression", "bayesian", "hypothesis",
        "estimators?", "confidence intervals?", "semiparametric", "sampling",
        "probabilit(y|ies)", "\\bp-values?\\b",
    ],
    "causal inference": [
        "causal", "counterfactuals?", "treatment effects?", "confounding",
        "instrumental variables?", "\\bdo-calculus\\b",
    ],
    "optimization": [
        "optimi(z|s)ation", "convex", "minimax", "stochastic gradient",
        "linear programming", "objective function", "\\bsolvers?\\b",
    ],
    "algorithms & theory": [
        "algorithms?", "approximation", "computational complexity", "\\bnp-hard\\b",
        "streaming", "sublinear", "\\bbounds?\\b", "\\bproofs?\\b", "theoretical guarantees?",
        "clustering", "sketching",
    ],
    "networks & graphs": [
        "graphs?", "hypergraphs?", "networks? (analysis|science|structure)",
        "social networks?", "community detection", "\\bnodes? and edges?\\b",
        "graph neural", "homophily",
    ],
    "data management": [
        "databases?", "\\bsql\\b", "quer(y|ies)", "data (integration|discovery|cleaning|quality|wrangling|pipelines?)",
        "tables?", "data lakes?", "\\betl\\b", "schema",
    ],
    "fairness & ethics": [
        "fairness", "\\bfair\\b", "\\bbias(es|ed)?\\b", "ethics", "ethical", "equity",
        "equitable", "discrimination", "responsible (ai|use)", "justice", "accountability",
    ],
    "privacy & security": [
        "privacy", "differential privacy", "security", "adversarial (attacks?|examples?|robustness)",
        "encrypt(ed|ion)", "\\bprivate\\b", "de-?identif",
    ],
    "health & medicine": [
        "clinical", "patients?", "health(care)?", "medical", "medicine", "diseases?",
        "cancer", "epidemiolog", "psychiatry", "diagnos(is|tic)", "drug discovery",
        "public health", "mental health",
    ],
    "biology & genomics": [
        "genom(e|ic|ics)", "\\bgenes?\\b", "proteins?", "\\bcells?\\b", "biolog",
        "bioinformatics", "\\brna\\b", "\\bdna\\b", "single-cell", "neuroscience", "\\bbrain\\b",
    ],
    "climate & environment": [
        "climate", "environmental", "air quality", "weather", "atmospheric",
        "water (quality|crisis)", "pollution", "sustainab", "wildfires?", "hazards?",
        "earth observation", "ecolog",
    ],
    "physics & astronomy": [
        "astronom", "cosmolog", "galax(y|ies)", "\\bphysics\\b", "quantum",
        "telescopes?", "\\bdark (energy|matter)\\b", "x-ray", "materials science",
        "partial differential equations?", "\\bpdes?\\b", "simulations? of",
    ],
    "geospatial": [
        "geospatial", "\\bgis\\b", "remote sensing", "satellite", "spatial (data|analysis)",
        "land (cover|use)", "urban", "mapping",
    ],
    "education": [
        "education", "students?", "teaching", "classrooms?", "curricul(um|a)",
        "learning analytics", "instructors?", "\\bcourses?\\b", "\\bk-12\\b",
    ],
    "society & policy": [
        "polic(y|ies)", "social (science|media)", "society", "societal", "economics?",
        "government", "elections?", "crisis informatics", "misinformation",
        "communit(y|ies)", "civic",
    ],
}

COMPILED = {
    tag: [re.compile(rf"\b(?:{pattern})", re.I) for pattern in patterns]
    for tag, patterns in VOCABULARY.items()
}


def score_tags(title: str, abstract: str, bio: str = "") -> list[str]:
    """Title matches count triple; abstracts carry the topic; bios are a weak hint."""
    scores: dict[str, int] = {}
    for tag, patterns in COMPILED.items():
        hits = 0
        for pattern in patterns:
            hits += 3 * len(pattern.findall(title))
            hits += len(pattern.findall(abstract))
            hits += len(pattern.findall(bio))
        if hits:
            scores[tag] = hits
    if not scores:
        return []
    # keep the strongest signals, and drop long-tail matches from a single word
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    best = ranked[0][1]
    kept = [tag for tag, hits in ranked[:MAX_TAGS] if hits >= 2 or hits == best]
    return sorted(kept)


def render_tags(tags: list[str]) -> str:
    return "tags = [" + ", ".join(f'"{tag}"' for tag in tags) + "]"


def write_tags(path: str, tags: list[str]) -> None:
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    line = render_tags(tags)
    if re.search(r"^tags = .*$", text, re.M):
        text = re.sub(r"^tags = .*$", line, text, count=1, flags=re.M)
    elif re.search(r"^canceled = .*$", text, re.M):
        text = re.sub(r"^(canceled = .*)$", r"\1\n" + line, text, count=1, flags=re.M)
    else:  # last resort: append to the end of the [talk] table
        text = re.sub(r"(\n\n\[\[speakers\]\])", "\n" + line + r"\1", text, count=1)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="print, do not write")
    parser.add_argument("--overwrite", action="store_true", help="re-tag records that already have tags")
    parser.add_argument("--report", action="store_true", help="print tag counts and exit")
    args = parser.parse_args()

    counts: collections.Counter[str] = collections.Counter()
    untagged, updated = [], 0

    for path in sorted(glob.glob(os.path.join(DATA_DIR, "*.toml"))):
        if os.path.basename(path).startswith("_"):
            continue
        with open(path, "rb") as handle:
            record = tomllib.load(handle)
        talk = record.get("talk", {})
        existing = talk.get("tags") or []
        if existing and not args.overwrite:
            counts.update(existing)
            continue

        abstract = str(talk.get("abstract", ""))
        bios = " ".join(str(s.get("bio", "")) for s in record.get("speakers", []))
        tags = score_tags(str(talk.get("title", "")), abstract, bios)
        counts.update(tags)
        if not tags:
            untagged.append(os.path.basename(path))
        if args.dry_run or args.report:
            if args.dry_run:
                print(f"{os.path.basename(path)}: {', '.join(tags) or '(none)'}")
            continue
        write_tags(path, tags)
        updated += 1

    if args.report or args.dry_run:
        print("\ntag counts:")
        for tag, count in counts.most_common():
            print(f"  {count:4d}  {tag}")
        print(f"\n{len(untagged)} record(s) with no tag")
        for name in untagged[:15]:
            print(f"  {name}")
        return 0

    print(f"tagged {updated} record(s) using {len(VOCABULARY)} tags")
    if untagged:
        print(f"{len(untagged)} record(s) matched nothing and were left untagged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
