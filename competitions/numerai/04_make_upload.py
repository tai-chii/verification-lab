# -*- coding: utf-8 -*-
"""
04_make_upload.py  Numerai の「Model Uploads」用の .pkl を作る（毎日 Numerai 側で自動実行される）
使い方: python3 ~/ワークスペース/検証/verification-lab/competitions/numerai/04_make_upload.py [small|medium|xerxes60|fn|xerxes60_medium|xerxes60_medium_fn]
  xerxes60_medium_fn = 上の medium モデルの予測を、エラごとに small 42本の特徴量で 50% 中和したもの（10 の K と同じ計算。
    10 で「保留」→ live で TAICHI_MD（I）と並べて比べるための別枠用。2026-10-10 追加）
  xerxes60_medium = 08 で学習した target_xerxes_60・medium 780本のモデル（models/xerxes60_medium_seg*.txt の8本の
    生スコアを合計する。09 で「保留」→ live で small と比べるための別枠用。2026-10-04 追加）
    自己確認は results/upload_check_era1226.parquet（1エラ分）で行い、3.10 で計算した予測と一致するか確かめる
  xerxes60 = 06_target_ensemble.py で採用になった target_xerxes_60 のモデル（small 42本）
  fn = 基準（small）を small 42本の特徴量で 50% 中和したもの（05 の B と同じ。オンボーディングの taichi_fn 用）
出力: uploads/<名前>_predict.pkl → numer.ai のモデルのページから「Upload model」でアップロード
  - **Python の版を Numerai の環境（既定は 3.12）に合わせて作ること**。2026-10-03、3.11 で作った .pkl を 3.12 の環境で
    実行して「SystemError: unknown opcode 0」で失敗した（関数の中身が Python の版ごとに違うため）。
    作り方: conda activate numerai312（下の手順で作った 3.12 の環境）で、このスクリプトを実行する
  - 制限（公式）: 1 CPU・4GB RAM・10分。small 特徴量の LightGBM 2000本なら十分収まる
  - 一度上げれば Mac を閉じていても毎日提出される。API キーも要らない
"""
import os, sys, pickle, platform
import pandas as pd, cloudpickle
HERE = os.path.dirname(os.path.abspath(__file__))
FS = (sys.argv[1] if len(sys.argv) > 1 else "small").lower()
NEUTRAL = 0.0
SEGS = None
NEUT_FEATS = None  # 中和に使う特徴量（None なら FEATS と同じ）
if FS in ("xerxes60_medium", "xerxes60_medium_fn"):
    import glob, json, lightgbm as lgb
    FEATS = json.load(open(os.path.join(HERE, "data", "features.json")))["feature_sets"]["medium"]
    SEGS = [lgb.Booster(model_file=f) for f in sorted(glob.glob(os.path.join(HERE, "models", "xerxes60_medium_seg*.txt")))]
    assert len(SEGS) == 8 and sum(b.num_trees() for b in SEGS) == 2000
    MODEL, NAME = None, FS
    if FS == "xerxes60_medium_fn":  # K: small 42本で 50% 中和（small は medium の部分集合ではないので別に持つ）
        NEUTRAL, NEUT_FEATS = 0.5, pickle.load(open(os.path.join(HERE, "models", "baseline_small.pkl"), "rb"))["features"]
elif FS == "fn":
    pk = pickle.load(open(os.path.join(HERE, "models", "baseline_small.pkl"), "rb"))
    MODEL, FEATS, NAME, NEUTRAL = pk["model"], pk["features"], "feature_neutral_small", 0.5
elif FS in ("small", "medium"):
    pk = pickle.load(open(os.path.join(HERE, "models", f"baseline_{FS}.pkl"), "rb"))
    MODEL, FEATS, NAME = pk["model"], pk["features"], f"baseline_{FS}"
else:  # 別ターゲットのモデル（特徴量は small と同じ）
    MODEL = pickle.load(open(os.path.join(HERE, "models", f"{FS}_small.pkl"), "rb"))
    FEATS = pickle.load(open(os.path.join(HERE, "models", "baseline_small.pkl"), "rb"))["features"]
    NAME = f"{FS}_small"


def predict(live_features: pd.DataFrame, live_benchmark_models: pd.DataFrame = None) -> pd.DataFrame:
    import numpy as np
    X = live_features[FEATS]
    if SEGS is not None:  # 分けて学習した木を、生スコアで足し合わせる（08 の採点と同じ）
        p = pd.Series(sum(b.predict(X.values, raw_score=True) for b in SEGS), index=live_features.index)
    else:
        p = pd.Series(MODEL.predict(X), index=live_features.index)
    if NEUTRAL > 0:  # numerai_tools.scoring.neutralize と同じ計算（05 の B を再現）: 順位に対して特徴量＋定数で回帰し、proportion 分を引く
        v = p.rank(pct=True).values
        N = live_features[NEUT_FEATS] if NEUT_FEATS is not None else X
        F = np.hstack([N.values.astype(float), np.ones((len(N), 1))])
        v = v - NEUTRAL * F @ np.linalg.lstsq(F, v, rcond=1e-6)[0]
        p = pd.Series(v, index=live_features.index)
    return p.rank(pct=True).to_frame("prediction")


os.makedirs(os.path.join(HERE, "uploads"), exist_ok=True)
out = os.path.join(HERE, "uploads", f"{NAME}_predict.pkl")
cloudpickle.register_pickle_by_value(sys.modules[__name__]) if __name__ != "__main__" else None
with open(out, "wb") as f:
    cloudpickle.dump(predict, f)
# 自己確認: 読み戻して、validation の先頭1エラで動くか
if SEGS is not None:
    import numpy as np
    va = pd.read_parquet(os.path.join(HERE, "results", "upload_check_era1226.parquet"))
    ref = pd.read_csv(os.path.join(HERE, "results", "upload_check_era1226_pred_py310.csv"), index_col=0).prediction
else:
    va = pd.read_parquet(os.path.join(HERE, "data", "validation.parquet"), columns=["era"] + FEATS)
    va = va[va.era == va.era.iloc[0]]; ref = None
fn = pickle.load(open(out, "rb")); r = fn(va[list(dict.fromkeys(FEATS + (NEUT_FEATS or [])))], None)  # live は全特徴量を持つ
assert list(r.columns) == ["prediction"] and len(r) == len(va) and r.prediction.between(0, 1).all()
if ref is not None:
    if NEUTRAL > 0:  # K は numerai_tools.scoring.neutralize（10 の計算）で作り直して一致を確かめる
        from numerai_tools.scoring import neutralize
        raw = pd.Series(sum(b.predict(va[FEATS].values, raw_score=True) for b in SEGS), index=va.index).rank(pct=True).to_frame("I")
        print(f"確認: 中和前（3.10 の予測）と生スコアの差の最大 {np.abs(raw.I.values - ref.loc[raw.index].values).max():.1e}")
        ref = neutralize(raw, va[NEUT_FEATS], proportion=NEUTRAL)["I"].rank(pct=True)
        print(f"確認: 中和前との順位相関 {r.prediction.corr(raw.I):.4f}（1 なら中和が効いていない）")
    d = np.abs(r.prediction.values - ref.loc[r.index].values).max(); assert d < 1e-9, d
    print(f"自己確認: 参照（{'numerai_tools の neutralize' if NEUTRAL > 0 else '3.10 で計算した予測'}）との差の最大 {d:.1e}")
print(f"作成: {out}（{os.path.getsize(out)/1e6:.1f}MB）/ この Mac の Python {platform.python_version()} → アップロード時に同じ版を選ぶ")
