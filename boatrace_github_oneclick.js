// BOAT RACE 24場 -> GitHub -> EPG/M3U更新
// Scriptable版（初期の「公営これ一発」取得方式を復元）
// 初回だけ Fine-grained PAT を入力します。
// 必要権限: Contents Read and write / Actions Read and write

const GITHUB_OWNER = "earphone1981";
const GITHUB_REPO = "public-sports-iptv";
const GITHUB_BRANCH = "main";
const BOAT_FILE = "boatrace_today.m3u";
const WORKFLOW_NAME = "update_epg_3days.yml";
const TOKEN_KEY = "public_sports_github_pat";

const venues = [
  ["01kiryu",       "boat.kiryu",       "01 桐生"],
  ["02toda",        "boat.toda",        "02 戸田"],
  ["03edogawa",     "boat.edogawa",     "03 江戸川"],
  ["04heiwajima",   "boat.heiwajima",   "04 平和島"],
  ["05tamagawa",    "boat.tamagawa",    "05 多摩川"],
  ["06hamanako",    "boat.hamanako",    "06 浜名湖"],
  ["07gamagori",    "boat.gamagori",    "07 蒲郡"],
  ["08tokoname",    "boat.tokoname",    "08 常滑"],
  ["09tsu",         "boat.tsu",         "09 津"],
  ["10mikuni",      "boat.mikuni",      "10 三国"],
  ["11biwako",      "boat.biwako",      "11 びわこ"],
  ["12suminoe",     "boat.suminoe",     "12 住之江"],
  ["13amagasaki",   "boat.amagasaki",   "13 尼崎"],
  ["14naruto",      "boat.naruto",      "14 鳴門"],
  ["15marugame",    "boat.marugame",    "15 丸亀"],
  ["16kojima",      "boat.kojima",      "16 児島"],
  ["17miyajima",    "boat.miyajima",    "17 宮島"],
  ["18tokuyama",    "boat.tokuyama",    "18 徳山"],
  ["19shimonoseki", "boat.shimonoseki", "19 下関"],
  ["20wakamatsu",   "boat.wakamatsu",   "20 若松"],
  ["21ashiya",      "boat.ashiya",      "21 芦屋"],
  ["22fukuoka",     "boat.fukuoka",     "22 福岡"],
  ["23karatsu",     "boat.karatsu",     "23 唐津"],
  ["24omura",       "boat.omura",       "24 大村"]
];

function japanDateYYYYMMDD() {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Tokyo", year: "numeric", month: "2-digit", day: "2-digit"
  }).formatToParts(new Date());
  const y = parts.find(x => x.type === "year").value;
  const m = parts.find(x => x.type === "month").value;
  const d = parts.find(x => x.type === "day").value;
  return `${y}${m}${d}`;
}

function findStreamUrl(data) {
  if (!data) return null;
  if (Array.isArray(data.sources)) {
    for (const source of data.sources) {
      if (source?.src) return source.src;
      if (source?.url) return source.url;
    }
  }
  if (typeof data === "object") {
    for (const key of Object.keys(data)) {
      const value = data[key];
      if (typeof value === "string" && (value.includes(".m3u8") || value.includes("manifest"))) {
        return value;
      }
      if (value && typeof value === "object") {
        const found = findStreamUrl(value);
        if (found) return found;
      }
    }
  }
  return null;
}

async function getToken() {
  if (Keychain.contains(TOKEN_KEY)) return Keychain.get(TOKEN_KEY);
  const a = new Alert();
  a.title = "GitHub Token 初回設定";
  a.message = "Fine-grained PATを入力してください。\n\nContents: Read and write\nActions: Read and write";
  a.addSecureTextField("github_pat_...");
  a.addAction("保存");
  a.addCancelAction("中止");
  const r = await a.present();
  if (r === -1) throw new Error("Token設定を中止しました");
  const token = a.textFieldValue(0).trim();
  if (!token) throw new Error("Tokenが空です");
  Keychain.set(TOKEN_KEY, token);
  return token;
}

async function githubRequest(path, token, method = "GET", body = null) {
  const req = new Request(`https://api.github.com${path}`);
  req.method = method;
  req.headers = {
    "Authorization": `Bearer ${token}`,
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "Scriptable-Public-Sports"
  };
  if (body !== null) {
    req.headers["Content-Type"] = "application/json";
    req.body = JSON.stringify(body);
  }
  const data = await req.load();
  const status = req.response?.statusCode ?? 0;
  const text = data.toRawString();
  if (status < 200 || status >= 300) throw new Error(`GitHub API ${status}\n${text.slice(0, 500)}`);
  if (!text) return {};
  try { return JSON.parse(text); } catch { return text; }
}

function utf8ToBase64(text) {
  return Data.fromString(text).toBase64String();
}

async function upsertGitHubFile(path, content, token, message) {
  let sha = null;
  try {
    const current = await githubRequest(
      `/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${encodeURIComponent(path).replace(/%2F/g, "/")}?ref=${GITHUB_BRANCH}`,
      token
    );
    sha = current.sha ?? null;
    if (current.content) {
      const oldText = Data.fromBase64String(current.content.replace(/\n/g, "")).toRawString();
      if (oldText === content) return { changed: false, sha };
    }
  } catch (e) {
    if (!String(e).includes("GitHub API 404")) throw e;
  }
  const body = { message, content: utf8ToBase64(content), branch: GITHUB_BRANCH };
  if (sha) body.sha = sha;
  const result = await githubRequest(
    `/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${encodeURIComponent(path).replace(/%2F/g, "/")}`,
    token, "PUT", body
  );
  return { changed: true, sha: result?.content?.sha ?? null };
}

async function dispatchWorkflow(token) {
  await githubRequest(
    `/repos/${GITHUB_OWNER}/${GITHUB_REPO}/actions/workflows/${WORKFLOW_NAME}/dispatches`,
    token, "POST", { ref: GITHUB_BRANCH }
  );
}

async function generateBoatM3U() {
  const date = japanDateYYYYMMDD();
  let output = "#EXTM3U\n\n";
  let success = 0;
  const failed = [];

  for (const [apiId, tvgId, name] of venues) {
    const apiUrl =
      "https://playback.api.streaks.jp/v1/projects/cp-boatrace-prod/medias/ref:lm-br-" +
      apiId + "-tokyo-" + date + "?audio_only=false";
    console.log(`取得中: ${name}`);
    try {
      const req = new Request(apiUrl);
      req.method = "GET";
      req.headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1",
        "Origin": "https://front.player.boatrace-cdn.jp",
        "Referer": "https://front.player.boatrace-cdn.jp/"
      };
      req.timeoutInterval = 15;
      const json = await req.loadJSON();
      const streamUrl = findStreamUrl(json);
      if (!streamUrl) {
        failed.push(name);
        continue;
      }
      output += `#EXTINF:-1 tvg-id="${tvgId}" tvg-name="${name}" group-title="ボートレース",${name}\n`;
      output += streamUrl + "\n\n";
      success++;
    } catch (e) {
      console.log(`× ${name}: ${e}`);
      failed.push(name);
    }
  }
  return { date, output, success, failed };
}

async function saveLocalM3U(content) {
  const fm = FileManager.iCloud();
  const path = fm.joinPath(fm.documentsDirectory(), BOAT_FILE);
  fm.writeString(path, content);
}

try {
  const token = await getToken();
  const boat = await generateBoatM3U();
  await saveLocalM3U(boat.output);
  const pushed = await upsertGitHubFile(BOAT_FILE, boat.output, token, `Update BOAT RACE M3U ${boat.date} from iPhone one-click`);
  await dispatchWorkflow(token);

  let msg =
    `日付：${boat.date}\n` +
    `ボート取得：${boat.success} / 24場\n` +
    `GitHub送信：${pushed.changed ? "更新" : "変更なし"}\n` +
    `Actions：起動しました\n\n` +
    `iCloud Drive / Scriptable / ${BOAT_FILE}`;
  if (boat.failed.length) msg += `\n\n取得できなかった場：\n${boat.failed.join(" / ")}`;

  const a = new Alert();
  a.title = "🚤 公営これ一発 完了";
  a.message = msg;
  a.addAction("OK");
  await a.present();
} catch (e) {
  console.error(e);
  const a = new Alert();
  a.title = "❌ エラー";
  a.message = String(e);
  a.addAction("OK");
  await a.present();
}

Script.complete();
