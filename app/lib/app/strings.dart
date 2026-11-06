import '../core/content.dart';

/// Everything the app says, in Traditional Chinese (Taiwan).
abstract final class Strings {
  static const appName = '眼尖尖大挑戰';

  // Home.
  static const title = '咦！哪裡不一樣？';
  static const welcome = '我是小變！我偷偷變了魔法，快來找一找！';
  static const hello = ['我是小變！', '我又偷偷變了喔！', '你找得到我嗎？', '嘻嘻，猜猜我變了什麼？'];
  static const parent = '家長';
  static const album = '相簿';
  static const home = '回家';
  static const back = '回去';
  static String placeAsk(Place p) => '我們在${p.zh}！要玩哪一個？';
  static const locked = '完整版才有喔，請爸爸媽媽看看。';
  static const switchStyle = '換畫風';
  static String styleNow(Style s) => '換成${s.zh}的樣子！';

  // Playing.
  static String oddAsk(String thing) => '哪一個$thing不一樣？';
  static const look = '先看一看，記住喔！';
  static const magic = '變！';
  static const changedOne = '小變變了什麼？點一點！';
  static const changedTwo = '小變變了兩個地方，找找看！';
  static String twoAsk(int n) => '上下兩張圖，有 $n 個地方不一樣，找找看！';
  static const hideAsk = '小變躲起來了，找找看！';
  static const hideFound = '找到小變了！被你發現了！';
  static String left(int n) => '還有 $n 個喔！';
  static const hint = '小變給你一點提示！';
  static const peek = '再看一次原來的樣子';
  static const right = ['好棒！', '你的眼睛好尖！', '找到了！', '真厲害！'];
  static const allFound = '全部找到了！';
  static const next = '下一張';
  static const again = '再玩一次';
  static const toHome = '回家';
  static String inAlbum(Place p) => '${p.zh}放進相簿了！';
  static const stamp = '找到了';

  // The album.
  static String albumCount(int have, int all) => '放進相簿 $have／$all 張';
  static const notYet = '還沒去過';

  // Resting.
  static const restTitle = '小變要睡覺了';
  static const restLine = '眼睛也休息一下。\n我們去窗戶邊，\n看看遠遠的地方吧！';

  // Parent gate (as in the sibling apps).
  static const callParent = '請爸爸媽媽來幫忙喔！';
  static const parentGateTitle = '家長確認';
  static String gateQuestion(String a, String b) => '$a 加 $b 等於多少？';
  static const gateRules = '答錯三次要等一分鐘。';
  static const wrongAnswer = '不對喔，換一題。';
  static String gateWait(int s) => '請等 $s 秒再試';
  static const backspace = '刪掉';
  static const cancel = '取消';

  // Parent mode.
  static const parentTitle = '家長模式';
  static const age = '年齡（難度）';
  static String levelLine(Level l) => l.ages;
  static const ageNote = '年紀越大，不一樣的地方越小、越多。2～3 歲只有很大、很明顯的變化，也不玩「兩張找不同」。';
  static const playTime = '每次可以玩多久';
  static String minutes(int m) => '$m 分鐘';
  static const playTimeNote = '時間到了，小變會睡覺，請小朋友讓眼睛休息、看看遠方。要家長解開，或等一個小時，才能再玩。';
  static const playOn = '讓小朋友再玩一次（重新計時）';
  static const resting = '現在是休息時間。';
  static const style = '一開始的畫風';
  static const styleNote = '三種畫風的題目一模一樣，小朋友玩的時候也可以點右上角換。';
  static const hints = '提示';
  static const hintsMany = '多';
  static const hintsFew = '少';
  static const hintsNote = '多：20 秒沒找到，小變會在附近發亮；少：要點放大鏡才有提示。';
  static const sound = '聲音';
  static const music = '背景音樂';
  static const effects = '音效';
  static const voice = '念出小變說的話和東西的名字';
  static const english = '東西的名字後面加英文（balloon）';
  static const progress = '進度';
  static String progressLine(int found, int stars) => found == 0 ? '還沒玩過' : '找到 $found 個，$stars 顆星';
  static const progressNote = '每個場景玩完一種遊戲得一顆星，最多三顆。';
  static const together = '生活中一起玩';
  static const tips = [
    '散步時玩「我看到一個紅色的……」，讓小朋友找找看。',
    '桌上放三樣東西，閉上眼睛偷偷拿走一樣，問「少了什麼？」',
    '看繪本時比一比：這一頁和上一頁，哪裡不一樣？',
    '把小玩具藏在顏色一樣的地方，玩躲貓貓。',
    '找到的時候，請小朋友說出來：「氣球變藍色了！」',
  ];
  static const fullVersion = '完整版';
  static const fullNote = '免費版有公園和海邊；完整版有全部六個場景。（測試版先全部打開。）';
  static const fullSwitch = '打開完整版（測試用）';
  static const about = '關於';
  static const privacy = '不連網、不定位、沒有廣告、沒有帳號；玩的紀錄不會傳給任何人，只存在這支手機（和家長自己帳號的手機備份）裡。';
  static String version(String v) => '版本 $v';
}
