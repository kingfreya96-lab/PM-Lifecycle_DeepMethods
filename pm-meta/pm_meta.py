#!/usr/bin/env python3
"""
pm_meta.py - Search PM method meta-index by scene, keyword, or method name.

Usage:
    python3 pm_meta.py --scene "验证"
    python3 pm_meta.py --keyword "interview"
    python3 pm_meta.py --method "opportunity-solution-tree"
    python3 pm_meta.py --scene "衡量" --detail
    python3 pm_meta.py --list-scenes
"""

import argparse
import json
import sys
from pathlib import Path

INDEX_PATH = Path(__file__).parent / "index.json"


def load_index():
    if not INDEX_PATH.exists():
        print(f"Error: {INDEX_PATH} not found")
        sys.exit(1)
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def search_by_scene(data, scene, detail=False):
    results = [m for m in data["methods"] if scene in m["scene"]]
    if not results:
        print(f"No methods found for scene: {scene}")
        return
    print(f"\n=== 场景「{scene}」：{len(results)} 个方法 ===\n")
    for m in results:
        if detail:
            lib_full = data["libraries"][m["library"]]["full_name"]
            print(f"  {m['name_cn']}（{m['name']}）")
            print(f"    摘要：{m['summary']}")
            print(f"    来源：{lib_full}")
            print()
        else:
            print(f"  {m['name_cn']}（{m['name']}）— {m['summary']} [{m['library']}]")


def search_by_keyword(data, keyword, detail=False):
    kw = keyword.lower()
    results = [m for m in data["methods"]
               if kw in m["name"].lower() or kw in m["name_cn"] or kw in m["summary"]]
    if not results:
        print(f"No methods found for keyword: {keyword}")
        return
    print(f"\n=== 关键词「{keyword}」：{len(results)} 个方法 ===\n")
    for m in results:
        if detail:
            lib_full = data["libraries"][m["library"]]["full_name"]
            print(f"  {m['name_cn']}（{m['name']}）")
            print(f"    场景：{m['scene']}")
            print(f"    摘要：{m['summary']}")
            print(f"    来源：{lib_full}")
            print()
        else:
            print(f"  {m['name_cn']}（{m['name']}）— {m['scene']} | {m['summary']} [{m['library']}]")


def show_method(data, name):
    name_lower = name.lower()
    for m in data["methods"]:
        if m["name"].lower() == name_lower or m["name_cn"] == name:
            lib_full = data["libraries"][m["library"]]["full_name"]
            print(f"\n=== {m['name_cn']}（{m['name']}）===")
            print(f"  场景：{m['scene']}")
            print(f"  摘要：{m['summary']}")
            print(f"  来源：{lib_full}（{m['library']}）")
            return
    print(f"Method not found: {name}")


def list_scenes(data):
    from collections import Counter
    scenes = Counter(m["scene"] for m in data["methods"])
    print("\n=== 场景分类 ===\n")
    for scene, count in scenes.most_common():
        print(f"  {scene}：{count} 个方法")


def main():
    parser = argparse.ArgumentParser(description="PM method meta-index search")
    parser.add_argument("--scene", help="Search by scene (e.g. 验证, 衡量, 策略)")
    parser.add_argument("--keyword", help="Search by keyword in name/summary")
    parser.add_argument("--method", help="Show details of a specific method")
    parser.add_argument("--list-scenes", action="store_true", help="List all scenes")
    parser.add_argument("--detail", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    data = load_index()

    if args.list_scenes:
        list_scenes(data)
    elif args.scene:
        search_by_scene(data, args.scene, args.detail)
    elif args.keyword:
        search_by_keyword(data, args.keyword, args.detail)
    elif args.method:
        show_method(data, args.method)
    else:
        print(f"PM Meta Index: {data['total_methods']} methods from {len(data['libraries'])} libraries")
        print("Use --scene, --keyword, --method, or --list-scenes to search")


if __name__ == "__main__":
    main()