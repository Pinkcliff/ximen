# Git Push 推送失败问题解决记录

## 问题描述

执行 `git push` 时出现以下错误：

```
fatal: unable to access 'https://github.com/xxx.git/': Failed to connect to github.com port 443 via 127.0.0.1:10809 after 2023 ms: Could not connect to server
```

## 原因分析

Git 配置了代理（`http://127.0.0.1:10809`），但代理服务可能未正常启动或无法连接。

## 解决方案

### 方案1：检查代理服务是否启动

确认代理软件（如 Clash、V2Ray 等）是否正在运行，端口是否正确。

### 方案2：临时取消代理推送（推荐）

如果代理正常但仍无法连接，可以临时取消代理：

```bash
git config --global --unset http.proxy
git config --global --unset https.proxy
git push
```

推送成功后，如需恢复代理设置：

```bash
git config --global http.proxy http://127.0.0.1:10809
git config --global https.proxy http://127.0.0.1:10809
```

## 快速诊断命令

```bash
# 查看当前代理配置
git config --global --get http.proxy
git config --global --get https.proxy

# 测试连接
ping github.com
```

## 发生时间

2026-04-10 - 项目 ximen

## 解决结果

✅ 使用方案2成功推送到远程仓库
