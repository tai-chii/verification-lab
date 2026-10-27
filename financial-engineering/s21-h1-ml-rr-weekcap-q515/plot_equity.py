import pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import kensho_s21_h1_ml_rr_q515 as K, kensho_s21_walkforward_q518 as W
for f in fm.findSystemFonts():
    if "NotoSansCJK-Regular" in f: fm.fontManager.addfont(f)
plt.rcParams["font.family"]="Noto Sans CJK JP"
def curve(path):
    t=pd.read_csv(path,parse_dates=["entry","exit"]); out=[]
    for Y,g in t.groupby("fold"):
        out.append(K.daily(g,W.TS(Y),W.TS(Y+1),g["r"].iloc[0]))
    p=pd.concat(out); return p.cumsum()*100
a=curve("results/trades_q519_W-exp.csv"); b=curve("results/trades_wf_q518.csv"); c=curve("results/trades_q519_W-5y.csv"); e=curve("results/trades_q519_W-exp-mtf.csv"); dde=e-e.cummax()
dd=a-a.cummax()
INK,INK2,GRID,SURF="#0b0b0b","#52514e","#e4e3df","#fcfcfb"; C1,C2,CRIT="#2a78d6","#eb6834","#e34948"
fig,(ax,ax2)=plt.subplots(2,1,figsize=(11,6.6),sharex=True,gridspec_kw=dict(height_ratios=[3,1.1],hspace=0.08),facecolor=SURF)
for x in (ax,ax2):
    x.set_facecolor(SURF); x.grid(axis="y",color=GRID,lw=0.8); x.tick_params(colors=INK2,labelsize=9)
    for s in ["top","right","left"]: x.spines[s].set_visible(False)
    x.spines["bottom"].set_color(GRID)
    for Y in range(2015,2024): x.axvline(pd.Timestamp(f"{Y}-10-01"),color=GRID,lw=0.8,zorder=0)
ax.plot(b.index,b.values,color=C2,lw=2,label="Q518（固定の入る基準 θ）")
ax.plot(c.index,c.values,color="#1baf7a",lw=2,label="Q519 比較（同じ入り方・直近5年だけで学習）")
ax.plot(a.index,a.values,color=C1,lw=2,label="Q519 本体（直近20営業日の上位10%・全期間で学習）")
ax.plot(e.index,e.values,color="#6250d6",lw=2,label="Q521（Q519 本体＋H4/D1 確定足からの乖離）")
ax.annotate(f"{e.iloc[-1]:+.1f}%",(e.index[-1],e.iloc[-1]),xytext=(6,0),textcoords="offset points",color=INK,fontsize=10,va="center")
ax.axhline(0,color=INK2,lw=0.8)
ax.annotate(f"{a.iloc[-1]:+.1f}%",(a.index[-1],a.iloc[-1]),xytext=(6,0),textcoords="offset points",color=INK,fontsize=10,va="center")
ax.annotate(f"{c.iloc[-1]:+.1f}%",(c.index[-1],c.iloc[-1]),xytext=(6,-8),textcoords="offset points",color=INK,fontsize=10,va="center")
ax.annotate(f"{b.iloc[-1]:+.1f}%",(b.index[-1],b.iloc[-1]),xytext=(6,8),textcoords="offset points",color=INK,fontsize=10,va="center")
ax.set_ylabel("累積損益（%・単利）",color=INK2,fontsize=10)
ax.legend(loc="upper left",frameon=False,fontsize=9.5,labelcolor=INK)
ax.set_title("S21 ウォークフォワード：残高の推移（評価年 2014-10〜2023-09・H1・15銘柄・コスト込み）",loc="left",color=INK,fontsize=12,pad=12)
ax2.plot(dd.index,dd.values,color=C1,lw=1.2,label="Q519 本体"); ax2.plot(dde.index,dde.values,color="#6250d6",lw=1.2,label="Q521"); ax2.legend(loc="lower right",frameon=False,fontsize=8.5,ncol=2)
ax2.axhline(-6,color=CRIT,lw=1,ls="--"); ax2.text(dd.index[0],-6,"  関門 −6%",color=INK2,fontsize=8.5,va="bottom")

ax2.set_ylabel("ドローダウン（%）",color=INK2,fontsize=9); ax2.set_ylim(-7.5,0.5)
fig.text(0.01,0.005,"各年はその年より前のデータだけで学習（緑のみ直近5年、他は全期間）。リスクは1トレード0.04〜0.06%（Q519・Q521）・0.04〜0.21%（Q518）。縦線は評価年の区切り（10月）。",color=INK2,fontsize=8.5)
fig.savefig("results/equity_q519_vs_q518.png",dpi=150,bbox_inches="tight",facecolor=SURF)
print(a.iloc[-1],b.iloc[-1],c.iloc[-1],dd.min())
