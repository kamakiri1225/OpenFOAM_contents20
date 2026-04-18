# interfaceHeatFlow の熱量計算

## 対象

`system/interfaceHeatFlow` は、`fluid_1` 側の patch
`fluid_1_to_solid_1` から、その mapped patch の相手である
`solid_1:solid_1_to_fluid_1` を取得して、共通面の熱流量を 1 回だけ計算します。

出力される主な値は次の通りです。

```text
Q_fluid_1_to_solid_1[W]
Q_solid_1_to_fluid_1[W]
balance[W]
qAvg_fluid_1_to_solid_1[W/m2]
qAvg_solid_1_to_fluid_1[W/m2]
area[m2]
```

`Q_fluid_1_to_solid_1` と `Q_solid_1_to_fluid_1` は、共通の界面温度を使って両側から別々に計算します。最後に `balance = Q_fluid_1_to_solid_1 + Q_solid_1_to_fluid_1` を出し、熱量が釣り合っているか確認します。

## 記号

面 `i` について、以下の記号を使います。

```text
T_c,i       : local 側、つまり fluid_1 側の patch 隣接セル中心温度
T_nbr,c,i   : neighbour 側、つまり solid_1 側の patch 隣接セル中心温度
k_i         : local 側の熱伝導率または有効熱伝導率
k_nbr,i     : neighbour 側の熱伝導率または有効熱伝導率
delta_i     : local 側の deltaCoeffs
delta_nbr,i : neighbour 側の deltaCoeffs
A_i         : face 面積
```

実装上は、`mappedPatchBase::distribute()` によって neighbour 側の配列を local patch の face 順序に並べ替えています。これにより、`i` 番目の face 同士が同じ共通面を指すようになります。

## プログラムと数式の対応

全体の計算手順を、コードと数式を並べると次のようになります。

| 処理 | コード | 数式・意味 |
| --- | --- | --- |
| local 側 patch を選ぶ | `patchName("fluid_1_to_solid_1")` | local 側は `fluid_1_to_solid_1` |
| mapped patch から相手側を取得 | `mpp.sampleMesh()`, `mpp.samplePolyPatch()` | neighbour 側は `solid_1_to_fluid_1` |
| local 側セル中心温度 | `Tc = bc.patchInternalField()` | \(T_{c,i}\) |
| neighbour 側セル中心温度 | `TcNbr = nbrBc.patchInternalField()` | \(T_{nbr,c,i}\) |
| neighbour 側の face 順序合わせ | `mpp.distribute(TcNbr)` | \(T_{nbr,c,i}\) を local 側 face `i` に対応させる |
| local 側コンダクタンス | `KDelta = bc.kappa(bc)*patch.deltaCoeffs()` | \(K_{\Delta,i}=k_i\delta_i\) |
| neighbour 側コンダクタンス | `KDeltaNbr = nbrBc.kappa(nbrBc)*nbrPatch.deltaCoeffs()` | \(K_{\Delta,nbr,i}=k_{nbr,i}\delta_{nbr,i}\) |
| neighbour 側の face 順序合わせ | `mpp.distribute(KDeltaNbr)` | \(K_{\Delta,nbr,i}\) を local 側 face `i` に対応させる |
| 界面温度 | `Tinterface = (KDelta*Tc + KDeltaNbr*TcNbr)/(KDelta + KDeltaNbr + ROOTVSMALL)` | \(T_{I,i}=\frac{K_{\Delta,i}T_{c,i}+K_{\Delta,nbr,i}T_{nbr,c,i}}{K_{\Delta,i}+K_{\Delta,nbr,i}}\) |
| local から neighbour への face 熱流束 | `qLocalToNbr = KDelta*(Tc - Tinterface)` | \(q_{local\to nbr,i}=K_{\Delta,i}(T_{c,i}-T_{I,i})\) |
| neighbour から local への face 熱流束 | `qNbrToLocal = KDeltaNbr*(TcNbr - Tinterface)` | \(q_{nbr\to local,i}=K_{\Delta,nbr,i}(T_{nbr,c,i}-T_{I,i})\) |
| face 面積 | `magSf = patch.magSf()` | \(A_i\) |
| 合計面積 | `area = gSum(magSf)` | \(A=\sum_i A_i\) |
| local から neighbour への積分熱量 | `QLocal = gSum(qLocalToNbr*magSf)` | \(Q_{local\to nbr}=\sum_i q_{local\to nbr,i} A_i\) |
| neighbour から local への積分熱量 | `QNbr = gSum(qNbrToLocal*magSf)` | \(Q_{nbr\to local}=\sum_i q_{nbr\to local,i} A_i\) |
| 面平均熱流束 | `qAvgLocal = QLocal/max(area, SMALL)` | \(\bar{q}_{local\to nbr}=Q_{local\to nbr}/A\) |
| 相手側の面平均熱流束 | `qAvgNbr = QNbr/max(area, SMALL)` | \(\bar{q}_{nbr\to local}=Q_{nbr\to local}/A\) |
| 収支確認 | `balance = QLocal + QNbr` | \(balance=Q_{local\to nbr}+Q_{nbr\to local}\) |

この表の通り、neighbour 側の温度とコンダクタンスは必ず `mpp.distribute()` で local 側の face 順序にそろえてから使います。これをしないと、`fluid_1` 側の face `i` と `solid_1` 側の face `i` が同じ場所を指す保証がなくなり、面ごとの熱流束計算がずれます。

## 各側の面コンダクタンス

OpenFOAM の `deltaCoeffs` は、おおまかに壁面から隣接セル中心までの距離の逆数です。

したがって、各側の面コンダクタンスを次のように置いています。

```math
K_{\Delta,i} = k_i \delta_i
```

```math
K_{\Delta,nbr,i} = k_{nbr,i} \delta_{nbr,i}
```

コードでは次に対応します。

```cpp
const scalarField KDelta(bc.kappa(bc)*patch.deltaCoeffs());
scalarField KDeltaNbr(nbrBc.kappa(nbrBc)*nbrPatch.deltaCoeffs());
mpp.distribute(KDeltaNbr);
```

ここで `bc.kappa(bc)` と `nbrBc.kappa(nbrBc)` は、`compressible::turbulentTemperatureRadCoupledMixed` の `kappaMethod` に従って各側の熱伝導率を評価します。このケースでは境界条件が `kappaMethod fluidThermo` なので、その region の thermo/turbulence から `kappa` または `kappaEff` を取得します。

## 界面温度

界面温度 \(T_{I,i}\) は、両側の熱流束が釣り合うように決めます。local 側から界面へ向かう熱流束を

```math
q_{local\to I,i} = K_{\Delta,i}(T_{c,i}-T_{I,i})
```

neighbour 側から界面へ向かう熱流束を

```math
q_{nbr\to I,i} = K_{\Delta,nbr,i}(T_{nbr,c,i}-T_{I,i})
```

と置きます。界面で熱量が保存される条件は、

```math
q_{local\to I,i} + q_{nbr\to I,i} = 0
```

です。これを \(T_{I,i}\) について解くと、

```math
T_{I,i}
=
\frac{K_{\Delta,i}T_{c,i}+K_{\Delta,nbr,i}T_{nbr,c,i}}
{K_{\Delta,i}+K_{\Delta,nbr,i}}
```

コードではゼロ割りを避けるため、分母に `ROOTVSMALL` を足しています。

```cpp
const scalarField Tinterface
(
    (KDelta*Tc + KDeltaNbr*TcNbr)
   /(KDelta + KDeltaNbr + ROOTVSMALL)
);
```

## 面ごとの熱流束

界面温度を使って、fluid 側から solid 側へ向かう熱流束を次のように計算します。

```math
q_{local\to nbr,i} = K_{\Delta,i}(T_{c,i}-T_{I,i})
```

solid 側から fluid 側へ向かう熱流束は、neighbour 側の式で別に計算します。

```math
q_{nbr\to local,i} = K_{\Delta,nbr,i}(T_{nbr,c,i}-T_{I,i})
```

単位は次の通りです。

```text
K_Delta : W/(m2 K)
T差   : K
q     : W/m2
```

コードでは次に対応します。

```cpp
const scalarField Tc(bc.patchInternalField());
scalarField TcNbr(nbrBc.patchInternalField());
mpp.distribute(TcNbr);

const scalarField Tinterface
(
    (KDelta*Tc + KDeltaNbr*TcNbr)
   /(KDelta + KDeltaNbr + ROOTVSMALL)
);

const scalarField qLocalToNbr(KDelta*(Tc - Tinterface));
const scalarField qNbrToLocal(KDeltaNbr*(TcNbr - Tinterface));
```

この符号定義では、`fluid_1` 側セル中心温度が界面温度より高いとき `qLocalToNbr > 0`、つまり `fluid_1 -> solid_1` 方向の熱流束が正になります。逆に `solid_1` 側セル中心温度が界面温度より高いとき `qNbrToLocal > 0`、つまり `solid_1 -> fluid_1` 方向が正になります。

## 面積積分した熱量

共通面全体の熱量は、面ごとの熱流束に面積を掛けて総和します。

```math
Q_{local\to nbr} = \sum_i q_{local\to nbr,i} A_i
```

```math
Q_{nbr\to local} = \sum_i q_{nbr\to local,i} A_i
```

コードでは次に対応します。

```cpp
const scalarField magSf(patch.magSf());
const scalar QLocal = gSum(qLocalToNbr*magSf);
const scalar QNbr = gSum(qNbrToLocal*magSf);
```

合計面積は、

```math
A = \sum_i A_i
```

コードでは、

```cpp
const scalar area = gSum(magSf);
```

です。

## 面平均熱流束

面平均熱流束は、面積積分した熱量を合計面積で割って計算しています。

```math
\bar{q}_{local\to nbr} = \frac{Q_{local\to nbr}}{A}
```

```math
\bar{q}_{nbr\to local} = \frac{Q_{nbr\to local}}{A}
```

コードではゼロ割りを避けるため、分母を `max(area, SMALL)` にしています。

```cpp
const scalar qAvgLocal = QLocal/max(area, SMALL);
const scalar qAvgNbr = QNbr/max(area, SMALL);
```

## 熱量収支

以前の実装では `QNbr = -QLocal` としていましたが、それでは一致を仮定しているだけでした。現在の実装では、`Q_fluid_1_to_solid_1` と `Q_solid_1_to_fluid_1` をそれぞれ独立に面積積分し、最後に収支を計算します。

```math
balance = Q_{local\to nbr} + Q_{nbr\to local}
```

コードでは次に対応します。

```cpp
const scalar balance = QLocal + QNbr;
```

この `balance[W]` が 0 に近ければ、両側から独立に計算した熱量が釣り合っていると判断できます。

## wallHeatFlux との違い

`wallHeatFlux` は各 region の壁面境界場から熱流束を評価します。一方、`interfaceHeatFlow` は共通面の両側セル中心温度と両側の `kappa*deltaCoeffs` から、1 つの合成コンダクタンスを作って熱量を計算します。

そのため、`wallHeatFlux` の `fluid_1_to_solid_1` と `solid_1_to_fluid_1` が数値的に一致しない場合でも、`interfaceHeatFlow` では同じ界面温度を使って両側の熱流束を別々に評価するため、

```math
Q_{fluid_1 \to solid_1} + Q_{solid_1 \to fluid_1} = 0
```

になります。

## 注意点

この計算は、温度境界条件 `compressible::turbulentTemperatureRadCoupledMixed` の内部実装を完全に再現するものではありません。特に `thermalInertia`、radiation、thin layer の効果を境界条件と同じ形で再実装しているわけではありません。

目的は、共通面を 1 つの interface として扱い、両側で同じ熱量になるかを確認することです。そのため、両側に別々の `wallHeatFlux` を計算させるのではなく、共通の界面温度を求めてから `fluid_1 -> solid_1` と `solid_1 -> fluid_1` の熱量を別々に計算し、最後に `balance` を出力しています。
