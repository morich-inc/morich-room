# morichの部屋 - ご案内ページ

Notion管理のイベント情報を毎日自動でWebに反映するシステムです。

## セットアップ手順

### 1. Notionでインテグレーションを作成

1. https://www.notion.so/my-integrations を開く
2. 「新しいインテグレーション」を作成（名前: `morich-no-heya-web`）
3. 表示された **Internal Integration Secret**（`secret_xxx...`）をコピーして保存

### 2. Notionデータベースを共有

イベント管理データベースを開き、右上「...」→「コネクト」→ 作成したインテグレーションを追加

#### データベースに必要なプロパティ（列名）

| プロパティ名 | 種類 | 説明 |
|---|---|---|
| 名前（タイトル） | タイトル | （自動）ゲスト名でも可 |
| Vol | 数値 | Vol番号 |
| 開催日 | 日付 | 開催日 |
| ゲスト名 | テキスト | ゲストの氏名 |
| 会社名・役職 | テキスト | 会社名と役職をまとめて1列（例：株式会社〇〇 代表取締役CEO） |
| 申込URL | URL | Googleフォーム等のURL |
| YouTubeURL | URL | アーカイブ動画URL |
| ステータス | セレクト | 募集中 / 満員 / 終了 / キャンセル |
| 説明 | テキスト | イベントの補足説明（任意） |

#### データベースIDの確認方法

データベースを開いたときのURL:
```
https://www.notion.so/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx?v=...
```
`?v=` の前の部分（32文字）がデータベースIDです。

### 3. GitHubリポジトリにSecretsを設定

リポジトリの **Settings → Secrets and variables → Actions** を開き、以下を追加:

| Secret名 | 値 |
|---|---|
| `NOTION_TOKEN` | `secret_xxx...`（手順1でコピーしたトークン） |
| `NOTION_DB_ID` | データベースのID（手順2で確認） |

### 4. GitHub Pagesを有効化

リポジトリの **Settings → Pages** を開き:
- Source: `Deploy from a branch`
- Branch: `main` / `/ (root)`
- Save

数分後に `https://[ユーザー名].github.io/[リポジトリ名]/` でアクセス可能になります。

### 5. ロゴ画像を配置

`assets/logo.png` に `・morichの部屋・.png` をコピーして配置してください。

---

## 使い方

### 自動更新
毎日 **午前8時（日本時間）** にNotionから自動取得してページを更新します。

### 手動更新
GitHubの **Actions タブ** → `Notion → GitHub Pages 自動更新` → `Run workflow` で即時更新できます。

### URLの共有
GitHub PagesのURLをご案内したい方にだけお伝えください。
robots.txtでGoogle等の検索エンジンには登録されないよう設定済みです。

---

## ファイル構成

```
web-project/
├── index.html                    ← 自動生成されるページ
├── robots.txt                    ← 検索エンジン非公開設定
├── assets/
│   ├── style.css                 ← デザイン
│   └── logo.png                  ← ロゴ（要配置）
├── scripts/
│   └── build.py                  ← Notion取得 → HTML生成スクリプト
└── .github/workflows/
    └── sync.yml                  ← GitHub Actions（自動更新）
```
