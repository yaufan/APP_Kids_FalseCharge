# 場景檔：圖和程式共用的約定

每個場景一個 JSON 檔：`app/assets/scenes/<場景>.json`（由 `design/art/` 的程式寫出來，和圖一起產生）。程式靠它組出圖、出題、判斷點對了沒有。

## 圖放在哪裡
- 三種畫風：`a`（等角小模型）、`b`（孔版印刷）、`c`（粗蠟筆童畫）。
- 場景背景：`app/assets/art/<畫風>/<場景>/bg.svg`，`viewBox="0 0 600 600"`（正方形，四邊都畫滿）。
- 每樣東西（和它的每個變化）一個檔：`app/assets/art/<畫風>/<場景>/<art>.svg`，透明底，`viewBox` 的寬高比和它在場景裡的框一樣（框是 `w*600` × `h*600`），東西剛好畫滿框（站在地上的東西，腳底在框的下緣）。
- 變色龍小變：`app/assets/art/<畫風>/chameleon_<pose>.svg`（pose：`wave`、`think`、`cheer`、`magic`），`viewBox="0 0 200 200"`；躲起來的樣子 `chameleon_hide_<tint>.svg`（只露眼睛和捲尾巴，身體是 tint 的顏色）。
- 三種畫風的同一樣東西，位置、大小、形狀都一樣，只是畫法不同。

## 場景 JSON
```json
{
  "id": "park", "zh": "公園", "en": "park",
  "objects": [
    {
      "id": "balloon", "zh": "氣球", "en": "balloon",
      "x": 0.62, "y": 0.30, "w": 0.10, "h": 0.18,
      "z": 50,
      "big": true,
      "changes": [
        {"kind": "art", "type": "color", "art": "balloon_blue", "said": "氣球變藍色了！"},
        {"kind": "gone", "said": "氣球不見了！"},
        {"kind": "flip", "said": "……"},
        {"kind": "size", "scale": 1.4, "said": "氣球變大了！"}
      ]
    }
  ],
  "extras": [
    {"id": "butterfly", "zh": "蝴蝶", "en": "butterfly", "x": 0.3, "y": 0.4, "w": 0.08, "h": 0.06, "z": 60, "big": false, "said": "多了一隻蝴蝶！"}
  ],
  "hides": [
    {"x": 0.7, "y": 0.75, "w": 0.12, "h": 0.08, "z": 40, "tint": "sand"}
  ],
  "lineup": {
    "art": "duck", "zh": "小鴨子", "w": 0.2, "h": 0.2,
    "odd": [
      {"kind": "art", "art": "duck_hat", "said": "這隻小鴨戴了帽子！"},
      {"kind": "flip", "said": "這隻小鴨轉向另一邊！"}
    ]
  }
}
```

- `x`、`y`：框的中心；`w`、`h`：框的寬高。全部是 0～1，相對於 600×600 的場景。
- `z`：畫的先後，數字大的在前面（等角圖：越下面越前面）。
- `big`：夠大、夠明顯，2～3 歲的題目可以用。
- `art` 的檔名就是物件的 `id`（原本的樣子）；變化用 `art` 指定另一張圖。
- `changes[].kind`：
  - `art`：換成另一張圖。`type` 是 `color`（換顏色）、`swap`（換成別的東西）、`count`（數量變了）、`pattern`（花紋變了）、`face`（表情變了）。
  - `gone`：不見了。
  - `flip`：左右反過來（只有看得出方向的東西才有）。
  - `size`：變大或變小（`scale`）。
- `extras`：平常不在、只在「多了一個」時出現的東西。
- `hides`：小變可以躲的地方和它要變的顏色（`tint`，例如 `leaf`、`sand`、`wood`、`red`）。
- `lineup`：「哪一個不一樣？」用的東西：排三、四個一樣的 `art`，其中一個用 `odd` 裡的一種變化。
- `said`：找到時小變說的話（念出來）。

## 難度怎麼用
- 小小：只用 `big` 的東西；變化只有 `color`、`gone`、`extras`（多一個）。
- 中：再加 `flip`、`size`、`swap`；兩張找不同 3 個。
- 大：全部；兩張找不同 5 個，小東西也可以。
- 同一題的不一樣，框不可以重疊（測試檢查）。
