# 公開用の検証ログ

## FEVERを実機へ書き込んだときの記録

- [ホスト側の113項目](host-fever.log)
- [ビルド](build-fever.log)
- [ハッシュ検証を含む書き込み](flash-fever.log)
- [起動後のシリアル出力](runtime-fever.log)

ビルド時のアプリ容量は522,337 bytes、静的RAMは25,772 bytesです。
実機ログでは240×240、32フレーム、64カウント／周、FEVERの起動を確認できます。
実機ログの描画時間は待機中のサンプルであり、最大段階の連続FPSを示しません。
FEVERの派手さと最大段階の性能評価は未完了です。

## 公開用整理後の再確認

- [既存113項目の再実行](host-publication.log)
- [固定した依存関係での再ビルド](build-publication.log)
- [Gitに登録したファイルだけの作業ツリーでのビルド](build-clean-publication.log)
- [同梱PNG原本からのパック再生成](package-publication-check.log)

commit `3a4889c`を`git archive`で別フォルダへ展開し、113項目のモデルテストとビルドが成功しました。
ビルドではPlatformIOの共有ダウンロードキャッシュを利用しています。
同梱の32枚から再生成したパックは、レビュー済み配布パックとバイト単位で一致しました。

整理後にファームウェアを書き直してはいません。
公開のために変更した箇所は依存バージョン、Pythonツールの書式と既定パス、資料です。
配布アセットのSHA256は次の値を維持しています。

```text
9b483a188286b83aa35b9bf2f39bcd258c5fb1aeb6e30c824a75b820232fa167
```

## ログの取り扱い

絶対パス、デバイスMACアドレス、シリアルポート名を置き換えています。
元ログと公開版のSHA256は[manifest.json](manifest.json)に収録しました。
元の`logs/`と中間ファイルは開発環境に保持し、Gitの対象から外しています。
試行錯誤を含む過去の記録は[VALIDATION.md](../VALIDATION.md)を参照してください。
