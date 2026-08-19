// Variables used by Scriptable.
// These must be at the very top of the file. Do not edit.
// icon-color: cyan; icon-glyph: magic;
// Variables used by Scriptable.
// These must be at the very top of the file. Do not edit.
// icon-color: cyan; icon-glyph: magic;

// ============================================================
// 公営これ一発 v14.1
// Scriptable 全文コピペ正式版
//
// v14.1
// ・公営YouTubeを毎回ゼロから再構築
// ・tvg-id重複を除去
// ・同一YouTube配信ID / 実URL重複も除去
// ・前回のYouTubeエントリーを積み増さない
// ・かなチューブは kana_live.m3u から保険読込
// ・その他LIVEは公営側へ戻さない
// ・BOAT前回URL保持
// ・JRA/GCH維持
// ・YouTube Actions / EPG Actions 起動
// ・本体を v14.1 / latest としてGitHub保存
// ============================================================

const OWNER = "earphone1981";
const REPO = "public-sports-iptv";
const BRANCH = "main";

const TOKEN_KEY =
  "public_sports_github_pat_v4";

const RAW_BASE =
  `https://raw.githubusercontent.com/${OWNER}/${REPO}/${BRANCH}`;

const API_REPO =
  `/repos/${OWNER}/${REPO}`;

const EPG_URL =
  `${RAW_BASE}/epg.xml`;

const PUBLIC_YOUTUBE_FILE =
  "public_sports_youtube.m3u";

const KANA_FILE =
  "kana_live.m3u";

const UA =
  "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) " +
  "AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1";


// ============================================================
// BOAT 24場
// ============================================================

const BOAT = [
  ["01kiryu","boat.kiryu","BOATRACE桐生","桐生","01_kiryu.png"],
  ["02toda","boat.toda","BOATRACE戸田","戸田","02_toda.png"],
  ["03edogawa","boat.edogawa","BOATRACE江戸川","江戸川","03_edogawa.png"],
  ["04heiwajima","boat.heiwajima","BOATRACE平和島","平和島","04_heiwajima.png"],
  ["05tamagawa","boat.tamagawa","BOATRACE多摩川","多摩川","05_tamagawa.png"],
  ["06hamanako","boat.hamanako","BOATRACE浜名湖","浜名湖","06_hamanako.png"],
  ["07gamagori","boat.gamagori","BOATRACE蒲郡","蒲郡","07_gamagori.png"],
  ["08tokoname","boat.tokoname","BOATRACE常滑","常滑","08_tokoname.png"],
  ["09tsu","boat.tsu","BOATRACE津","津","09_tsu.png"],
  ["10mikuni","boat.mikuni","BOATRACE三国","三国","10_mikuni.png"],
  ["11biwako","boat.biwako","BOATRACEびわこ","びわこ","11_biwako.png"],
  ["12suminoe","boat.suminoe","BOATRACE住之江","住之江","12_suminoe.png"],
  ["13amagasaki","boat.amagasaki","BOATRACE尼崎","尼崎","13_amagasaki.png"],
  ["14naruto","boat.naruto","BOATRACE鳴門","鳴門","14_naruto.png"],
  ["15marugame","boat.marugame","BOATRACE丸亀","丸亀","15_marugame.png"],
  ["16kojima","boat.kojima","BOATRACE児島","児島","16_kojima.png"],
  ["17miyajima","boat.miyajima","BOATRACE宮島","宮島","17_miyajima.png"],
  ["18tokuyama","boat.tokuyama","BOATRACE徳山","徳山","18_tokuyama.png"],
  ["19shimonoseki","boat.shimonoseki","BOATRACE下関","下関","19_shimonoseki.png"],
  ["20wakamatsu","boat.wakamatsu","BOATRACE若松","若松","20_wakamatsu.png"],
  ["21ashiya","boat.ashiya","BOATRACE芦屋","芦屋","21_ashiya.png"],
  ["22fukuoka","boat.fukuoka","BOATRACE福岡","福岡","22_fukuoka.png"],
  ["23karatsu","boat.karatsu","BOATRACE唐津","唐津","23_karatsu.png"],
  ["24omura","boat.omura","BOATRACE大村","大村","24_omura.png"]
];


// ============================================================
// JRA / GCH
// ============================================================

const JRA = [
  [
    "jra.gch",
    "グリーンチャンネル",
    "グリーンチャンネル（高画質）",
    "gchmain.m3u8",
    "gch.png"
  ],
  [
    "jra.gch",
    "グリーンチャンネル",
    "グリーンチャンネル（低画質）",
    "gchmain_LQ.m3u8",
    "gch.png"
  ],
  [
    "jra.east",
    "JRA EAST",
    "JRA EAST（高画質）",
    "EAST_test.m3u8",
    "east_web3.png"
  ],
  [
    "jra.east",
    "JRA EAST",
    "JRA EAST（低画質）",
    "EAST_test_LQ.m3u8",
    "east_web3.png"
  ],
  [
    "jra.west",
    "JRA WEST",
    "JRA WEST（高画質）",
    "WEST_master .m3u8",
    "west_web4.png"
  ],
  [
    "jra.west",
    "JRA WEST",
    "JRA WEST（低画質）",
    "WEST_master_LQ.m3u8",
    "west_web4.png"
  ],
  [
    "jra.hokkaido",
    "JRA HOKKAIDO",
    "JRA HOKKAIDO（高画質）",
    "hokaido_master (1).m3u8",
    "hokkaido_local.png"
  ],
  [
    "jra.hokkaido",
    "JRA HOKKAIDO",
    "JRA HOKKAIDO（低画質）",
    "hokaido_master_LQ.m3u8",
    "hokkaido_local.png"
  ]
];


// ============================================================
// 日付 / RAW
// ============================================================

function japanDate() {
  const p =
    new Intl.DateTimeFormat(
      "en-CA",
      {
        timeZone: "Asia/Tokyo",
        year: "numeric",
        month: "2-digit",
        day: "2-digit"
      }
    ).formatToParts(new Date());

  return (
    p.find(x => x.type === "year").value +
    p.find(x => x.type === "month").value +
    p.find(x => x.type === "day").value
  );
}


function rawUrl(path) {
  return RAW_BASE + "/" +
    path
      .split("/")
      .map(encodeURIComponent)
      .join("/");
}


// ============================================================
// TOKEN
// ============================================================

async function getToken() {

  if (Keychain.contains(TOKEN_KEY)) {
    return Keychain.get(TOKEN_KEY);
  }

  const a = new Alert();

  a.title = "GitHub Token";
  a.addSecureTextField("github_pat_...");
  a.addAction("保存");
  a.addCancelAction("中止");

  const r =
    await a.present();

  if (r === -1) {
    throw new Error(
      "Token入力中止"
    );
  }

  const token =
    a.textFieldValue(0).trim();

  if (!token) {
    throw new Error(
      "Tokenが空です"
    );
  }

  Keychain.set(
    TOKEN_KEY,
    token
  );

  return token;
}


// ============================================================
// GitHub API
// ============================================================

async function githubRequest(
  path,
  token,
  method = "GET",
  body = null
) {

  const req =
    new Request(
      `https://api.github.com${path}`
    );

  req.method = method;

  req.headers = {
    "Authorization":
      `Bearer ${token}`,
    "Accept":
      "application/vnd.github+json",
    "X-GitHub-Api-Version":
      "2022-11-28",
    "User-Agent":
      "Scriptable-Public-Sports"
  };

  if (body !== null) {
    req.headers["Content-Type"] =
      "application/json";

    req.body =
      JSON.stringify(body);
  }

  const data =
    await req.load();

  const status =
    req.response?.statusCode ?? 0;

  const text =
    data.toRawString();

  if (
    status < 200 ||
    status >= 300
  ) {
    throw new Error(
      `GitHub API ${status}\n` +
      text.slice(0, 500)
    );
  }

  if (!text) {
    return {};
  }

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}


// ============================================================
// GitHub保存
// ============================================================

function toBase64(text) {
  return Data
    .fromString(text)
    .toBase64String();
}


async function uploadFile(
  path,
  content,
  token,
  message
) {

  const encodedPath =
    path
      .split("/")
      .map(encodeURIComponent)
      .join("/");

  let sha = null;

  try {

    const current =
      await githubRequest(
        `${API_REPO}/contents/${encodedPath}?ref=${BRANCH}`,
        token
      );

    sha =
      current.sha ?? null;

    if (current.content) {

      const old =
        Data
          .fromBase64String(
            current.content
              .replace(/\n/g, "")
          )
          .toRawString();

      if (old === content) {
        console.log(
          `${path}: 変更なし`
        );

        return false;
      }
    }

  } catch(e) {

    if (
      !String(e).includes(
        "GitHub API 404"
      )
    ) {
      throw e;
    }
  }

  const body = {
    message,
    content:
      toBase64(content),
    branch: BRANCH
  };

  if (sha) {
    body.sha = sha;
  }

  await githubRequest(
    `${API_REPO}/contents/${encodedPath}`,
    token,
    "PUT",
    body
  );

  console.log(
    `${path}: GitHub更新`
  );

  return true;
}


// ============================================================
// RAW取得
// ============================================================

async function getRaw(path) {

  const req =
    new Request(
      rawUrl(path)
    );

  req.headers = {
    "Cache-Control":
      "no-cache",
    "User-Agent":
      UA
  };

  req.timeoutInterval = 30;

  return await req.loadString();
}


async function safeGetRaw(path) {

  try {
    return await getRaw(path);

  } catch(e) {

    console.log(
      `${path}: 取得失敗`
    );

    console.log(
      String(e)
    );

    return "";
  }
}


// ============================================================
// M3U解析
// ============================================================

function readEntries(text) {

  const lines =
    String(text || "")
      .replace(/\r\n/g, "\n")
      .replace(/\r/g, "\n")
      .split("\n");

  const result = [];

  for (
    let i = 0;
    i < lines.length;
    i++
  ) {

    const extinf =
      lines[i].trim();

    if (
      !extinf.startsWith(
        "#EXTINF:"
      )
    ) {
      continue;
    }

    const options = [];
    let url = null;

    for (
      let j = i + 1;
      j < lines.length;
      j++
    ) {

      const n =
        lines[j].trim();

      if (!n) {
        continue;
      }

      if (
        n.startsWith(
          "#EXTINF:"
        )
      ) {
        break;
      }

      if (
        n.startsWith(
          "#EXTVLCOPT:"
        )
      ) {
        options.push(n);
        continue;
      }

      if (
        !n.startsWith("#")
      ) {
        url = n;
        break;
      }
    }

    if (url) {
      result.push({
        extinf,
        options,
        url
      });
    }
  }

  return result;
}


function getTvgId(extinf) {

  const m =
    String(extinf || "")
      .match(
        /tvg-id="([^"]+)"/i
      );

  return m
    ? m[1].trim()
    : null;
}


// ============================================================
// YouTube安定識別キー
//
// 期限・署名が変わっても同じ配信なら同一扱い
// ============================================================

function getStableStreamKey(url) {

  const s =
    String(url || "").trim();

  if (!s) {
    return "";
  }

  // YouTube watch URL
  try {

    const u =
      new URL(s);

    const host =
      u.hostname.toLowerCase();

    if (
      host === "youtu.be" ||
      host.endsWith(".youtu.be")
    ) {

      const id =
        u.pathname
          .replace(/^\/+/, "")
          .split("/")[0];

      if (id) {
        return `youtube-video:${id}`;
      }
    }


    if (
      host.includes("youtube.com")
    ) {

      const v =
        u.searchParams.get("v");

      if (v) {
        return `youtube-video:${v}`;
      }

      // /live/VIDEOID
      const liveMatch =
        u.pathname.match(
          /\/live\/([^/]+)/
        );

      if (liveMatch) {
        return `youtube-video:${liveMatch[1]}`;
      }
    }


    // googlevideo系
    // HLS URLの /id/XXXX/ を安定識別子として使う
    if (
      host.includes(
        "googlevideo.com"
      )
    ) {

      const idMatch =
        u.pathname.match(
          /\/id\/([^/]+)/
        );

      if (idMatch) {
        return `googlevideo-id:${idMatch[1]}`;
      }

      // IDが取れない場合でもクエリは期限付きなので除外
      return (
        u.origin +
        u.pathname
      );
    }


    // その他のURLも
    // ?token= 等を無視
    return (
      u.origin +
      u.pathname
    );

  } catch {

    return s
      .split("?")[0]
      .split("#")[0];
  }
}


// ============================================================
// YouTube重複除去
//
// ・同じtvg-id → 1件
// ・同じ配信ID/URL → 1件
//
// 前回データは使わず、今回読み込んだM3Uだけから作る
// ============================================================

function dedupeYouTubeEntries(entries) {

  const result = [];

  const seenIds =
    new Set();

  const seenStreams =
    new Set();

  for (
    const item
    of entries || []
  ) {

    const tvgId =
      getTvgId(
        item.extinf
      );

    const streamKey =
      getStableStreamKey(
        item.url
      );


    if (
      tvgId &&
      seenIds.has(tvgId)
    ) {

      console.log(
        `YouTube重複除去 tvg-id: ${tvgId}`
      );

      continue;
    }


    if (
      streamKey &&
      seenStreams.has(streamKey)
    ) {

      console.log(
        `YouTube重複除去 stream: ${streamKey}`
      );

      continue;
    }


    if (tvgId) {
      seenIds.add(tvgId);
    }

    if (streamKey) {
      seenStreams.add(streamKey);
    }

    result.push(item);
  }

  return result;
}


// ============================================================
// 前回BOAT URL取得
// ============================================================

function extractPreviousBoat(
  existingPublic
) {

  const map =
    new Map();

  const entries =
    readEntries(
      existingPublic
    );

  for (
    const item
    of entries
  ) {

    const tvgId =
      getTvgId(
        item.extinf
      );

    if (
      !tvgId ||
      !tvgId.startsWith(
        "boat."
      )
    ) {
      continue;
    }

    if (!map.has(tvgId)) {

      map.set(
        tvgId,
        item.url
      );
    }
  }

  return map;
}


// ============================================================
// BOAT JSONから映像URL探索
// ============================================================

function findStreamUrl(data) {

  if (!data) {
    return null;
  }

  if (
    Array.isArray(data)
  ) {

    for (
      const item
      of data
    ) {

      const found =
        findStreamUrl(item);

      if (found) {
        return found;
      }
    }

    return null;
  }


  if (
    typeof data ===
    "object"
  ) {

    if (
      Array.isArray(
        data.sources
      )
    ) {

      for (
        const s
        of data.sources
      ) {

        if (
          typeof s?.src ===
          "string"
        ) {
          return s.src;
        }

        if (
          typeof s?.url ===
          "string"
        ) {
          return s.url;
        }
      }
    }


    for (
      const key
      of Object.keys(data)
    ) {

      const value =
        data[key];

      if (
        typeof value ===
        "string" &&
        (
          value.includes(".m3u8") ||
          value.includes("manifest")
        )
      ) {
        return value;
      }

      if (
        value &&
        typeof value ===
        "object"
      ) {

        const found =
          findStreamUrl(value);

        if (found) {
          return found;
        }
      }
    }
  }

  return null;
}


// ============================================================
// BOAT本線
// ============================================================

async function makeBoatM3U(
  existingPublic
) {

  const date =
    japanDate();

  const previousBoat =
    extractPreviousBoat(
      existingPublic
    );

  let text =
    "#EXTM3U\n\n";

  let freshCount = 0;
  let keptCount = 0;
  let missingCount = 0;

  const fresh = [];
  const kept = [];
  const missing = [];


  for (
    const [
      apiId,
      tvgId,
      display,
      venue,
      logoFile
    ]
    of BOAT
  ) {

    const api =
      "https://playback.api.streaks.jp/v1/" +
      "projects/cp-boatrace-prod/" +
      "medias/ref:lm-br-" +
      apiId +
      "-tokyo-" +
      date +
      "?audio_only=false";

    let stream = null;
    let sourceType = "none";


    try {

      const req =
        new Request(api);

      req.headers = {
        "User-Agent":
          UA,
        "Origin":
          "https://front.player.boatrace-cdn.jp",
        "Referer":
          "https://front.player.boatrace-cdn.jp/"
      };

      req.timeoutInterval =
        15;

      const json =
        await req.loadJSON();

      const found =
        findStreamUrl(
          json
        );

      if (found) {
        stream = found;
        sourceType = "fresh";
      }

    } catch(e) {

      console.warn(
        `${venue} 当日URL取得失敗`,
        e
      );
    }


    if (
      !stream &&
      previousBoat.has(
        tvgId
      )
    ) {

      stream =
        previousBoat.get(
          tvgId
        );

      sourceType =
        "kept";
    }


    if (!stream) {

      missingCount++;
      missing.push(venue);

      continue;
    }


    const logo =
      rawUrl(
        `public_sports_logos_github_43/boatrace/${logoFile}`
      );


    text +=
      `#EXTINF:-1 ` +
      `tvg-id="${tvgId}" ` +
      `tvg-name="${display}" ` +
      `tvg-logo="${logo}" ` +
      `group-title="ボートレース",${display}\n`;

    text +=
      stream +
      "\n\n";


    if (
      sourceType ===
      "fresh"
    ) {

      freshCount++;
      fresh.push(venue);

    } else {

      keptCount++;
      kept.push(venue);
    }
  }


  return {
    date,
    text,

    freshCount,
    keptCount,
    missingCount,

    fresh,
    kept,
    missing,

    total:
      freshCount +
      keptCount
  };
}


// ============================================================
// かなチューブ判定
// ============================================================

function isKanaEntry(item) {

  const text =
    `${item.extinf}\n${item.url}`
      .toLowerCase();

  return (
    text.includes(
      "youtube.kana.live"
    ) ||
    text.includes(
      "かなチューブ"
    ) ||
    text.includes(
      "華奈tube"
    ) ||
    text.includes(
      "kana_tube"
    )
  );
}


// ============================================================
// 公営YouTube読込
// ============================================================

async function loadPublicYouTube() {

  try {

    const text =
      await getRaw(
        PUBLIC_YOUTUBE_FILE
      );

    const source =
      readEntries(text);

    const entries =
      dedupeYouTubeEntries(
        source
      );

    return {
      entries,
      loaded: true,
      sourceCount:
        source.length,
      removed:
        source.length -
        entries.length,
      error: null
    };

  } catch(e) {

    console.warn(
      `${PUBLIC_YOUTUBE_FILE} 取得失敗:`,
      e
    );

    return {
      entries: [],
      loaded: false,
      sourceCount: 0,
      removed: 0,
      error:
        String(e)
    };
  }
}


// ============================================================
// かなチューブ保険
// ============================================================

async function loadKanaFallback() {

  try {

    const text =
      await getRaw(
        KANA_FILE
      );

    const source =
      readEntries(text)
        .filter(
          isKanaEntry
        );

    const entries =
      dedupeYouTubeEntries(
        source
      );

    return {
      entries,
      loaded: true,
      error: null
    };

  } catch(e) {

    console.warn(
      `${KANA_FILE} 取得失敗:`,
      e
    );

    return {
      entries: [],
      loaded: false,
      error:
        String(e)
    };
  }
}


// ============================================================
// 公営YouTube + かな保険
//
// ここでも再度重複除去
// ============================================================

function mergePublicYouTubeAndKana(
  publicEntries,
  kanaEntries
) {

  return dedupeYouTubeEntries([
    ...(publicEntries || []),
    ...(kanaEntries || [])
  ]);
}


// ============================================================
// 通常M3Uを出力
// ============================================================

function appendM3UEntries(
  out,
  label,
  source
) {

  const entries =
    readEntries(source);

  if (!entries.length) {
    return 0;
  }

  out.push(
    `## ${label}`
  );

  for (
    const item
    of entries
  ) {

    out.push(
      item.extinf
    );

    for (
      const opt
      of item.options
    ) {

      out.push(opt);
    }

    out.push(
      item.url
    );

    out.push("");
  }

  return entries.length;
}


// ============================================================
// public_sports.m3u
//
// ★ 毎回ゼロから作成
// ★ 前回YouTube部分を引き継がない
// ============================================================

async function makePublicM3U(
  boatText,
  publicYouTube
) {

  const keirin =
    await getRaw(
      "keirin_master.m3u"
    );

  const keiba =
    await getRaw(
      "keiba_master.m3u"
    );

  const auto =
    await getRaw(
      "autorace_master.m3u"
    );


  const out = [
    `#EXTM3U url-tvg="${EPG_URL}"`,
    ""
  ];


  appendM3UEntries(
    out,
    "競輪",
    keirin
  );

  appendM3UEntries(
    out,
    "地方競馬",
    keiba
  );

  appendM3UEntries(
    out,
    "オートレース",
    auto
  );

  appendM3UEntries(
    out,
    "ボートレース",
    boatText
  );


  // ----------------------------------------------------------
  // 公営YouTube
  // 今回取得したリストだけを使用
  // ----------------------------------------------------------

  const cleanYouTube =
    dedupeYouTubeEntries(
      publicYouTube || []
    );


  if (
    cleanYouTube.length
  ) {

    out.push(
      "## 公営YouTube公式"
    );

    for (
      const item
      of cleanYouTube
    ) {

      out.push(
        item.extinf
      );

      for (
        const opt
        of item.options
      ) {
        out.push(opt);
      }

      out.push(
        item.url
      );

      out.push("");
    }
  }


  // ----------------------------------------------------------
  // JRA / GCH
  // ----------------------------------------------------------

  out.push(
    "## 中央競馬"
  );

  for (
    const [
      tvg,
      tvgName,
      display,
      file,
      logoFile
    ]
    of JRA
  ) {

    out.push(
      `#EXTINF:-1 ` +
      `tvg-id="${tvg}" ` +
      `tvg-name="${tvgName}" ` +
      `tvg-logo="${rawUrl(logoFile)}" ` +
      `group-title="中央競馬",${display}`
    );

    out.push(
      rawUrl(file)
    );

    out.push("");
  }


  return {
    text:
      out.join("\n")
        .replace(
          /\n{3,}/g,
          "\n\n"
        )
        .trimEnd() +
      "\n",

    youtubeCount:
      cleanYouTube.length
  };
}


// ============================================================
// iCloud保存
// ============================================================

function saveICloud(
  name,
  text
) {

  const fm =
    FileManager.iCloud();

  const path =
    fm.joinPath(
      fm.documentsDirectory(),
      name
    );

  fm.writeString(
    path,
    text
  );
}


// ============================================================
// Actions
// ============================================================

async function dispatchEPG(
  token
) {

  await githubRequest(
    `${API_REPO}/actions/workflows/update_epg_3days.yml/dispatches`,
    token,
    "POST",
    {
      ref: BRANCH
    }
  );
}


async function dispatchYouTube(
  token
) {

  await githubRequest(
    `${API_REPO}/actions/workflows/youtube_namibia_live.yml/dispatches`,
    token,
    "POST",
    {
      ref: BRANCH
    }
  );
}


// ============================================================
// 自己バックアップ
// ============================================================

async function backupSelfScript(
  token
) {

  try {

    const fm =
      FileManager.iCloud();

    const scriptName =
      Script.name();

    const candidates = [
      `${scriptName}.js`,
      scriptName
    ];

    let selfText =
      null;


    for (
      const name
      of candidates
    ) {

      const path =
        fm.joinPath(
          fm.documentsDirectory(),
          name
        );

      if (
        !fm.fileExists(path)
      ) {
        continue;
      }

      try {

        selfText =
          fm.readString(path);

        if (selfText) {
          break;
        }

      } catch {}
    }


    if (!selfText) {

      console.warn(
        "自己バックアップ: Scriptable本体取得できず"
      );

      return false;
    }


    // 世代版
    await uploadFile(
      "公営これ一発_v14.1.js",
      selfText,
      token,
      "Backup 公営これ一発 v14.1"
    );


    // 常に最新版
    await uploadFile(
      "公営これ一発_latest.js",
      selfText,
      token,
      "Backup 公営これ一発 latest v14.1"
    );


    return true;

  } catch(e) {

    console.warn(
      "自己バックアップ失敗:",
      e
    );

    return false;
  }
}


// ============================================================
// 表示
// ============================================================

async function show(
  title,
  message
) {

  const a =
    new Alert();

  a.title =
    title;

  a.message =
    message;

  a.addAction("OK");

  await a.present();
}


// ============================================================
// MAIN
// ============================================================

try {

  const token =
    await getToken();


  // ----------------------------------------------------------
  // 前回BOAT URLだけは保持に使用
  // YouTube部分は引き継がない
  // ----------------------------------------------------------

  let existingPublic = "";

  try {

    existingPublic =
      await getRaw(
        "public_sports.m3u"
      );

  } catch(e) {

    console.warn(
      "既存public_sports.m3u取得失敗:",
      e
    );
  }


  // ----------------------------------------------------------
  // BOAT
  // ----------------------------------------------------------

  const boat =
    await makeBoatM3U(
      existingPublic
    );


  // ----------------------------------------------------------
  // 公営YouTube
  // ----------------------------------------------------------

  const publicYouTube =
    await loadPublicYouTube();


  // ----------------------------------------------------------
  // かな保険
  // ----------------------------------------------------------

  const kanaFallback =
    await loadKanaFallback();


  // ----------------------------------------------------------
  // YouTube最終重複除去
  // ----------------------------------------------------------

  const beforeMergeCount =
    publicYouTube.entries.length +
    kanaFallback.entries.length;


  const mergedYouTube =
    mergePublicYouTubeAndKana(
      publicYouTube.entries,
      kanaFallback.entries
    );


  const totalDuplicateRemoved =
    publicYouTube.removed +
    (
      beforeMergeCount -
      mergedYouTube.length
    );


  // ----------------------------------------------------------
  // 統合M3U
  // 毎回完全再生成
  // ----------------------------------------------------------

  const built =
    await makePublicM3U(
      boat.text,
      mergedYouTube
    );


  const publicM3U =
    built.text;


  // ----------------------------------------------------------
  // iCloud
  // ----------------------------------------------------------

  saveICloud(
    "boatrace_today.m3u",
    boat.text
  );


  saveICloud(
    "public_sports.m3u",
    publicM3U
  );


  // ----------------------------------------------------------
  // GitHub M3U
  // ----------------------------------------------------------

  await uploadFile(
    "boatrace_today.m3u",
    boat.text,
    token,
    `Update BOATRACE M3U v14.1 ${boat.date}`
  );


  const changed =
    await uploadFile(
      "public_sports.m3u",
      publicM3U,
      token,
      `Update public sports M3U v14.1 ${boat.date}`
    );


  // ----------------------------------------------------------
  // YouTube Action
  // ----------------------------------------------------------

  let youtubeDispatchOK =
    false;


  try {

    await dispatchYouTube(
      token
    );

    youtubeDispatchOK =
      true;

  } catch(e) {

    console.warn(
      "YouTube Actions起動失敗:",
      e
    );
  }


  // ----------------------------------------------------------
  // EPG Action
  // ----------------------------------------------------------

  let epgDispatchOK =
    false;


  try {

    await dispatchEPG(
      token
    );

    epgDispatchOK =
      true;

  } catch(e) {

    console.warn(
      "EPG Actions起動失敗:",
      e
    );
  }


  // ----------------------------------------------------------
  // 自己保存
  // ----------------------------------------------------------

  const backupOK =
    await backupSelfScript(
      token
    );


  // ----------------------------------------------------------
  // 結果
  // ----------------------------------------------------------

  let msg =
    `🚤 BOATRACE登録：${boat.total} / 24場\n` +
    `🟢 当日URL更新：${boat.freshCount}場\n` +
    `📼 前回URL保持：${boat.keptCount}場\n` +
    `⚫ URL未登録：${boat.missingCount}場\n` +
    `📺 公営YouTube：${publicYouTube.loaded ? "正式M3U読込OK" : "M3U未作成/取得失敗"}\n` +
    `📺 かなチューブ保険：${kanaFallback.loaded ? "読込OK" : "取得失敗"}\n` +
    `📺 公営YouTube登録：${built.youtubeCount}件\n` +
    `🧹 YouTube重複除去：${totalDuplicateRemoved}件\n` +
    `🔒 重複防止：tvg-id＋配信ID/URL\n` +
    `♻️ YouTube：毎回完全再構築\n` +
    `🚫 その他LIVE：公営側には引継ぎなし\n` +
    `🏇 GCH/JRA：GitHub設定維持\n` +
    `📋 M3U：${changed ? "更新" : "変更なし"}\n` +
    `📺 YouTube Actions：${youtubeDispatchOK ? "起動済み" : "起動失敗"}\n` +
    `📅 EPG Actions：${epgDispatchOK ? "起動済み" : "起動失敗"}\n` +
    `💾 本体バックアップ：${backupOK ? "GitHub保存OK" : "保存できず"}\n` +
    `⚠️ 非開催判定はEPG側を正とします`;


  if (
    !publicYouTube.loaded
  ) {

    msg +=
      `\n\n⚠️ ${PUBLIC_YOUTUBE_FILE}：未作成または取得できません`;
  }


  if (
    !kanaFallback.loaded
  ) {

    msg +=
      `\n⚠️ ${KANA_FILE}：取得できません`;
  }


  if (
    boat.kept.length
  ) {

    msg +=
      `\n\n📼 前回映像保持：\n` +
      boat.kept.join(" / ");
  }


  if (
    boat.missing.length
  ) {

    msg +=
      `\n\n⚠️ URL履歴なし：\n` +
      boat.missing.join(" / ");
  }


  await show(
    "✅ 公営これ一発 v14.1 完了",
    msg
  );


} catch(e) {

  console.error(e);

  await show(
    "❌ 公営これ一発 v14.1 エラー",
    String(e)
  );
}


Script.complete();