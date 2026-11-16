# 観光サイトのコピー・移管記録

2026-11-16（JST）、[Issue #7](https://github.com/lecture-high-school-ai-team/ch04-04-materials/issues/7)。ユーザーの「そのままコピーする形で移行」の指示に基づき、元の3ファイルを変更せずに保存しました。

- コピー元：[funakoshi-takehiro/high-school-ai-4-test](https://github.com/funakoshi-takehiro/high-school-ai-4-test/tree/3db25752a837e1603bb5216a13b0080564666808)
- コピー元の固定コミット：`3db25752a837e1603bb5216a13b0080564666808`
- コピー先：[site/](../../site/)
- [サイトだけのZIP](../../downloads/まついわ町_観光ガイド.zip)
- [全ファイルのハッシュ・来歴](copy-record.json)

`site/README.md`・`site/index.html`・`site/style.css` は、元の追跡ファイルとバイト単位で同一です。元のHTML・CSS・8施設・91件の口コミを変更していません。元のREADMEも、原文のまま保存しています。サイト専用ZIPには同じ3ファイルを収録しました。

## 開き方

サイト専用ZIPのGitHubファイル画面で「Download raw file（↓）」を押して保存し、展開した `index.html` をブラウザーで開きます。リポジトリ全体を「Code」→「Download ZIP」で保存した場合は、展開後の `site/index.html` を開きます。CSSは同じフォルダに置いてください。

このリポジトリは非公開で、GitHub Pagesは未設定です。ここでの移行はファイルの格納先の移管です。Web公開URLの切替、教材2・3コマのリンク・QRの差替え、移行元の削除は実施していません。元の公開サイトの停止やリポジトリの公開化・プラン変更も行っていません。

## 表示・配布の確認

[ブラウザー確認結果](browser-result.json)と[PC画面](pc.png)・[狭い画面](mobile.png)を保存しました。

- Chromiumで元とコピー先の実ファイルをローカルHTTP配信し、1440pxと390pxで表示しました。同じ画面幅でスクリーンショットが画素単位で一致し、横はみ出しはありませんでした。
- 8施設・91件の口コミ、ページ内リンクによる移動、口コミの展開を確認しました。外部への通信要求は0件です。
- `file://` の直接確認は管理環境の `ERR_BLOCKED_BY_ADMINISTRATOR` で未確認です。ローカルHTTPの確認を、利用者のPCでのfile URL実測へ置き換えていません。
- ZIP内の3ファイルを展開してコピー元との実バイト・SHA-256を照合しています。

既存4コマのNotebook・データ・画像・コード・元の照合記録は維持しています。rootのREADMEには観光サイトの入口を末尾に追記し、元の本文はバイト単位で保持しました。CIは既存v10のファイル検査を継続し、追加したサイト・ZIPとREADME追記を別に検証します。新しい教材版は作成していません。

適用したGitHub規約の取得元は `lecture-high-school-ai-team/high-school-ai` の `0d7b7f138a489bb80335036f8579cf0be365db32` です。担当Codex、移行先の起点mainは `f218238d42c4b2a713c6f060a3a5abaf1c4386ed`。PR・CI・main統合後のGitHub実ファイル再取得はIssue #7に記録します。

再検査は `python checks/tourism-site-copy/validate.py`、ブラウザー比較はPlaywright/Chromiumを備えた環境で `python checks/tourism-site-copy/browser_check.py --source コピー元の固定コミットの作業フォルダ` を使います。
