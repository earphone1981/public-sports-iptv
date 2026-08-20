// Variables used by Scriptable.
// These must be at the very top of the file. Do not edit.
// icon-color: cyan; icon-glyph: magic;

// 公営これ一発 v15 loader
// YouTubeはpublic-sports側では扱わない。Free Wi-Fi本体は維持。

const BASE_URL = "https://raw.githubusercontent.com/earphone1981/public-sports-iptv/main/" + encodeURIComponent("公営これ一発_v14.3.js");

try {
  const req = new Request(BASE_URL);
  req.headers = {"Cache-Control":"no-cache","User-Agent":"Scriptable-Public-Sports-v15"};
  req.timeoutInterval = 30;
  let text = await req.loadString();
  const status = req.response?.statusCode ?? 0;
  if (status < 200 || status >= 300 || !text) throw new Error(`公営本体取得失敗 HTTP ${status}`);
  text = text.replace(/Script\.complete\(\);\s*$/m, "");
  const runner = new Function(`return (async () => {\n${text}\n})();`);
  await runner();
} catch (e) {
  const a = new Alert();
  a.title = "❌ 公営これ一発 エラー";
  a.message = String(e);
  a.addAction("OK");
  await a.present();
}
Script.complete();
