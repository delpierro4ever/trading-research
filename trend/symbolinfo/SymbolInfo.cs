using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using cAlgo.API;
using cAlgo.API.Internals;
namespace cAlgo.Robots {
  [Robot(AccessRights = AccessRights.FullAccess)]
  public class SymbolInfo : Robot {
    static string J(string s) { return "\"" + (s ?? "").Replace("\\", "\\\\").Replace("\"", "\\\"") + "\""; }
    static string N(double d) { return double.IsNaN(d) || double.IsInfinity(d) ? "null" : d.ToString("R", System.Globalization.CultureInfo.InvariantCulture); }
    protected override void OnStart() {
      var sb = new StringBuilder();
      sb.Append("{\"account\":{\"currency\":" + J(Account.Asset.Name) + ",\"balance\":" + N(Account.Balance) + ",\"leverage\":" + N(Account.PreciseLeverage) + "},\n");
      var all = new List<string>(); for (int i = 0; i < Symbols.Count; i++) all.Add(Symbols[i].ToString());
      sb.Append("\"all_names\":[" + string.Join(",", all.Select(J)) + "],\n\"symbols\":{\n");
      var cands = "EURUSD GBPUSD USDJPY AUDUSD USDCAD USDCHF NZDUSD EURJPY GBPJPY EURGBP AUDJPY EURCHF XAUUSD XAGUSD US500 US30 USTEC DE40 UK100 JP225 XTIUSD XBRUSD XNGUSD BTCUSD ETHUSD".Split(' ').ToList();
      // also any non-FX names that look like bonds / other
      foreach (var n in all) if (!cands.Contains(n) && (n.Contains("Bund") || n.Contains("Bond") || n.Contains("TNote") || n.Contains("Gilt") || n.Contains("BUND") || n.Contains("BOND"))) cands.Add(n);
      bool isFirst = true;
      foreach (var name in cands) {
        Symbol s = null;
        try { s = Symbols.GetSymbol(name); } catch (Exception e) { Print("ERR " + name + " " + e.Message); }
        if (s == null) { Print("MISSING " + name); continue; }
        if (!isFirst) sb.Append(",\n"); isFirst = false;
        sb.Append(J(name) + ":{");
        sb.Append("\"name\":" + J(s.Name) + ",\"desc\":" + J(s.Description) + ",\"base\":" + J(s.BaseAsset?.Name) + ",\"quote\":" + J(s.QuoteAsset?.Name));
        sb.Append(",\"digits\":" + s.Digits + ",\"pip_size\":" + N(s.PipSize) + ",\"pip_value\":" + N(s.PipValue) + ",\"tick_size\":" + N(s.TickSize) + ",\"tick_value\":" + N(s.TickValue));
        sb.Append(",\"lot_size\":" + N(s.LotSize) + ",\"vol_min\":" + N(s.VolumeInUnitsMin) + ",\"vol_step\":" + N(s.VolumeInUnitsStep) + ",\"vol_max\":" + N(s.VolumeInUnitsMax));
        sb.Append(",\"bid\":" + N(s.Bid) + ",\"ask\":" + N(s.Ask) + ",\"spread\":" + N(s.Spread) + ",\"spread_pips\":" + N(s.Spread / s.PipSize));
        sb.Append(",\"commission\":" + N(s.Commission) + ",\"commission_type\":" + J(s.CommissionType.ToString()));
        sb.Append(",\"swap_long\":" + N(s.SwapLong) + ",\"swap_short\":" + N(s.SwapShort) + ",\"swap_calc\":" + J(s.SwapCalculationType.ToString()) + ",\"swap_3day\":" + J(s.Swap3DaysRollover.ToString()));
        try { sb.Append(",\"leverage_tiers\":[" + string.Join(",", s.DynamicLeverage.Select(t => "{\"vol\":" + N(t.Volume) + ",\"lev\":" + N(t.Leverage) + "}")) + "]"); } catch (Exception e) { sb.Append(",\"leverage_tiers_err\":" + J(e.Message)); }
        try { sb.Append(",\"margin_1lot_units\":" + N(s.GetEstimatedMargin(TradeType.Buy, s.VolumeInUnitsMin))); } catch (Exception e) { sb.Append(",\"margin_err\":" + J(e.Message)); }
        try { sb.Append(",\"market_open\":" + (s.MarketHours.IsOpened() ? "true" : "false")); sb.Append(",\"sessions\":[" + string.Join(",", s.MarketHours.Sessions.Select(x => J(x.StartDay + " " + x.StartTime + " -> " + x.EndDay + " " + x.EndTime))) + "]"); } catch (Exception e) { sb.Append(",\"hours_err\":" + J(e.Message)); }
        try { sb.Append(",\"trading_mode\":" + J(s.TradingMode.ToString())); } catch { }
        sb.Append("}");
      }
      sb.Append("\n}}");
      System.IO.File.WriteAllText("/mnt/Robots/symbolinfo.json", sb.ToString());
      Print("wrote symbolinfo.json with " + (all.Count) + " names");
      Stop();
    }
  }
}
