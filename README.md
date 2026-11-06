# 眼尖尖大挑戰

給 2～5 歲小朋友的找碴遊戲：調皮的變色龍「小變」偷偷把圖裡的東西變了，還會變色躲起來，小朋友要把它找出來。從「哪一個不一樣」「哪裡變了」到「兩張找不同」，一步一步練仔細看、專心和說出來。

- 設計：[docs/design.md](docs/design.md)，草圖在 `docs/mockups/`。
- 和「[畫畫小鎮](https://github.com/yaufan/APP_Kids_Paint)」「[字母寵物](https://github.com/yaufan/APP_Kids_Paint_for_learning_writing)」「[動物小餐廳](https://github.com/yaufan/APP_Kids_Cook)」「[小卡認天下](https://github.com/yaufan/APP_Kids_Card_Game)」「[想一想樂園](https://github.com/yaufan/APP_Kids_Brainstorming)」是兄弟 APP：同一個作者、同一套技術、不同畫風。
- 不連網、不定位、沒有廣告、沒有帳號。

## 下載（Android）
- 最新版：[Releases](https://github.com/yaufan/APP_Kids_FalseCharge/releases/latest)，一般手機下載 `sharp-eyes-版本-arm64.apk`。
- 用手機掃描 [docs/download-qr.png](docs/download-qr.png)。

## 目前進度
- 0.1.0（測試版）：四種玩法（哪一個不一樣、小變變了什麼、兩張找不同、小變躲在哪裡）、三個難度、6 個場景、三種畫風隨時換、相簿、休息時間、家長模式、音樂和音效、APP 圖示。版本紀錄在 [CHANGELOG.md](CHANGELOG.md)。

## 程式和素材在哪裡
- `app/`：Flutter 程式。`lib/core/` 是場景資料（`scenes.dart`）、出題規則（`puzzles.dart`）、存檔、聲音、語音；`lib/features/` 是首頁和場景頁（`home/`）、四種玩法（`play/`）、相簿、休息、家長模式。
- `app/assets/scenes/<場景>.json`：每個場景的東西和可以怎麼變，約定寫在 [docs/scenes.md](docs/scenes.md)。
- `design/art/`：用 Python 畫的圖。`kit.py` 把同一份幾何畫成三種畫風，`scene_<場景>.py` 是六個場景，`chameleon.py` 是小變，`icon.py` 是 APP 圖示；`python3 build.py all` 全部重畫。
- `design/sounds/make_sounds.py`：合成全部的音樂和聲音。
- 測試：在 `app/` 裡 `flutter test`；完整流程 `flutter test test/flow_test.dart`，截圖在 `app/build/screenshots/`。

## 授權
- 非商業使用授權：自己、家人使用，或學校、非營利團體的教學，都可以免費使用、修改、分享，要註明出處。
- 商業用途（販賣、收費、廣告、上架）要先取得作者書面同意。也不可以拿來訓練 AI。
- 細節見 [LICENSE](LICENSE)；別人做的部分（字型）見 [NOTICE.md](NOTICE.md)。
