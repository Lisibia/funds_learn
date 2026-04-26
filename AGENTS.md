# AGENTS.md

This file provides guidance to codeflicker when working with code in this repository.

## WHY: Purpose and Goals
`funds_learn` 是一个基金/ETF 回测学习项目，当前重点是 `fund_traceback/` 多文件基金回测模块。它用于验证买入持有与再平衡策略在历史净值数据上的表现，并输出收益、回撤、夏普率和图表结果。

## WHAT: Technical Stack
- Runtime/Language: Python 3.14（本地 `venv`）
- Data/Analysis: pandas, numpy
- Visualization: matplotlib
- Market Data: Tushare（基金净值、基金名称）
- Project shape: 根目录脚本 + `fund_traceback/` 包
- Recommended module: `fund_traceback/`
- Legacy scripts: `main.py`, `main_fund.py`, `index_find.py`

## HOW: Core Development Workflow
```bash
# Run the main fund backtest package
./venv/bin/python -m fund_traceback.main

# Syntax-check core modules
./venv/bin/python -m py_compile fund_traceback/*.py

# Run legacy ETF script
python3 main.py

# Run legacy fund script
python3 main_fund.py
```

## Progressive Disclosure

For detailed information, consult these documents as needed:

- `docs/agent/development_commands.md` - All runnable project commands
- `docs/agent/architecture.md` - Module structure and architectural patterns
- `docs/agent/testing.md` - Current test status and recommended test setup

**When working on a task, first determine which documentation is relevant, then read only those files.**
