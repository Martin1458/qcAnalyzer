import tkinter as tk
from tkinter import ttk, messagebox
import json
import pathlib
from collections import Counter

from .chart_frame import ChartFrame

DIRECTIONS = ["up", "left", "right", "down"]


def _load_data(base_dir):
    base_dir = pathlib.Path(base_dir)

    qc_path = base_dir / "qc_options.json"
    filled_path = base_dir / "image_filled.json"
    recorded_path = base_dir / "recorded.txt"

    if not qc_path.exists():
        raise FileNotFoundError("qc_options.json not found")
    with open(qc_path, encoding="utf-8") as f:
        qc_options = json.load(f)

    image_filled = {}
    if filled_path.exists():
        with open(filled_path, encoding="utf-8") as f:
            image_filled = json.load(f)

    combo_for_id = {}
    for r_dir in DIRECTIONS:
        for c_dir in DIRECTIONS:
            qc_id = image_filled.get(r_dir, {}).get(c_dir)
            if qc_id:
                combo_for_id[qc_id] = f"{r_dir}+{c_dir}"

    timeline = []
    if recorded_path.exists():
        with open(recorded_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",")
                if len(parts) != 2:
                    continue
                a, b = parts
                qc_id = image_filled.get(a, {}).get(b)
                msg = qc_options.get(qc_id, f"Unknown ({a},{b})")
                timeline.append((msg, a, b))

    counts = Counter(msg for msg, _, _ in timeline)

    layout_ids = set()
    for r in image_filled.values():
        for qc_id in r.values():
            if qc_id:
                layout_ids.add(qc_id)
    layout_phrases = {qc_options[i] for i in layout_ids if i in qc_options}

    never_used = [p for p in layout_phrases if counts.get(p, 0) == 0]
    rarely_used = [p for p in layout_phrases if counts.get(p, 0) == 1]
    unmapped = [p for p in qc_options.values() if p not in layout_phrases]

    return {
        "timeline": timeline,          # list of (msg, dir_a, dir_b)
        "counts": counts,
        "qc_options": qc_options,
        "image_filled": image_filled,
        "combo_for_id": combo_for_id,
        "never_used": sorted(never_used),
        "rarely_used": sorted(rarely_used),
        "unmapped": sorted(unmapped),
    }


class AnalysisTab(ttk.Frame):
    def __init__(self, parent, base_dir):
        super().__init__(parent)
        self._base_dir = pathlib.Path(base_dir)
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Top bar
        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))
        ttk.Button(top, text="Refresh / Load Data", command=self.load_and_render).pack(side="left")
        self._info_label = ttk.Label(top, text="Click Refresh to load data.")
        self._info_label.pack(side="left", padx=10)

        # Vertical PanedWindow — user can drag the sashes to resize sections
        pane = ttk.PanedWindow(self, orient=tk.VERTICAL)
        pane.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # --- Pane 1: Charts notebook ---
        chart_outer = ttk.Frame(pane)
        chart_outer.columnconfigure(0, weight=1)
        chart_outer.rowconfigure(0, weight=1)
        pane.add(chart_outer, weight=3)

        chart_nb = ttk.Notebook(chart_outer)
        chart_nb.grid(row=0, column=0, sticky="nsew")

        self._bar_frame = ChartFrame(chart_nb, figsize=(9, 4))
        self._pie_frame = ChartFrame(chart_nb, figsize=(9, 4))
        self._heat_frame = ChartFrame(chart_nb, figsize=(9, 4))
        self._cumul_frame = ChartFrame(chart_nb, figsize=(9, 4))
        self._rank_frame = ChartFrame(chart_nb, figsize=(9, 4))

        chart_nb.add(self._bar_frame,   text="  Bar Chart  ")
        chart_nb.add(self._pie_frame,   text="  Pie Chart  ")
        chart_nb.add(self._heat_frame,  text="  D-Pad Heatmap  ")
        chart_nb.add(self._cumul_frame, text="  Cumulative  ")
        chart_nb.add(self._rank_frame,  text="  Top vs Unused  ")

        # --- Pane 2: Usage table ---
        table_frame = ttk.LabelFrame(pane, text="Usage Table")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        pane.add(table_frame, weight=2)

        cols = ("chat", "count", "pct", "combo")
        self._tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=6)
        self._tree.heading("chat",  text="Quick Chat",  command=lambda: self._sort("chat"))
        self._tree.heading("count", text="Count",       command=lambda: self._sort("count"))
        self._tree.heading("pct",   text="% of Total",  command=lambda: self._sort("pct"))
        self._tree.heading("combo", text="D-Pad Combo", command=lambda: self._sort("combo"))
        self._tree.column("chat",  width=260)
        self._tree.column("count", width=70,  anchor="center")
        self._tree.column("pct",   width=80,  anchor="center")
        self._tree.column("combo", width=110, anchor="center")
        self._tree.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")
        self._sort_col = "count"
        self._sort_reverse = True

        # --- Pane 3: Recommendations ---
        rec_frame = ttk.LabelFrame(pane, text="Recommendations")
        rec_frame.columnconfigure(0, weight=1)
        rec_frame.rowconfigure(0, weight=1)
        pane.add(rec_frame, weight=1)

        self._rec_text = tk.Text(rec_frame, state="disabled", wrap="word",
                                 font=("Consolas", 10))
        self._rec_text.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        rec_sb = ttk.Scrollbar(rec_frame, orient="vertical", command=self._rec_text.yview)
        self._rec_text.configure(yscrollcommand=rec_sb.set)
        rec_sb.grid(row=0, column=1, sticky="ns")

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def load_and_render(self):
        try:
            data = _load_data(self._base_dir)
        except FileNotFoundError as e:
            messagebox.showwarning("Missing File", str(e))
            return
        except Exception as e:
            messagebox.showerror("Load Error", str(e))
            return

        total = sum(data["counts"].values())
        self._info_label.config(
            text=f"{total} total chats recorded across {len(data['timeline'])} events."
        )

        self._render_bar(data)
        self._render_pie(data)
        self._render_heatmap(data)
        self._render_cumulative(data)
        self._render_rank(data)
        self._render_table(data)
        self._render_recommendations(data)

    # ------------------------------------------------------------------
    # Charts
    # ------------------------------------------------------------------

    def _no_data(self, frame):
        frame.clear()
        ax = frame.fig.add_subplot(111)
        ax.text(0.5, 0.5, "No data yet", ha="center", va="center", transform=ax.transAxes)
        frame.draw()

    def _render_bar(self, data):
        self._bar_frame.clear()
        counts = data["counts"]
        if not counts:
            return self._no_data(self._bar_frame)

        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        labels = [msg[:26] for msg, _ in sorted_counts]
        values = [cnt for _, cnt in sorted_counts]

        ax = self._bar_frame.fig.add_subplot(111)
        colors = ["#4C9BE8" if v > 1 else "#AAAAAA" for v in values]
        bars = ax.barh(labels, values, color=colors)
        ax.bar_label(bars, padding=3, fontsize=8)
        ax.set_xlabel("Times Used")
        ax.set_title("Quick Chat Usage — sorted by frequency (grey = used only once)")
        ax.invert_yaxis()
        self._bar_frame.fig.tight_layout()
        self._bar_frame.draw()

    def _render_pie(self, data):
        self._pie_frame.clear()
        counts = data["counts"]
        if not counts:
            return self._no_data(self._pie_frame)

        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        top_n = 8
        slices = list(sorted_counts[:top_n])
        other_total = sum(v for _, v in sorted_counts[top_n:])
        if other_total:
            slices.append(("Other", other_total))

        labels = [s[0][:20] for s in slices]
        sizes  = [s[1] for s in slices]

        ax = self._pie_frame.fig.add_subplot(111)
        wedges, texts, autotexts = ax.pie(
            sizes, labels=None, autopct="%1.0f%%", startangle=140,
            pctdistance=0.82
        )
        ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1),
                  fontsize=8)
        ax.set_title("Quick Chat Distribution (Top 8)")
        self._pie_frame.fig.tight_layout()
        self._pie_frame.draw()

    def _render_heatmap(self, data):
        """4×4 grid coloured by how often each d-pad combo was used."""
        self._heat_frame.clear()
        image_filled = data["image_filled"]
        counts = data["counts"]
        qc_options = data["qc_options"]

        if not image_filled:
            return self._no_data(self._heat_frame)

        import numpy as np
        grid = np.zeros((4, 4))
        labels = [["" for _ in DIRECTIONS] for _ in DIRECTIONS]

        for ri, r_dir in enumerate(DIRECTIONS):
            for ci, c_dir in enumerate(DIRECTIONS):
                qc_id = image_filled.get(r_dir, {}).get(c_dir)
                phrase = qc_options.get(qc_id, "") if qc_id else ""
                cnt = counts.get(phrase, 0)
                grid[ri][ci] = cnt
                short = phrase[:14] if phrase else "—"
                labels[ri][ci] = f"{short}\n({cnt})"

        ax = self._heat_frame.fig.add_subplot(111)
        im = ax.imshow(grid, cmap="YlOrRd", aspect="auto")
        self._heat_frame.fig.colorbar(im, ax=ax, label="Uses")

        ax.set_xticks(range(4))
        ax.set_yticks(range(4))
        ax.set_xticklabels([f"2nd: {d}" for d in DIRECTIONS], fontsize=9)
        ax.set_yticklabels([f"1st: {d}" for d in DIRECTIONS], fontsize=9)
        ax.set_title("D-Pad Combo Heatmap — brighter = used more")

        for ri in range(4):
            for ci in range(4):
                ax.text(ci, ri, labels[ri][ci], ha="center", va="center",
                        fontsize=7, color="black")

        self._heat_frame.fig.tight_layout()
        self._heat_frame.draw()

    def _render_cumulative(self, data):
        """Cumulative uses over time for the top-5 quick chats."""
        self._cumul_frame.clear()
        timeline = data["timeline"]
        if not timeline:
            return self._no_data(self._cumul_frame)

        counts = data["counts"]
        top5 = [msg for msg, _ in counts.most_common(5)]
        cumul = {msg: [] for msg in top5}
        running = {msg: 0 for msg in top5}

        for msg, _, _ in timeline:
            for t in top5:
                if msg == t:
                    running[t] += 1
                cumul[t].append(running[t])

        ax = self._cumul_frame.fig.add_subplot(111)
        x = list(range(1, len(timeline) + 1))
        for msg in top5:
            ax.plot(x, cumul[msg], label=msg[:22], linewidth=1.8)

        ax.set_xlabel("Chat # (chronological)")
        ax.set_ylabel("Cumulative uses")
        ax.set_title("Cumulative Usage Over Time — Top 5 Quick Chats")
        ax.legend(fontsize=8, loc="upper left")
        self._cumul_frame.fig.tight_layout()
        self._cumul_frame.draw()

    def _render_rank(self, data):
        """Side-by-side: top 5 most used vs never/rarely used."""
        self._rank_frame.clear()
        counts = data["counts"]
        never = data["never_used"]
        rarely = data["rarely_used"]

        ax1, ax2 = self._rank_frame.fig.subplots(1, 2)

        # Left: top used
        top = counts.most_common(6)
        if top:
            t_labels = [m[:20] for m, _ in top]
            t_vals   = [v for _, v in top]
            bars = ax1.barh(t_labels, t_vals, color="#4C9BE8")
            ax1.bar_label(bars, padding=2, fontsize=8)
            ax1.invert_yaxis()
        ax1.set_title("Most Used")
        ax1.set_xlabel("Count")

        # Right: candidates for replacement
        weak = [(p, counts.get(p, 0)) for p in never + rarely]
        weak.sort(key=lambda x: x[1])
        if weak:
            w_labels = [m[:20] for m, _ in weak]
            w_vals   = [v for _, v in weak]
            colors   = ["#E84C4C" if v == 0 else "#E8A84C" for v in w_vals]
            bars2 = ax2.barh(w_labels, w_vals, color=colors)
            ax2.bar_label(bars2, padding=2, fontsize=8)
            ax2.invert_yaxis()
            ax2.set_xlim(0, max(w_vals or [1]) + 1)
        else:
            ax2.text(0.5, 0.5, "All chats used!", ha="center", va="center",
                     transform=ax2.transAxes)
        ax2.set_title("Replace Candidates")
        ax2.set_xlabel("Count")

        self._rank_frame.fig.suptitle("Best vs Worst Performing Slots", fontsize=11)
        self._rank_frame.fig.tight_layout()
        self._rank_frame.draw()

    # ------------------------------------------------------------------
    # Table
    # ------------------------------------------------------------------

    def _render_table(self, data):
        for row in self._tree.get_children():
            self._tree.delete(row)

        counts = data["counts"]
        qc_options = data["qc_options"]
        image_filled = data["image_filled"]
        total = sum(counts.values()) or 1

        phrase_combo = {}
        for r_dir in DIRECTIONS:
            for c_dir in DIRECTIONS:
                qc_id = image_filled.get(r_dir, {}).get(c_dir)
                if qc_id and qc_id in qc_options:
                    phrase_combo[qc_options[qc_id]] = f"{r_dir}+{c_dir}"

        all_phrases = set(phrase_combo.keys()) | set(counts.keys())
        rows = []
        for phrase in all_phrases:
            cnt   = counts.get(phrase, 0)
            pct   = f"{cnt / total * 100:.1f}%"
            combo = phrase_combo.get(phrase, "—")
            rows.append((phrase, cnt, pct, combo))

        rows.sort(key=lambda r: r[1], reverse=True)
        for phrase, cnt, pct, combo in rows:
            self._tree.insert("", "end", values=(phrase, cnt, pct, combo))

    def _sort(self, col):
        if self._sort_col == col:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_col = col
            self._sort_reverse = col == "count"

        rows = [(self._tree.set(child, col), child) for child in self._tree.get_children("")]
        try:
            rows.sort(
                key=lambda x: float(x[0].rstrip("%")) if col in ("count", "pct") else x[0].lower(),
                reverse=self._sort_reverse,
            )
        except ValueError:
            rows.sort(key=lambda x: x[0].lower(), reverse=self._sort_reverse)

        for idx, (_, child) in enumerate(rows):
            self._tree.move(child, "", idx)

    # ------------------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------------------

    def _render_recommendations(self, data):
        lines = []

        if data["never_used"]:
            lines.append("NEVER USED — consider replacing these slots:")
            for p in data["never_used"]:
                lines.append(f"  • {p}")
            lines.append("")

        if data["rarely_used"]:
            lines.append("RARELY USED (only 1 time) — consider replacing:")
            for p in data["rarely_used"]:
                lines.append(f"  • {p}")
            lines.append("")

        if data["unmapped"]:
            lines.append("NOT IN YOUR LAYOUT — you might want to add these:")
            for p in data["unmapped"]:
                lines.append(f"  • {p}")
            lines.append("")

        if not lines:
            lines.append("All your quick chats are in use — great layout!")

        self._rec_text.config(state="normal")
        self._rec_text.delete("1.0", "end")
        self._rec_text.insert("end", "\n".join(lines))
        self._rec_text.config(state="disabled")
