"""
build_notebook.py
-----------------
Builds notebooks/retail_sales_analysis.ipynb from notebooks/notebook_cells.py
and executes every cell, embedding text, tables and charts as outputs.
(You can also just open the .ipynb in Jupyter / VS Code / Colab and Run All.)

Run:  python scripts/build_notebook.py
"""

import ast
import base64
import contextlib
import io
import json
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NB_DIR = ROOT / "notebooks"
sys.path.insert(0, str(NB_DIR))
from notebook_cells import CELLS  # noqa: E402

os.chdir(NB_DIR)  # notebook uses ../data paths
ns = {}
cells = []
exec_count = 0


def rich(obj):
    if isinstance(obj, (pd.DataFrame, pd.Series)):
        frame = obj.to_frame() if isinstance(obj, pd.Series) else obj
        return {"text/html": frame.to_html(), "text/plain": obj.to_string()}
    return {"text/plain": repr(obj)}


for kind, src in CELLS:
    if kind == "md":
        cells.append({"cell_type": "markdown", "metadata": {}, "source": src.splitlines(True)})
        continue
    exec_count += 1
    outputs = []
    buf = io.StringIO()

    def flush():
        if buf.getvalue():
            outputs.append({"output_type": "stream", "name": "stdout", "text": buf.getvalue().splitlines(True)})
            buf.seek(0); buf.truncate()

    def show(*a, **k):
        flush()
        for num in plt.get_fignums():
            fig = plt.figure(num)
            png = io.BytesIO(); fig.savefig(png, format="png", bbox_inches="tight")
            outputs.append({"output_type": "display_data", "metadata": {},
                            "data": {"image/png": base64.b64encode(png.getvalue()).decode(),
                                     "text/plain": "<Figure>"}})
        plt.close("all")

    def display(obj):
        flush()
        outputs.append({"output_type": "display_data", "metadata": {}, "data": rich(obj)})

    plt.show = show
    ns["display"] = display
    tree = ast.parse(src)
    last = tree.body[-1] if tree.body and isinstance(tree.body[-1], ast.Expr) else None
    body = tree.body[:-1] if last else tree.body
    with contextlib.redirect_stdout(buf):
        exec(compile(ast.Module(body, []), "<cell>", "exec"), ns)
        value = eval(compile(ast.Expression(last.value), "<cell>", "eval"), ns) if last else None
    flush()
    if value is not None:
        outputs.append({"output_type": "execute_result", "execution_count": exec_count,
                        "metadata": {}, "data": rich(value)})
    cells.append({"cell_type": "code", "execution_count": exec_count, "metadata": {},
                  "outputs": outputs, "source": src.splitlines(True)})

nb = {"cells": cells, "nbformat": 4, "nbformat_minor": 5,
      "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                   "language_info": {"name": "python"}}}
out = NB_DIR / "retail_sales_analysis.ipynb"
out.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"Built {out.relative_to(ROOT)} with {len(cells)} cells ({exec_count} executed)")
