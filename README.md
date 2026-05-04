# RIGOL DS1104Z LAN 測定ヘルパー

RIGOL DS1104Z オシロスコープを LAN/LXI 経由で Python/SCPI 制御するための Codex Skill と Python ツール集です。

組み込みハードウェアの信号測定で、スクリーンショット PNG、波形 CSV、setup JSON、Markdown レポートをセットで保存し、あとから測定条件と判断根拠を追えるようにすることを目的にしています。

## ライセンス

MIT License で公開しています。詳細は [LICENSE](LICENSE) を参照してください。

## 必要なもの

- RIGOL DS1104Z または DS1000Z 系の互換オシロスコープ
- LAN 接続
- `uv`

Skill 単体配布でも使えるように、実行例は `uv run --with pyvisa --with pyvisa-py ...` を基本にしています。
このリポジトリ自体を開発する場合は、固定された依存関係を使うために `uv sync` も利用できます。

```bash
uv sync
```

IP アドレスなどの個人環境に固有の情報は、commit しないローカル設定ファイルに書きます。このリポジトリ内で使う場合は、作業ディレクトリの `config/rigol.env` を使えます。

```bash
cp config/rigol.example.env config/rigol.env
$EDITOR config/rigol.env
```

`config/rigol.env` の例:

```bash
RIGOL_IP=<YOUR_IP_ADDR>
```

`config/rigol.env` は `.gitignore` で除外されています。実IPやシリアル番号など、個人環境に固有の情報は README や commit 済みファイルに書かないでください。

Skill を個人用にコピーして別プロジェクトから使う場合は、共通設定として `~/.config/rigol-ds1104z-lan/rigol.env` を使うのが便利です。

```bash
mkdir -p ~/.config/rigol-ds1104z-lan
cp ~/.codex/skills/rigol-ds1104z-lan/config/rigol.example.env ~/.config/rigol-ds1104z-lan/rigol.env
$EDITOR ~/.config/rigol-ds1104z-lan/rigol.env
```

`--ip` を省略した場合、ツールは次の順に `RIGOL_IP` を探します。

1. 現在の作業ディレクトリの `config/rigol.env`
2. `~/.config/rigol-ds1104z-lan/rigol.env`
3. Skill ディレクトリ内の `config/rigol.env`
4. shell environment の `RIGOL_IP`

## 確認済みの実機

この作業環境では、以下の実機と通信できることを確認済みです。

```text
RIGOL TECHNOLOGIES,DS1104Z Plus,<YOUR_SERIAL>,00.04.05.SP2
```

`<YOUR_IP_ADDR>` では次の両方で `*IDN?` が成功しました。

```text
TCPIP0::<YOUR_IP_ADDR>::INSTR
TCPIP0::<YOUR_IP_ADDR>::5555::SOCKET
```

通常は `INSTR` を優先し、失敗した場合だけ socket mode を試してください。

## クイックスタート

LAN/SCPI 通信を確認します。

```bash
uv run --with pyvisa --with pyvisa-py python .codex/skills/rigol-ds1104z-lan/scripts/rigol_check_lan.py --ip <YOUR_IP_ADDR>
uv run --with pyvisa --with pyvisa-py python .codex/skills/rigol-ds1104z-lan/scripts/rigol_check_lan.py --ip <YOUR_IP_ADDR> --socket
```

上記いずれかの設定ファイルに `RIGOL_IP` を設定済みなら `--ip` は省略できます。

```bash
uv run --with pyvisa --with pyvisa-py python .codex/skills/rigol-ds1104z-lan/scripts/rigol_check_lan.py
uv run --with pyvisa --with pyvisa-py python .codex/skills/rigol-ds1104z-lan/scripts/rigol_check_lan.py --socket
```

スクリーンショットを保存します。

```bash
uv run --with pyvisa --with pyvisa-py python .codex/skills/rigol-ds1104z-lan/scripts/rigol_screenshot.py --ip <YOUR_IP_ADDR> --outdir captures
```

または:

```bash
uv run --with pyvisa --with pyvisa-py python .codex/skills/rigol-ds1104z-lan/scripts/rigol_screenshot.py --outdir captures
```

CH1 の falling edge を single-shot capture します。

```bash
uv run --with pyvisa --with pyvisa-py python .codex/skills/rigol-ds1104z-lan/scripts/rigol_single_capture.py \
  --ip <YOUR_IP_ADDR> \
  --channel CHAN1 \
  --slope falling \
  --level 1.5 \
  --outdir captures
```

`RIGOL_IP` 設定済みの場合:

```bash
uv run --with pyvisa --with pyvisa-py python .codex/skills/rigol-ds1104z-lan/scripts/rigol_single_capture.py \
  --channel CHAN1 \
  --slope falling \
  --level 1.5 \
  --outdir captures
```

別の設定ファイルを使う場合は `--config` を指定します。

```bash
uv run --with pyvisa --with pyvisa-py python .codex/skills/rigol-ds1104z-lan/scripts/rigol_check_lan.py --config config/lab-a.env
```

CH1 の rising edge を single-shot capture します。

```bash
uv run --with pyvisa --with pyvisa-py python .codex/skills/rigol-ds1104z-lan/scripts/rigol_single_capture.py \
  --ip <YOUR_IP_ADDR> \
  --channel CHAN1 \
  --slope rising \
  --level 1.5 \
  --outdir captures
```

表示中の CH1 波形を CSV に保存します。

```bash
uv run --with pyvisa --with pyvisa-py python .codex/skills/rigol-ds1104z-lan/scripts/rigol_waveform_csv.py \
  --ip <YOUR_IP_ADDR> \
  --channel CHAN1 \
  --outdir captures
```

## 測定ワークフロー

1. DS1104Z の LAN 設定画面で IP アドレスを確認する。
2. `rigol_check_lan.py` で `*IDN?` を確認する。
3. 測定対象の端子、GND、プローブ倍率、使用 CH、トリガ条件を決める。
4. GPIO、logic、switch、sensor、power rail はまず DC coupling で測る。
5. AUTO setup に依存せず、CH、timebase、trigger、waveform 設定を明示する。
6. スクリーンショット PNG と setup JSON を保存する。
7. 波形 CSV を保存する。
8. `.codex/skills/rigol-ds1104z-lan/references/signal_capture_report.md` の形式で Markdown レポートを書く。

スクリーンショットだけで電圧や時間を断定しないでください。波形 CSV は `:WAV:PRE?` を parse してから time/voltage に変換します。

## ツール

### `rigol_check_lan.py`

`*IDN?` を query して、DS1104Z と通信できるか確認します。

```bash
uv run --with pyvisa --with pyvisa-py python .codex/skills/rigol-ds1104z-lan/scripts/rigol_check_lan.py --ip <YOUR_IP_ADDR>
uv run --with pyvisa --with pyvisa-py python .codex/skills/rigol-ds1104z-lan/scripts/rigol_check_lan.py --ip <YOUR_IP_ADDR> --socket
```

### `rigol_screenshot.py`

`:DISP:DATA? PNG` でスクリーンショットを取得し、timestamp 付き PNG と JSON metadata を `captures/` に保存します。

```bash
uv run --with pyvisa --with pyvisa-py python .codex/skills/rigol-ds1104z-lan/scripts/rigol_screenshot.py --ip <YOUR_IP_ADDR>
```

### `rigol_single_capture.py`

single-shot edge trigger を設定し、指定秒数待ってから停止し、スクリーンショット PNG と setup JSON を保存します。

デフォルト値:

- Channel: `CHAN1`
- Coupling: `DC`
- Probe: `10x`
- Vertical scale: `1 V/div`
- Time scale: `5 ms/div`
- Trigger level: `1.5 V`

```bash
uv run --with pyvisa --with pyvisa-py python .codex/skills/rigol-ds1104z-lan/scripts/rigol_single_capture.py --ip <YOUR_IP_ADDR> --channel CHAN1 --slope falling
```

### `rigol_waveform_csv.py`

`:STOP` 後、`:WAV:PRE?` を読み、`:WAV:DATA?` の binary block を取得して `time_s,voltage_v,adc` CSV と JSON metadata を保存します。

```bash
uv run --with pyvisa --with pyvisa-py python .codex/skills/rigol-ds1104z-lan/scripts/rigol_waveform_csv.py --ip <YOUR_IP_ADDR> --channel CHAN1
```

## Codex Skill として使う

このリポジトリには Codex Skill が同梱されています。

```text
.codex/skills/rigol-ds1104z-lan/
```

### このリポジトリ内だけで使う

Codex がプロジェクト内の `.codex/skills/` を読む環境では、リポジトリを開くだけで project skill として使えます。
この使い方では、Skill は測定手順、注意事項、レポート形式を Codex に教え、実際の通信や保存処理は Skill 配下の `.codex/skills/rigol-ds1104z-lan/scripts/*.py` を `uv run --with pyvisa --with pyvisa-py python ...` で実行します。

つまり、このリポジトリは「Codex Skill」と「その Skill に同梱された Python ツール集」をセットで配布する構成です。

Skill を明示して依頼する例:

```text
$rigol-ds1104z-lan DS1104ZでCH1のsingle-shot測定をしたい。プローブ位置から指示して。
```

または通常の依頼文でも、内容が一致すれば Skill が自動で使われます。

```text
RIGOL DS1104ZをLANで制御して、CH1の波形CSVとスクリーンショットを保存して。
```

### 個人用 Codex Skill として登録する

全プロジェクトで使いたい場合は、Skill ディレクトリを `~/.codex/skills/` にコピーします。

```bash
mkdir -p ~/.codex/skills
cp -R .codex/skills/rigol-ds1104z-lan ~/.codex/skills/
```

登録後、Codex を再起動してください。

この方法では、Skill 本体と同時に `.codex/skills/rigol-ds1104z-lan/scripts/` の Python ツールもコピーされます。`pyproject.toml`、`uv.lock` はコピーされませんが、通常の測定コマンドは Skill 配下の `scripts/` から実行できます。

個人用 Skill として登録した場合の実行例:

```bash
uv run --with pyvisa --with pyvisa-py python ~/.codex/skills/rigol-ds1104z-lan/scripts/rigol_check_lan.py
```

この実行方法は作業ディレクトリに依存しないため、別プロジェクトを開いている状態でも使えます。ローカル設定ファイルを使う場合は、`~/.config/rigol-ds1104z-lan/rigol.env` に置くか、`--config <path>` で明示してください。

### GitHub から Codex にインストールする

このリポジトリを GitHub で公開した後は、Codex の `$skill-installer` に GitHub のディレクトリ URL を渡してインストールできます。

```text
$skill-installer install https://github.com/fooping-tech/rigol_ds1104/tree/main/.codex/skills/rigol-ds1104z-lan
```

インストール後は Codex を再起動します。

## Claude Code Skill として使う

Claude Code の Skills は、次の場所から自動検出されます。

- Project Skills: `.claude/skills/`
- Personal Skills: `~/.claude/skills/`
- Plugin Skills: installed plugin に同梱された Skills

この Skill は `SKILL.md` 形式なので、同じ中身を Claude Code にも登録できます。

### このリポジトリの Claude project skill として登録する

リポジトリ内で Claude Code に使わせたい場合は、`.claude/skills/` にコピーします。

```bash
mkdir -p .claude/skills
cp -R .codex/skills/rigol-ds1104z-lan .claude/skills/
```

この方法は project skill なので、`.claude/skills/rigol-ds1104z-lan/` を git に commit すれば、チームメンバーも同じ Skill を使えます。

### 個人用 Claude Code Skill として登録する

全プロジェクトで使いたい場合は、`~/.claude/skills/` にコピーします。

```bash
mkdir -p ~/.claude/skills
cp -R .codex/skills/rigol-ds1104z-lan ~/.claude/skills/
```

Claude Code を起動済みの場合は、再起動して Skill を読み直してください。

### Claude Code で確認する

Claude Code 上で次のように聞くと、利用可能な Skills を確認できます。

```text
List all available Skills
```

Skill が見えていれば、通常の依頼文で自動的に使われます。環境によっては slash command として次のように呼び出せます。

```text
/rigol-ds1104z-lan DS1104ZのLAN接続確認をして
```

## プローブ接続ガイド

測定前に、必ず次を明確にしてください。

- Signal node: 物理 pin、pad、connector、test point、部品端子
- Ground reference: 近くの board GND。GND lead は短くする
- Channel assignment: `CHAN1` から `CHAN4`
- Probe attenuation: 通常は `10x`
- Coupling: 組み込み信号はまず `DC`
- Trigger: source、slope、level、期待する event

例:

- MCU GPIO: MCU pin または最寄りの accessible pad に probe tip を当てる。
- Power rail: regulator output だけでなく、負荷側 VDD pin でも測る。
- I2C/SPI/UART: threshold や ringing を見る場合は receiver 側 pin で測る。
- PWM/load: まず controller output を測り、必要なら load 側 node も測る。

## 検証

ローカル構文チェック:

```bash
uv run python -m py_compile .codex/skills/rigol-ds1104z-lan/scripts/*.py
uv run --with pyvisa --with pyvisa-py python .codex/skills/rigol-ds1104z-lan/scripts/rigol_check_lan.py --help
```

実機通信は `INSTR` と socket mode の両方で確認してください。制限された実行環境では ICMP `ping` が失敗しても、SCPI 通信は成功する場合があります。

## 参考リンク

- Codex Skills catalog: https://github.com/openai/skills
- Claude Code Agent Skills: https://docs.claude.com/en/docs/claude-code/skills
