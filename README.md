# OpenFOAM_contents20

技術書典20 向けの OpenFOAM 解析ケースファイルです。

## ケース一覧

### 001_snappyMultiRegionHeater

snappyHexMesh を用いた共役熱伝達（CHT）解析のチュートリアルケースです。

- **ソルバー**: chtMultiRegionFoam
- **メッシュ**: snappyHexMesh
- **領域**: bottomAir / topAir / heater / leftSolid / rightSolid

### 002_Uthermal

熱抵抗（U値）を考慮した共役熱伝達解析ケースです。

- **ソルバー**: chtMultiRegionFoam
- **メッシュ**: blockMesh + topoSet
- **領域**: fluid_1 / fluid_2 / solid_1 / solid_2
- `ana001_base` : 計算実行前のベースケース
- `ana001_run` : 計算設定済みケース（計算結果は含まれていません）

### 003_heatsink

ヒートシンクの共役熱伝達解析ケースです。

- **ソルバー**: chtMultiRegionFoam
- **メッシュ**: snappyHexMesh
- **3D モデル**: FreeCAD (model/model.FCStd)
- `ana001_base` : 計算実行前のベースケース
- `ana001_chtMultiRegionFoam` : 計算設定済みケース（計算結果は含まれていません）

## 使い方

各ケースディレクトリに移動して `Allrun` スクリプトを実行してください。

```bash
cd 001_snappyMultiRegionHeater
./Allrun
```

## 注意事項

- 計算結果（タイムステップディレクトリ、processor、postProcessing 等）はリポジトリに含まれていません
- 各自の環境で計算を実行してください

## ライセンス

本リポジトリの内容は技術書典20の書籍に関連するものです。
