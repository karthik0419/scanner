import pandas as pd
import numpy as np


def generate_report(trades, output_csv="backtest_results.csv"):
    if not trades:
        print("No trades to report.")
        return pd.DataFrame()

    df = pd.DataFrame(trades)
    df.to_csv(output_csv, index=False)

    total = len(df)
    wins = (df["result"] == "WIN").sum()
    losses = (df["result"] == "LOSS").sum()
    win_rate = wins / total * 100 if total > 0 else 0

    avg_win = df.loc[df["result"] == "WIN", "pnl_pct"].mean() if wins else 0
    avg_loss = df.loc[df["result"] == "LOSS", "pnl_pct"].mean() if losses else 0
    avg_pnl = df["pnl_pct"].mean()

    gross_profit = df.loc[df["pnl_pct"] > 0, "pnl_pct"].sum()
    gross_loss = abs(df.loc[df["pnl_pct"] < 0, "pnl_pct"].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    # Max drawdown (equity curve)
    equity = (1 + df["pnl_pct"] / 100).cumprod()
    peak = equity.cummax()
    drawdown = ((equity - peak) / peak * 100).min()

    print("\n" + "=" * 60)
    print("BACKTEST REPORT")
    print("=" * 60)
    print(f"Total Trades    : {total}")
    print(f"Wins            : {wins}  ({win_rate:.1f}%)")
    print(f"Losses          : {losses}  ({100 - win_rate:.1f}%)")
    print(f"Avg Win         : +{avg_win:.2f}%")
    print(f"Avg Loss        : {avg_loss:.2f}%")
    print(f"Avg P&L / Trade : {avg_pnl:.2f}%")
    print(f"Profit Factor   : {profit_factor:.2f}")
    print(f"Max Drawdown    : {drawdown:.2f}%")

    # --- By Pattern ---
    print("\n--- By Pattern ---")
    pat = (
        df.groupby("pattern")
        .apply(
            lambda g: pd.Series(
                {
                    "Trades": len(g),
                    "Wins": (g["result"] == "WIN").sum(),
                    "Win%": f"{(g['result'] == 'WIN').mean()*100:.1f}%",
                    "Avg P&L": f"{g['pnl_pct'].mean():.2f}%",
                    "Best": f"{g['pnl_pct'].max():.2f}%",
                    "Worst": f"{g['pnl_pct'].min():.2f}%",
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )
    print(pat.to_string(index=False))

    # --- By Exit Reason ---
    print("\n--- By Exit Reason ---")
    ex = (
        df.groupby("exit_reason")
        .apply(
            lambda g: pd.Series(
                {
                    "Trades": len(g),
                    "Avg P&L": f"{g['pnl_pct'].mean():.2f}%",
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )
    print(ex.to_string(index=False))

    print(f"\nFull results saved to: {output_csv}")
    return df
