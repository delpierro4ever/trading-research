import pandas as pd, engine as E, analysis as A
pd.set_option("display.width", 250); pd.set_option("display.float_format", "{:.3f}".format)
ctx = A.Ctx(["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "JP225"])
for s in ("S1", "S2", "S3"):
    pos, res = A.run(ctx, s)
    print(s); print(A.table(pos, res, "DEV")[["cagr", "vol", "sharpe", "gross_sharpe", "maxdd", "cost_ann", "fin_ann", "turnover"]])
