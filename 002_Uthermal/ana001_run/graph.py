import matplotlib
matplotlib.use("Agg")

import pandas as pd
import matplotlib.pyplot as plt
from glob import glob
from pathlib import Path

output_dir = Path("png")
output_dir.mkdir(exist_ok=True)

pdf_dir = Path("pdf")
pdf_dir.mkdir(exist_ok=True)


# ============================================================
# 残差の確認
# ============================================================

def plot_fluid_residual(file_path, label, ymin=1e-12, ymax=1):
    df = pd.read_csv(
        file_path,
        comment="#",
        sep=r"\s+",
        header=None,
        names=[
            "Time", "U_solver",
            "Ux_initial", "Ux_final", "Ux_iters",
            "Uy_initial", "Uy_final", "Uy_iters", "U_converged",
            "h_solver", "h_initial", "h_final", "h_iters", "h_converged",
            "p_rgh_solver", "p_rgh_initial", "p_rgh_final", "p_rgh_iters", "p_rgh_converged",
        ],
        engine="python"
    )
    plt.figure(figsize=(8, 5))
    plt.plot(df["Time"], df["Ux_final"], label="Ux_final")
    plt.plot(df["Time"], df["Uy_final"], label="Uy_final")
    plt.plot(df["Time"], df["h_final"], label="h_final")
    plt.plot(df["Time"], df["p_rgh_final"], label="p_rgh_final")
    plt.yscale("log")
    plt.ylim(ymin, ymax)
    plt.xlabel("Time [s]")
    plt.ylabel("Final residual")
    plt.title(label)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    out = output_dir / f"residual_{label}.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")


def plot_solid_residual(file_path, label, ymin=1e-12, ymax=1):
    df = pd.read_csv(
        file_path,
        comment="#",
        sep=r"\s+",
        header=None,
        names=["Time", "h_solver", "h_initial", "h_final", "h_iters", "h_converged"],
        engine="python"
    )
    plt.figure(figsize=(8, 5))
    plt.plot(df["Time"], df["h_final"], label="h_final")
    plt.yscale("log")
    plt.ylim(ymin, ymax)
    plt.xlabel("Time [s]")
    plt.ylabel("Final residual")
    plt.title(label)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    out = output_dir / f"residual_{label}.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")


plot_fluid_residual("postProcessing/fluid_1/residuals_fluid_1/0/solverInfo.dat", "fluid_1")
plot_fluid_residual("postProcessing/fluid_2/residuals_fluid_2/0/solverInfo.dat", "fluid_2")
plot_solid_residual("postProcessing/solid_1/residuals_solid_1/0/solverInfo.dat", "solid_1")
plot_solid_residual("postProcessing/solid_2/residuals_solid_2/0/solverInfo.dat", "solid_2")


# ============================================================
# 熱量の比較（qInt 全ファイル）
# ============================================================

def read_surface_field_value(filepath):
    p = Path(filepath)
    if not p.exists():
        print(f"[WARNING] File not found: {filepath}")
        return None
    df = pd.read_csv(
        filepath,
        comment="#",
        sep=r"\s+",
        header=None,
        names=["Time", "Value"],
        engine="python"
    )
    zero_row = pd.DataFrame({"Time": [0.0], "Value": [0.0]})
    return pd.concat([zero_row, df], ignore_index=True)

files = sorted(glob("postProcessing/*/qInt_*/0/surfaceFieldValue.dat"))

if files:
    plt.figure(figsize=(10, 6))
    for f in files:
        df = read_surface_field_value(f)
        if df is None:
            continue
        p = Path(f)
        label = f"{p.parts[1]} : {p.parts[2]}"
        y = -df["Value"] if "/fluid_" in f.replace("\\", "/") else df["Value"]
        plt.plot(df["Time"], y, label=label)
    plt.xlabel("Time [s]")
    plt.ylabel("Integrated wallHeatFlux [W]")
    plt.title("Comparison of all qInt histories")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    out = output_dir / "qInt_all_auto.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")


# ============================================================
# qInt（指定順・絶対値）
# ============================================================

plt.rcParams["font.size"] = 14
plt.rcParams["axes.titlesize"] = 16
plt.rcParams["axes.labelsize"] = 14
plt.rcParams["legend.fontsize"] = 12
plt.rcParams["xtick.labelsize"] = 12
plt.rcParams["ytick.labelsize"] = 12

qint_targets = [
    ("fluid_1 : qInt_fluid_1_to_solid_1",
     "postProcessing/fluid_1/qInt_fluid_1_to_solid_1/0/surfaceFieldValue.dat"),
    ("solid_1 : qInt_solid_1_to_fluid_1",
     "postProcessing/solid_1/qInt_solid_1_to_fluid_1/0/surfaceFieldValue.dat"),
    ("solid_1 : qInt_solid_1_to_fluid_2",
     "postProcessing/solid_1/qInt_solid_1_to_fluid_2/0/surfaceFieldValue.dat"),
    ("fluid_2 : qInt_fluid_2_to_solid_1",
     "postProcessing/fluid_2/qInt_fluid_2_to_solid_1/0/surfaceFieldValue.dat"),
    ("fluid_2 : qInt_fluid_2_to_solid_2",
     "postProcessing/fluid_2/qInt_fluid_2_to_solid_2/0/surfaceFieldValue.dat"),
    ("solid_2 : qInt_solid_2_to_fluid_2",
     "postProcessing/solid_2/qInt_solid_2_to_fluid_2/0/surfaceFieldValue.dat"),
]

plt.figure(figsize=(10, 6))
for label, filepath in qint_targets:
    df = read_surface_field_value(filepath)
    if df is None:
        continue
    plt.plot(df["Time"], df["Value"].abs(), label=label)
plt.xlabel("Time [s]")
plt.ylabel("Integrated wallHeatFlux [W]")
plt.title("Comparison of all qInt histories (absolute value)")
plt.grid(True)
plt.legend()
plt.tight_layout()
out = output_dir / "qInt_all_histories.png"
plt.savefig(out, dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {out}")


# ============================================================
# qAvg（指定順・絶対値）
# ============================================================

qavg_targets = [
    ("fluid_1 : qAvg_fluid_1_to_solid_1",
     "postProcessing/fluid_1/qAvg_fluid_1_to_solid_1/0/surfaceFieldValue.dat"),
    ("solid_1 : qAvg_solid_1_to_fluid_1",
     "postProcessing/solid_1/qAvg_solid_1_to_fluid_1/0/surfaceFieldValue.dat"),
    ("solid_1 : qAvg_solid_1_to_fluid_2",
     "postProcessing/solid_1/qAvg_solid_1_to_fluid_2/0/surfaceFieldValue.dat"),
    ("fluid_2 : qAvg_fluid_2_to_solid_1",
     "postProcessing/fluid_2/qAvg_fluid_2_to_solid_1/0/surfaceFieldValue.dat"),
    ("fluid_2 : qAvg_fluid_2_to_solid_2",
     "postProcessing/fluid_2/qAvg_fluid_2_to_solid_2/0/surfaceFieldValue.dat"),
    ("solid_2 : qAvg_solid_2_to_fluid_2",
     "postProcessing/solid_2/qAvg_solid_2_to_fluid_2/0/surfaceFieldValue.dat"),
]

plt.figure(figsize=(10, 6))
for label, filepath in qavg_targets:
    df = read_surface_field_value(filepath)
    if df is None:
        continue
    plt.plot(df["Time"], df["Value"].abs(), label=label)
plt.xlabel("Time [s]")
plt.ylabel("Area-averaged wallHeatFlux [W/m²]")
plt.title("Comparison of all qAvg histories (absolute value)")
plt.grid(True)
plt.legend()
plt.tight_layout()
out = output_dir / "qAvg_all_histories.png"
plt.savefig(out, dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {out}")


# ============================================================
# interfaceHeatFlow
# ============================================================

interface_file = "postProcessing/interfaceHeatFlow/interfaceHeatFlow.dat"
interface_path = Path(interface_file)

if interface_path.exists():
    df_if = pd.read_csv(
        interface_file,
        comment="#",
        sep=r"\s+",
        header=None,
        names=[
            "time",
            "Q_fluid_1_to_solid_1", "Q_solid_1_to_fluid_1",
            "balance",
            "qAvg_fluid_1_to_solid_1", "qAvg_solid_1_to_fluid_1",
            "area"
        ],
        engine="python"
    )

    plt.figure(figsize=(8, 5))
    plt.plot(df_if["time"], df_if["Q_fluid_1_to_solid_1"], label="Q_fluid_1_to_solid_1")
    plt.plot(df_if["time"], -df_if["Q_solid_1_to_fluid_1"], label="Q_solid_1_to_fluid_1", linestyle="--")
    plt.xlabel("Time [s]")
    plt.ylabel("Heat flow [W]")
    plt.title("Comparison of heat flow history")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    out = output_dir / "interfaceHeatFlow.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")


# ============================================================
# qInt + interfaceHeatFlow 統合プロット
# ============================================================

plt.rcParams["font.size"] = 20
plt.rcParams["axes.titlesize"] = 24
plt.rcParams["axes.labelsize"] = 22
plt.rcParams["legend.fontsize"] = 18
plt.rcParams["xtick.labelsize"] = 18
plt.rcParams["ytick.labelsize"] = 18

combined_targets = [
    ("fluid_1 : qInt_fluid_1_to_solid_1",
     "postProcessing/fluid_1/qInt_fluid_1_to_solid_1/0/surfaceFieldValue.dat"),
    ("solid_1 : qInt_solid_1_to_fluid_1",
     "postProcessing/solid_1/qInt_solid_1_to_fluid_1/0/surfaceFieldValue.dat"),
]

plt.figure(figsize=(12, 8))

for label, filepath in combined_targets:
    df = read_surface_field_value(filepath)
    if df is None:
        continue
    plt.plot(df["Time"], df["Value"].abs(), label=label, linewidth=2.5)

if interface_path.exists():
    plt.plot(
        df_if["time"],
        (-df_if["Q_fluid_1_to_solid_1"]).abs(),
        label="interfaceHeatFlow : -Q_fluid_1_to_solid_1",
        linestyle="--", linewidth=2.5
    )
    plt.plot(
        df_if["time"],
        df_if["Q_solid_1_to_fluid_1"].abs(),
        label="interfaceHeatFlow : Q_solid_1_to_fluid_1",
        linestyle=":", linewidth=2.5
    )

plt.xlabel("Time [s]")
plt.ylabel("Heat flow [W]")
plt.title("Comparison of qInt and interfaceHeatFlow histories")
plt.grid(True)
plt.legend()
plt.tight_layout()

out_png = output_dir / "all_heatflow_histories_one_plot.png"
out_pdf = pdf_dir / "all_heatflow_histories_one_plot.pdf"
plt.savefig(out_png, dpi=300, bbox_inches="tight")
plt.savefig(out_pdf, bbox_inches="tight")
plt.close()
print(f"Saved: {out_png}")
print(f"Saved: {out_pdf}")
