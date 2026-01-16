# ステップ5: フェード追加 - 調査結果

**調査日**: 2026-01-13
**結論**: DaVinci Resolve Scripting APIにはTransition追加機能が存在しないため、スキップ

---

## Sample.xmlの分析

XMLエクスポートでは、Cross Dissolveトランジションは**クリップとは独立した `<transitionitem>` 要素**として表現されている：

```xml
<transitionitem>
    <rate>
        <timebase>30</timebase>
        <ntsc>FALSE</ntsc>
    </rate>
    <start>654</start>
    <end>660</end>
    <alignment>center</alignment>
    <effect>
        <name>Cross Dissolve</name>
        <effectid>Cross Dissolve</effectid>
        <effecttype>transition</effecttype>
        <mediatype>video</mediatype>
        <effectcategory>Dissolve</effectcategory>
        <startratio>0</startratio>
        <endratio>1</endratio>
        <reverse>FALSE</reverse>
    </effect>
    <name>Transition</name>
</transitionitem>
```

### 主要な発見

- トランジションはクリップ間に配置される独立要素
- Opacityは各クリップで固定値100（フェード用ではなく静的な値）
- alignment属性:
  - `center`: クリップ間のトランジション
  - `end-black`: 黒へフェードアウト

---

## 試行した方法（失敗）

### 試行1: SetProperty("FadeIn"/"FadeOut")
```python
item.SetProperty("FadeIn", FADE_FRAMES)
item.SetProperty("FadeOut", FADE_FRAMES)
```
**結果**: 動作せず

### 試行2: SetProperty("videoFadeIn"/"videoFadeOut")
```python
item.SetProperty("videoFadeIn", FADE_FRAMES)
item.SetProperty("videoFadeOut", FADE_FRAMES)
```
**結果**: 動作せず

---

## APIドキュメント調査

### 公式APIドキュメント（README.txt）

「Looking up Timeline item properties」セクションでサポートされているSetPropertyのキー一覧：

- Pan, Tilt, ZoomX, ZoomY, ZoomGang, RotationAngle
- AnchorPointX, AnchorPointY, Pitch, Yaw
- FlipX, FlipY, CropLeft, CropRight, CropTop, CropBottom
- CropSoftness, CropRetain, DynamicZoomEase, CompositeMode
- Opacity, Distortion, RetimeProcess, MotionEstimation
- Scaling, ResizeFilter

**Fade関連のプロパティは公式ドキュメントに記載なし**

### オンラインドキュメント調査

| ソース | 結果 |
|--------|------|
| extremraym.com | Transition/Fade APIは存在しない |
| Blackmagic Forum | 「APIでTransitionは追加できない」と確認 |
| Unofficial DaVinciResolve-API-Docs | Transition関連メソッドなし |
| DaVinci Resolve API Doc v20.3 (GitHub Gist) | Transition/Fade記載なし |

### Blackmagic Forum の投稿

> "I got clips loaded onto a timeline successfully, but hitting a blocker with adding cross-dissolve transitions between timeline items. I can't find anything in the documentation or online that shows how to do transitions."
>
> "Is this not possible with the scripting API?"

投稿者は最終的に「DaVinci Resolveを諦めてFFmpegを使用した」と報告。

---

## 代替アプローチの検討

### 1. Fusion Composition + キーフレーム

**理論的には可能**

- `TimelineItem.AddFusionComp()` でFusion compを追加
- Merge nodeのBlendパラメータをキーフレームでアニメーション
- 0→1（フェードイン）、1→0（フェードアウト）

**課題**:
- 複雑な実装が必要
- Fusion APIの詳細な理解が必要
- 各クリップにFusion compを追加する必要があり、処理時間が長くなる可能性

### 2. クリップ重ね合わせ + Opacity

- 2つのトラックにクリップを配置し、Opacityをアニメーション
- 現在の仕様（単一トラック内での分割）とは異なるアプローチ

### 3. 手動でTransition追加

- スクリプトでクリップ分割後、UI上で手動でTransitionを追加
- 確実だが自動化の目的に反する

---

## 最終決定

**フェード機能はスキップ**

理由:
1. DaVinci Resolve Scripting APIにTransition追加機能が存在しない
2. 代替アプローチ（Fusion）は複雑すぎる
3. 主要機能（クリップ分割）は正常に動作している

---

## 参考リンク

- [Blackmagic Forum - Video transitions with scripting API](https://forum.blackmagicdesign.com/viewtopic.php?f=21&t=189135)
- [DaVinci Resolve Scripting API Doc v20.3](https://gist.github.com/X-Raym/2f2bf453fc481b9cca624d7ca0e19de8)
- [Unofficial DaVinci Resolve API Docs](https://deric.github.io/DaVinciResolve-API-Docs/)
- [DaVinci Resolve Scripting API Documentation - by X-Raym](https://extremraym.com/cloud/resolve-scripting-doc/)
