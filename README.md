# jb

GPU 服务器上的轻量后台任务管理工具. 单文件 Python, 只依赖标准库 (Python ≥ 3.8, Linux).

- `jb submit` 提交即返回, 任务脱离终端运行, 断开 SSH 也不影响
- 从日志自动识别进度并估算 ETA (tqdm / `step 12/100` / 自定义)
- 网页面板: GPU 利用率、显存、进程, 任务进度与日志
- 任务结束推送到微信 / QQ / 手机, 或 Mac 本地通知

## 安装到服务器

```bash
git clone https://github.com/whoisKIWIIZZZ/jb.git ~/.local/share/jb
~/.local/share/jb/install.sh          # 链接到 ~/.local/bin/jb
```

更新: `cd ~/.local/share/jb && git pull`.

> 通过 `ssh host 'cmd'` 远程执行时 PATH 通常不含 `~/.local/bin`, 请写全路径 `~/.local/bin/jb`.

## 常用命令

```bash
jb submit -n train -g 0 -- python train.py --lr 1e-3   # 提交
jb                                                     # 列表: 状态 / 进度 / ETA
jb show 3                                              # 详情 + 日志尾部
jb log 3 -n 100 [-f] [--grep loss]                     # 日志
jb kill 3 / jb retry 3 / jb wait 3                     # 终止 / 重跑 / 阻塞等待
jb submit --after 3 -- python eval.py                  # 等任务 3 成功后再跑
jb gpu                                                 # GPU 占用及对应任务
```

**进度识别** (优先级从高到低): 脚本打印 `[jb] progress 120/1000` → 提交时 `--total 30000` (配合 `--pattern`, 默认匹配 `step 123`) → 日志里的 `epoch 3/10`、`step 12/100` → tqdm 进度条.

## 分组 / 归档 / 批量清理

```bash
jb submit -G lf5 -n lf5-gated -- ...         # 提交时指定分组
jb group lf5 208-211                         # 设分组 (ID 可写 208-211 / 208,210); jb group - ID 清除
jb groups                                    # 各分组任务数
jb archive 201-207 / jb unarchive 203        # 归档后 jb ls 和面板默认隐藏; jb ls -A 带上, --archived 只看归档
jb ls -G lf5                                 # 只看某分组 (含全部历史)
jb rm --match smoke --status done,failed     # 按名称正则 / 状态 / -G 分组批量删除, 会先列出再确认 (-y 跳过)
```

运行中 / 排队中的任务不会被归档或删除. 标注存放在 `~/.jb/jobs/<ID>/label.json`, 不改动 runner 读写的 meta.json.
面板里: 最近 / 运行中 / 全部 / 已归档 四个标签页, 搜索, 分组筛选与按分组折叠, 勾选 (Shift 连选) 后批量设分组、按名称前缀自动分组、归档、删除; 勾选 \"隐藏 GPU\" 进入纯管理视图.

## 配置 `~/.jb/config.json`

限制可用 GPU (可选, 默认不限制):

```json
{"default_gpus": "0,1", "allowed_gpus": "0,1"}
```

## 结束推送

```bash
jb notify set qmsg <KEY>              # QQ (qmsg.zendee.cn)
jb notify set serverchan <SendKey>    # 微信 (sct.ftqq.com)
jb notify set pushplus <token>        # 微信 (pushplus.plus)
jb notify set bark https://api.day.app/<KEY>   # iPhone
jb notify set ntfy https://ntfy.sh/<topic>
jb notify test
```

运行不到 60 秒的任务默认不推送; `submit --notify` 强制推送, `--no-notify` 关闭.

## 网页面板

```bash
jb serve -d          # 后台启动, 只监听 127.0.0.1:18765
jb serve --stop
```

在本地电脑上通过 SSH 隧道访问:

```bash
ssh -N -L 18765:127.0.0.1:18765 user@server   # 然后打开 http://127.0.0.1:18765/
```

**Mac 常驻 (推荐)**: 登录自启、断线自动重连, 任务结束弹系统通知. 需要 SSH 免密 (密钥) 登录.

```bash
git clone https://github.com/whoisKIWIIZZZ/jb.git && cd jb
mac/install.sh user@server -p 22      # 卸载: mac/install.sh --uninstall
```

服务器重启后自动拉起面板: `crontab -e` 加一行 `@reboot $HOME/.local/bin/jb serve -d`.

## 数据位置

任务记录和日志在 `~/.jb/jobs/<ID>/` (可用 `JB_HOME` 修改), 清理: `jb rm ID` / `jb clean --days 14`.

## License

MIT
