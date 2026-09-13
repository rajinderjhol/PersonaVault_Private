import ast
import json
import pathlib
import sys
import urllib.request
from collections import defaultdict
from app.main import app

def consecutive_duplicate_segment(path):
    segs = [s for s in path.split("/") if s and not s.startswith("{")]
    for i in range(len(segs) - 1):
        if segs[i] == segs[i + 1]:
            return segs[i]
    return None

def main():
    print("--- API Surface Audit ---")
    routes = []
    
    for r in app.routes:
        if hasattr(r, "path"):
            routes.append(r.path)
            
    # Check for duplicates
    from collections import Counter
    dupes = {p: n for p, n in Counter(routes).items() if n > 1}
    if dupes:
        print("\n❌ Duplicate routes found:")
        for p, n in sorted(dupes.items()):
            print(f"  {n}x {p}")
    else:
        print("\n✅ No duplicate routes.")

    # Check for double-prefix
    double_prefix = [p for p in routes if "/api/v1/api/v1" in p]
    if double_prefix:
        print("\n❌ Double-prefix routes found:")
        for p in double_prefix:
            print(f"  {p}")
    else:
        print("\n✅ No double-prefix routes.")

    # Consecutive duplicates
    dup_seg = [(p, consecutive_duplicate_segment(p)) for p in routes]
    dup_seg = [(p, s) for p, s in dup_seg if s]
    if dup_seg:
        print("\n❌ Consecutive-duplicate-segment paths:")
        for p, s in dup_seg:
            print(f"   [{s}]  {p}")

if __name__ == "__main__":
    main()
