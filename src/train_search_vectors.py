"""Pretrain a small, reproducible skip-gram/negative-sampling model.

The synthetic, tokenized tourism corpus is authored for this lesson. There are
no imported pretrained weights and no manually assigned similarity scores.
NumPy is a build-time dependency only; learners use the exported numeric table.
"""
from pathlib import Path
from collections import Counter
import hashlib, json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / ('data/search' if Path(__file__).parent.name == 'src' else 'data/search_v6')
DEST.mkdir(parents=True, exist_ok=True)
SEED = 260623

# Each group supplies interchangeable vocabulary in shared tourism contexts.
# These are synthetic teaching sentences, not evidence about real visitors.
GROUPS = [
    ('休息 休憩 リラックス 休む くつろぐ のんびり 癒やし', '温泉 日帰り 湯 観光 疲れ 途中'),
    ('眺望 景色 眺め 見渡せる 展望 絶景', '灯台 丘 港 海 坂道 写真'),
    ('散策 散歩 歩く 歩き ゆっくり', '竹林 小道 木陰 自然 静か 写真'),
    ('静か 落ち着く 穏やか 静けさ', '竹林 小道 自然 木陰 散歩 ゆっくり'),
    ('歴史 昔 文化 学ぶ 学習', '資料館 公園 城 地域 展示 紹介'),
    ('食事 食べる グルメ おやつ 軽食', '市場 朝市 魚 野菜 地元 店 買い物'),
    ('買い物 土産 お土産 贈り物 ショッピング', '商店街 店 軽食 地元 めぐり 食'),
    ('生物 生き物 動物 観察 見学', '水族館 海 屋内 展示 近く 人気'),
    ('海辺 海岸 砂浜 浜辺 ビーチ', '海 白い 自然 景色 眺め 休憩'),
    ('温泉 入浴 湯 風呂 日帰り', '屋内 観光 途中 休憩 リラックス 休息'),
    ('写真 撮影 撮れる カメラ', '景色 自然 竹林 灯台 丘 港'),
]
sentences = []
for choices, context in GROUPS:
    words, anchors = choices.split(), context.split()
    for word in words:
        for i in range(len(anchors)):
            # Swap a focal word into repeated contexts; no place IDs or ranks.
            sentences.append([anchors[i], anchors[(i + 1) % len(anchors)], word,
                              anchors[(i + 2) % len(anchors)], anchors[(i + 3) % len(anchors)]])

freq = Counter(w for s in sentences for w in s)
vocab = sorted(freq)
idx = {w: i for i, w in enumerate(vocab)}
pairs = []
for sentence in sentences:
    for i, word in enumerate(sentence):
        for j in range(max(0, i - 2), min(len(sentence), i + 3)):
            if i != j:
                pairs.append((idx[word], idx[sentence[j]]))
pairs = np.asarray(pairs, dtype=np.int32)
rng = np.random.default_rng(SEED)
dim, negative, epochs, batch_size = 32, 5, 180, 256
vectors = rng.normal(0, .06, (len(vocab), dim))
contexts = rng.normal(0, .06, (len(vocab), dim))
noise = np.asarray([freq[w] ** .75 for w in vocab], dtype=float)
noise /= noise.sum()
losses = []
for epoch in range(epochs):
    order = rng.permutation(len(pairs))
    lr = .035 * (1 - .85 * epoch / epochs)
    loss = 0.
    for start in range(0, len(order), batch_size):
        p = pairs[order[start:start + batch_size]]
        center, positive = p[:, 0], p[:, 1]
        neg = rng.choice(len(vocab), (len(p), negative), p=noise)
        # A sampled negative must not equal the positive context.
        bad = neg == positive[:, None]
        while bad.any():
            neg[bad] = rng.choice(len(vocab), int(bad.sum()), p=noise)
            bad = neg == positive[:, None]
        target = np.column_stack([positive, neg])
        labels = np.zeros_like(target, dtype=float); labels[:, 0] = 1.
        vin, vout = vectors[center].copy(), contexts[target].copy()
        logits = np.einsum('bd,bkd->bk', vin, vout)
        predicted = 1 / (1 + np.exp(-np.clip(logits, -30, 30)))
        error = predicted - labels
        grad_in = np.einsum('bk,bkd->bd', error, vout)
        grad_out = error[:, :, None] * vin[:, None, :]
        np.add.at(vectors, center, -lr * grad_in)
        np.add.at(contexts, target.ravel(), -lr * grad_out.reshape(-1, dim))
        loss += float(np.sum(np.logaddexp(0, logits) - labels * logits))
    if epoch in (0, 59, 119, 179): losses.append({'epoch': epoch + 1, 'loss_per_pair': loss / len(pairs)})
vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
corpus = {'kind': 'synthetic teaching corpus', 'tokenization': 'space-separated tokens authored in advance',
          'sentences': [' '.join(s) for s in sentences]}
corpus_bytes = (json.dumps(corpus, ensure_ascii=False, indent=1) + '\n').encode()
(DEST / 'training_corpus.json').write_bytes(corpus_bytes)
model = {'format': 'matsuiwa-word-vectors-1', 'algorithm': 'skip-gram with negative sampling',
         'dimensions': dim, 'words': {w: [round(float(v), 7) for v in vectors[i]] for i, w in enumerate(vocab)}}
(DEST / 'word_vectors.json').write_text(json.dumps(model, ensure_ascii=False, separators=(',', ':')) + '\n')
provenance = {'source': '本教材用の合成観光文から制作時に事前学習。第三者の学習済み重みは使用していません。',
              'algorithm_reference': 'Mikolov et al. (2013), Distributed Representations of Words and Phrases and their Compositionality, section 2.2.',
              'reference_url': 'https://arxiv.org/abs/1310.4546',
              'implementation': 'このリポジトリ用に作成したNumPy実装。外部実装のコードを転記していません。',
              'redistribution': '第三者モデルの再配布条件はありません。新作の学習文・コード・数値の公開条件は本リポジトリの公開方針に従います。今回は非公開で、第4章完成後の公開判断を保留します。',
              'seed': SEED, 'epochs': epochs, 'dimensions': dim, 'negative_samples': negative,
              'window': 2, 'words': len(vocab), 'sentences': len(sentences), 'training_pairs': len(pairs),
              'training_loss': losses, 'corpus_sha256': hashlib.sha256(corpus_bytes).hexdigest(),
              'vectors_sha256': hashlib.sha256((DEST / 'word_vectors.json').read_bytes()).hexdigest(),
              'limitations': ['合成の小規模語彙で、一般的な日本語の意味理解能力を評価するモデルではありません。',
                              '類似度は正解率・好みの確率ではありません。',
                              '未知語・否定・細かな条件や語順を扱う汎用の文章モデルではありません。',
                              '学習は制作時だけ。生徒は同梱表を読み、外部通信なしで計算します。']}
(DEST / 'provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(provenance, ensure_ascii=False, indent=2))
