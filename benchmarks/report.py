#!/usr/bin/env python3
import json
from pathlib import Path


def main() -> None:
    data = json.loads(Path("results.json").read_text())
    print("# AstraOS Benchmark Report\n")
    print("| Metric | Before | After | Improvement |")
    print("|---|---:|---:|---:|")
    for item in data["metrics"]:
        before = item["before"]
        after = item["after"]
        if item["name"] == "AI Inference" or after > before:
            improvement = (after - before) / before * 100
            label = f"{improvement:.1f}% higher"
        else:
            improvement = (before - after) / before * 100
            label = f"{improvement:.1f}% lower"
        print(f"| {item['name']} | {before} {item['unit']} | {after} {item['unit']} | {label} |")


if __name__ == "__main__":
    main()
