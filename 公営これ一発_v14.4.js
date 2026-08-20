// Variables used by Scriptable.
// These must be at the very top of the file. Do not edit.
// icon-color: cyan; icon-glyph: magic;

// ============================================================
// 公営これ一発 v14.4
// v14.3 正式版を土台に実行し、最後に himitsu 側の
// 一般YouTube更新 Workflow も同時起動する正式版。
// ============================================================

const BASE_URL =
  "https://raw.githubusercontent.com/earphone1981/public-sports-iptv/main/" +
  encodeURIComponent("公営これ一発_v14.3.js");

const HIM_TOKEN_KEY = "himitsu_github_pat_v1";
const GENERAL_WORKFLOW = "update_general_youtube.yml";

async function loadBaseScript() {
  const req = new Request(BASE_URL);
  req.headers = {
    "Cache-Control": "no-cache",
    "User-Agent": "Scriptable-Public-Sports-v14.4"
  };
  req.timeoutInterval = 30;

  let text = await req.loadString();
  const status = req.response?.statusCode ?? 0;

  if (status < 200 || status >= 300 || !text) {
    throw new Error(`v14.3本体取得失敗: HTTP ${status}`);
  }

  // v14.3 の全機能をそのまま v14.4 として動かす。
  text = text.replace(/v14\.3/g, "v14.4");

  // 内側の Script.complete() は最後まで走らせるため外す。
  text = text.replace(/Script\.complete\(\);/g, "");

  return text;
}

async function dispatchGeneralYouTube() {
  if (!Keychain.contains(HIM_TOKEN_KEY)) {
    throw new Error(
      "Free Wi-Fi用TokenがKeychainにありません。\n" +
      "先に公営これ一発を一度実行してTokenを保存してください。"
    );
  }

  const token = Keychain.get(HIM_TOKEN_KEY);

  const req = new Request(
    `https://api.github.com/repos/ajiousama/himitsu/actions/workflows/${GENERAL_WORKFLOW}/dispatches`
  );

  req.method = "POST";
  req.headers = {
    "Authorization": `Bearer ${token}`,
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "Content-Type": "application/json",
    "User-Agent": "Scriptable-General-YouTube"
  };
  req.body = JSON.stringify({ ref: "main" });

  const data = await req.load();
  const status = req.response?.statusCode ?? 0;
  const body = data.toRawString();

  if (status < 200 || status >= 300) {
    throw new Error(
      `一般YouTube Actions起動失敗: GitHub API ${status}\n` +
      body.slice(0, 500)
    );
  }
}

async function showResult(title, message) {
  const a = new Alert();
  a.title = title;
  a.message = message;
  a.addAction("OK");
  await a.present();
}

try {
  const base = await loadBaseScript();

  // v14.3正式版を丸ごと継承して実行。
  const runner = new Function(
    `return (async () => {\n${base}\n})();`
  );
  await runner();

  // 公営・EPG処理終了後、一般YouTubeも同じ一発で起動。
  await dispatchGeneralYouTube();

  await showResult(
    "📺 一般YouTube 起動済み",
    "ajiousama/himitsu の一般YouTube更新を起動しました。\n\n" +
    "✅ update_general_youtube.yml\n" +
    "✅ かなチューブ／一般LIVE／ライブカメラ更新\n" +
    "✅ freewifiへ自動反映"
  );

} catch (e) {
  console.error(e);

  await showResult(
    "❌ 公営これ一発 v14.4 エラー",
    String(e)
  );
}

Script.complete();
