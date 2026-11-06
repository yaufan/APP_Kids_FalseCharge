---
name: release-kids-app
description: 把 yaufan 的兒童 APP（畫畫小鎮、字母寵物、動物小餐廳、小卡認天下、想一想樂園、眼尖尖大挑戰、迷宮小冒險，和以後的新 APP）做成可以安裝的 Android APK 並發布：本機測試、示範影片和截圖、問使用者能不能推到 main、推上去、等 GitHub Actions 打包、確認 Releases、做下載 QR code 傳給使用者。使用者說「發布」「出新版」「推到 main」「做成可以安裝的 APP」「給我 QR code」「新 APP 第一次發布」時用。
---

# 發布兒童 APP（做成可以安裝的 APK）

使用者在台灣，用手機上的 Claude App 看對話：**一律用繁體中文、白話**回覆；**打不開 artifact 連結**，圖片、影片、QR code 都用 SendUserFile 傳。專案自己的 `CLAUDE.md` 比這份優先。

## 這些 APP

| APP | 專案（github.com/yaufan/…） | APK 名稱 | 簽章環境變數 |
|---|---|---|---|
| 畫畫小鎮 | APP_Kids_Paint | `kids-paint-版本-arm64.apk` | `KIDS_PAINT_KEYSTORE` |
| 字母寵物 | APP_Kids_Paint_for_learning_writing | `letter-pets-…` | `LETTER_PETS_KEYSTORE` |
| 動物小餐廳 | APP_Kids_Cook | `animal-restaurant-…` | `ANIMAL_RESTAURANT_KEYSTORE` |
| 小卡認天下 | APP_Kids_Card_Game | `card-world-…` | `CARD_WORLD_KEYSTORE` |
| 想一想樂園 | APP_Kids_Brainstorming | `think-park-…` | `THINK_PARK_KEYSTORE` |
| 眼尖尖大挑戰 | APP_Kids_FalseCharge | `sharp-eyes-…` | `SHARP_EYES_KEYSTORE` |
| 迷宮小冒險 | APP_Kids_maze | `maze-adventure-…` | `MAZE_ADVENTURE_KEYSTORE` |

都是 Flutter（`app/`），工作流程在 `.github/workflows/`：
- `app.yml`（App）：推到 `main` 而且改到 `app/**` 時跑。內容是分析、全部測試、打包 APK、檢查簽章指紋和權限，約 8～20 分鐘。
- `release.yml`（Release）：推到 `main` 而且改到 `app/pubspec.yaml`、`CHANGELOG.md` 或它自己時跑。版本還沒發布過，就打包 arm64、armv7、x86_64 三個 APK 放上 Releases，約 9～20 分鐘；版本已經發布過約 1 分鐘。
- 推工作分支（`claude/...`）不會啟動任何工作流程。只改 `.claude/`、`docs/`、`README.md`、`CLAUDE.md` 推到 main 也不會啟動。

iPhone 不能裝 APK。要裝到 iPhone 得先辦 Apple 開發者帳號（每年 99 美元），再用 TestFlight；使用者還沒決定要不要辦。

## 步驟

### 1. 發布前在本機確認（都在工作分支上做）
1. **版本號三處一致**（`test/version_test.dart` 會檢查）：
   - `app/pubspec.yaml` 的 `version: X.Y.Z+N`，每一版 N 加 1；
   - `app/lib/app/version.dart` 的預設值；
   - `CHANGELOG.md` 最上面一段 `## X.Y.Z 測試版（日期）`，寫給家長看，白話中文。
   - 版本號規則：加新功能升中間那個數字（次版），只修問題升最後一個數字（修正）。
2. **測試**：
   - 在 `app/` 裡跑 `flutter analyze`，要零問題。
   - 跑 `flutter test`，但不含 `test/flow_test.dart`；`test/helpers.dart` 不是測試檔。畫畫小鎮要改用 `tools/run_tests.sh LOG 測試檔…`，它的 pubspec 會暫時加一段 sqlite，那段絕對不能 commit。
   - 跑完整流程 `flutter test test/flow_test.dart`，截圖會在 `app/build/screenshots/`。
3. **示範影片**：在 `app/` 裡跑 `flutter test test/demo/demo_video_test.dart --dart-define=DEMO=true`。完成後在專案根目錄跑 `python3 tools/demo_audio.py`，會產生 `app/build/demo/demo.mp4`。用 ffmpeg 抽幾格看字幕對不對。
4. **傳給使用者看**（SendUserFile）：
   - 示範影片，或照 `chapters.txt` 剪出新功能的片段；
   - 手機截圖，幾張併成一張（用 PIL）。
5. commit，訊息用英文，結尾加系統要求的署名行，不寫模型名稱；推工作分支。

### 2. 新 APP 第一次發布前多檢查
- **工作流程**：從最近的兄弟 APP 複製 `.github/workflows/{app,release,cleanup}.yml`，用 sed 換掉三樣東西：APK 名稱、`<名稱>_KEYSTORE` 環境變數、APP 中文名稱。指紋 `TEST_KEY_SHA256` 保持一樣。
- **`app/android/app/build.gradle.kts`**：
  - `applicationId` 要獨一無二，像 `com.yaufan.mazeadventure`；
  - 簽章段落讀環境變數 `<名稱>_KEYSTORE` 和 `<名稱>_KEYSTORE_PASSWORD`；
  - `keyAlias` 是 `kidspaint`，`storeType` 是 `pkcs12`。
- **AndroidManifest**：
  - `android:label` 用中文名稱；
  - 有 `flutter_deeplinking_enabled` = `false`，不接受別的 APP 傳來的頁面；
  - 沒有任何 `uses-permission`。
- **iOS**：Info.plist 的 `FlutterDeepLinkingEnabled` 是 false，`CFBundleDisplayName` 用中文名稱。
- **APP 圖示**：Android 的 mipmap 和 adaptive 都換好，iOS 的 AppIcon 也換好。
- **README**：加「下載（Android）」一段，並用下面的 make_qr 做 `docs/download-qr.png`，網址指向 `https://github.com/yaufan/<專案>/releases/latest`。
- **Secrets**：提醒使用者在這個專案的 GitHub 頁面 → Actions → **Secrets** 分頁 → **Repository secrets** 加 `ANDROID_KEYSTORE_BASE64` 和 `ANDROID_KEYSTORE_PASSWORD`。和畫畫小鎮是同一把測試金鑰，不能放 Variables 或 Environment。沒有 Secrets，Release 會停下來不發布。金鑰檔和密碼絕對不能放進 git。

### 3. 問使用者能不能推到 main（一定要問，不能自己決定）
問的時候說清楚四件事：
1. 會跑哪些工作流程（App、Release），為什麼要跑。
2. 這次大約用掉幾分鐘。
3. 這個月目前用了多少。用 GitHub 工具（`mcp__github__actions_list` 的 `list_workflow_runs`）列出這個月（UTC 每月 1 日起）各專案的執行，再請使用者到 GitHub 右上角頭像 → **Settings** → **Billing and licensing** → **Usage** 看正確數字。
4. 跑完大約還剩多少。帳號每月 2,000 分鐘，是所有**私有**專案共用的；Mac 主機的 1 分鐘算 10 分鐘。**公開**專案不扣額度，可以用 `curl -s https://api.github.com/repos/yaufan/<專案> | grep private` 確認是不是公開。

使用者要明確說出來才推，例如「Secrets 加好了，○○推到 main」「推到 main」「發布吧」。看不出是不是同意（例如只回「照建議」），就再問一次。

### 4. 推到 main
```bash
git fetch origin main
git merge-base --is-ancestor origin/main HEAD && git push origin HEAD:main   # 只做快轉，不強推
```
- 推完用 `mcp__github__actions_list`（`list_workflow_runs`）確認 App 和 Release 都開始了。
- 不要一直問進度：用 Bash 背景執行 `sleep 900` 等它，大約 15 分鐘後再看結果。

### 5. 確認發布成功
- 兩個工作流程的 `conclusion` 都要是 `success`。失敗的話，用 `mcp__github__get_job_logs` 看原因、修好，再照第 3 步問使用者一次。
- 用 `mcp__github__get_latest_release` 確認 tag `vX.Y.Z` 有三個 APK，記下 arm64 的 `browser_download_url`。

### 6. 做下載 QR code 給使用者
```bash
python3 .claude/skills/release-kids-app/make_qr.py "<arm64 的下載網址>" "<輸出>.png" "<APP 名稱> X.Y.Z" "Android 手機掃描，直接下載安裝" "github.com/yaufan/<專案>|releases/download/vX.Y.Z/<檔名>"
```
- 需要 `pip install segno pillow`，還有中文字型 WenQuanYi Zen Hei，或用 `QR_FONT` 指定別的字型。
- 一定要解碼確認網址對：`pip install zxing-cpp` 後執行 `python3 -c "import zxingcpp; from PIL import Image; print([r.text for r in zxingcpp.read_barcodes(Image.open('<輸出>.png'))])"`。OpenCV 有時候讀不出來，不代表 QR 壞了。
- QR 檔放在 scratchpad 的 `qr/` 資料夾。使用者要「全部 APP」的話，把每個 APP 最新版的 QR 併成一張，併完再解碼確認一次。
- 用 SendUserFile 傳兩張：這一版直接下載 arm64 APK 的 QR，和 `docs/download-qr.png`（最新版頁面）。

### 7. 收尾
- 回報要寫：版本、兩個工作流程的結果和用了幾分鐘、APK 名稱（一般手機用 arm64，很舊的手機用 armv7）、還沒用耳朵聽過或沒在真手機試過的地方。
- 更新專案 `CLAUDE.md` 的「目前的狀態」（如果有這一段）和 README 的進度。

## 常見問題
- **Release 說沒有 `ANDROID_KEYSTORE_BASE64`**：Secrets 沒加，或放錯地方（要放在 Repository secrets）。
- **APK 簽章指紋不對**：金鑰不是那把測試金鑰。手機要先移除舊版才能裝。
- **推到 main 被拒絕（不是快轉）**：先 `git fetch` 再合併，不要強推。
- **shallow clone 推不上去（HTTP 413）**：先 `git fetch origin main`，讓推送只帶差異。
