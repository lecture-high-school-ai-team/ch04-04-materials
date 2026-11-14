"""まついわ観光サイト。教材用の架空のサービス。"""
import copy
import html
import json
import math
import re
from collections import Counter
from library_hiroba import ui


class Matsuiwa:
    def __init__(self, data, task="start"):
        self.data = copy.deepcopy(data)
        self.task = task
        self.entries = []
        self.favorites = set()
        self.photo_keys = list(self.data["photos"])
        self.bugs = task in ("start", "A")

    def home(self):
        cards = []
        for place in self.data["places"]:
            reviews = [r for r in self.data["reviews"] if r["place_id"] == place["id"]]
            average = sum(r["rating"] for r in reviews) / len(reviews) if reviews else None
            rating_text = f"★{average:.1f}" if average is not None else "口コミなし"
            cards.append(
                f'<article><span class="category">{html.escape(place["category"])}</span>'
                f'<h3>{html.escape(place["name"])}</h3>'
                f'<p>{html.escape(place["intro"])}</p>'
                f'<p>{rating_text}　口コミ {len(reviews)}件</p>'
                f'<p>{html.escape(place["hours"])} ／ {place["fee"]}円</p></article>'
            )
        return ui.html(
            '<main class="matsuiwa"><header><p>MATSUIWA / 架空の観光案内</p>'
            '<h1>まついわ、次の寄り道。</h1>'
            '<p>気になる施設と、訪れた人の声を見つけてみましょう。</p></header>'
            '<div class="place-grid">' + ''.join(cards) + '</div></main>',
            css="""
            .matsuiwa { width:1100px; font-family: sans-serif; color:#1b3448; }
            .matsuiwa header { background:#e9f3f1; padding:28px; border-radius:12px; }
            .matsuiwa h1 { font-size:32px; margin:10px 0; }
            .matsuiwa .place-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:16px; margin-top:20px; }
            .matsuiwa article { padding:20px; border:1px solid #9bb1b8; border-radius:12px; background:white; }
            .matsuiwa .category { color:#176f7a; font-weight:normal; }
            """,
        )

    def detail(self, place):
        selected = next(p for p in self.data["places"] if p["name"] == place)
        if self.bugs:
            selected = self.data["places"][0]
        rows = [r for r in self.data["reviews"] if r["place_id"] == selected["id"]]
        # 新しい投稿から表示します。
        rows = sorted(rows, key=lambda r: r["date"], reverse=True)
        return ui.stack(
            ui.card(selected["name"], selected["intro"]),
            ui.table([[r["id"], r["date"], r["rating"], r["text"]] for r in rows],
                     headers=["口コミID", "日付", "評価", "口コミ"]),
        )

    def browse_form(self):
        return ui.form(self.detail,
            ui.field("place", "施設を選択", kind="choice",
                     choices=[p["name"] for p in self.data["places"]]),
            submit_label="口コミを表示", clear_on_submit=False)

    def all_reviews(self):
        names = {p["id"]: p["name"] for p in self.data["places"]}
        rows = sorted(self.data["reviews"], key=lambda r:r["date"], reverse=True)
        return ui.table([[r["id"],names[r["place_id"]],r["rating"],r["text"]] for r in rows],
                        headers=["口コミID","施設","評価","口コミ"])

    def review(self, place, rating, text):
        selected = next(p for p in self.data["places"] if p["name"] == place)
        rating = int(rating)
        if not 1 <= rating <= 5 or not text.strip():
            return ui.alert("評価は1〜5、口コミは1文字以上で入力してください。", kind="warning")
        if self.bugs:
            self.data["reviews"] = []
        self.data["reviews"].append({"id": f"new-{len(self.data['reviews']) + 1}",
            "place_id": selected["id"], "date": "2026-06-29", "rating": rating,
            "text": text.strip(), "period": "授業中"})
        return ui.alert("口コミを投稿しました。", kind="success")

    def review_form(self):
        return ui.form(self.review,
            ui.field("place", "施設", kind="choice", choices=[p["name"] for p in self.data["places"]]),
            ui.field("rating", "評価（1〜5）", kind="number", default=4),
            ui.field("text", "口コミ", kind="multiline"), submit_label="投稿", clear_on_submit=False)

    def campaign(self):
        return ui.alert("キャンペーンの応募画面は、これから追加します。")

    def photo_preview(self, photo):
        item = self.data["photos"][photo]
        return ui.html(f'<figure><img alt="{html.escape(item["label"])}" '
                       f'src="{item["image"]}" style="width:320px;max-width:100%;height:auto;">'
                       f'<figcaption>{html.escape(item["label"])}</figcaption></figure>')

    def lookup_pass(self, pass_number):
        record = next((p for p in self.data["passes"] if p["number"] == pass_number.strip()), None)
        if record is None:
            return ui.alert("この観光パス番号は登録されていません。", kind="warning")
        return ui.alert("この観光パスは応募済みです。" if record["used"] else "この観光パスは応募できます。")

    def analysis(self):
        counts = Counter(r["period"] for r in self.data["reviews"])
        return ui.table([[key, value] for key, value in counts.items()], headers=["期間", "全施設の口コミ数"])

    def classify_photo(self, photo):
        return ui.alert("画像を見分ける処理は、これから追加します。")

    def keyword_matches(self, query):
        query = str(query).strip()
        if not query:
            return []
        return [place for place in self.data["places"] if query in place_text(place)]

    def keyword_search(self, query):
        if not str(query).strip():
            return ui.alert("探したい言葉を入力してください。", kind="warning")
        rows = self.keyword_matches(query)
        if not rows:
            return ui.alert("入力した文字列を含む施設紹介はありませんでした。")
        return ui.table([[p["name"], p["intro"]] for p in rows], headers=["施設", "紹介文"])

    def keyword_form(self):
        return ui.form(self.keyword_search,
            ui.field("query", "探したい言葉", default="休息"),
            submit_label="文字の一致で探す", clear_on_submit=False)

    def vectorize(self, text, query_mode=False):
        """同梱した学習済み単語ベクトルを平均します。学習・外部通信はしません。"""
        text = str(text).strip()
        words = self.data["search_model"]["words"]
        pattern = re.compile("|".join(re.escape(w) for w in sorted(words, key=len, reverse=True)))
        used = pattern.findall(text)
        rest = pattern.sub(" ", text)
        unknown = re.findall(r"[^\s、。！？!?・,./:：;；()（）「」]+", rest)
        unsupported = query_mode and any(w in text for w in ("ない", "なく", "以外", "除く", "避け"))
        if not used or unsupported:
            return {"vector": None, "used_words": used, "unknown_parts": unknown,
                    "reason": "否定や除外の条件には対応していません。" if unsupported else "収録されている言葉がありません。"}
        dim = self.data["search_model"]["dimensions"]
        avg = [sum(words[word][i] for word in used) / len(used) for i in range(dim)]
        norm = math.sqrt(sum(v * v for v in avg))
        if not norm:
            return {"vector": None, "used_words": used, "unknown_parts": unknown, "reason": "数値の近さを計算できません。"}
        return {"vector": [v / norm for v in avg], "used_words": used,
                "unknown_parts": unknown, "reason": ""}

    def search_words(self):
        return ui.card("検索に使える言葉", "、".join(sorted(self.data["search_model"]["words"])))

    def search_compare(self, query):
        return ui.alert("意味の近さで探す処理は、これから追加します。")

    def import_photo(self, photo_json):
        item = json.loads(photo_json)
        if not item["image"].startswith(("data:image/png;base64,", "data:image/jpeg;base64,")):
            raise ValueError("画像入力ページで作ったJSONを貼り付けてください。")
        if len(item["rgb"]) != 32 * 32 * 3 or any(type(v) is not int or not 0 <= v <= 255 for v in item["rgb"]):
            raise ValueError("32×32画素のRGBデータが必要です。")
        key = "自分の写真"
        self.data["photos"][key] = item
        self.photo_keys = list(self.data["photos"])
        return self.photo_preview(key)

    def public_info(self):
        places = []
        for place in self.data["places"]:
            item = dict(place)
            item["reviews"] = [r["text"] for r in self.data["reviews"]
                               if r["place_id"] == place["id"]][:5]
            places.append(item)
        return json.dumps(places, ensure_ascii=False)


def new_case(task="start"):
    """どの選択課題も、共通活動やほかの選択課題の完了を必要としません。"""
    app = Matsuiwa(CASE, task=task)
    if task != "A" and task != "start":
        app.data["reviews"] = [r for r in app.data["reviews"] if r["id"] not in ("r365", "r366", "r367")]
    if task != "start":
        app.campaign = lambda: campaign_form(app)
    return app


def place_text(place):
    return place["name"] + "。" + place["category"] + "。" + place["intro"]


def cosine_similarity(a, b):
    if a is None or b is None or len(a) != len(b):
        raise ValueError("同じ長さの数値の並びが必要です。")
    norm_a = math.sqrt(sum(v * v for v in a))
    norm_b = math.sqrt(sum(v * v for v in b))
    if norm_a == 0 or norm_b == 0:
        raise ValueError("すべて0の数値からは近さを計算できません。")
    return sum(x * y for x, y in zip(a, b)) / (norm_a * norm_b)


def stage_banner(task, stage):
    return ui.card(f"{task}：{stage}",
        "まず操作して、直したいところや調べたいことを見つけます。"
        if stage == "改善前" else
        "同じ操作をもう一度試し、変わった点と残った問題を確かめます。")


def campaign_snapshot(app):
    return {"entry_count": len(app.entries),
            "used": {p["number"]: bool(p["used"]) for p in app.data["passes"]}}


def campaign_state_report(app, before):
    after = campaign_snapshot(app)
    rows = [["保存された応募の件数", before["entry_count"], after["entry_count"]]]
    rows += [["観光パス " + number, "応募済み" if used else "未応募",
              "応募済み" if after["used"].get(number) else "未応募"]
             for number, used in before["used"].items()]
    return ui.stack(ui.card("操作前後のデータ", "不一致の入力では件数と状態が変わっていないか、表を見て確かめてください。"),
                    ui.table(rows, headers=["確かめる項目", "操作前", "操作後"]))
