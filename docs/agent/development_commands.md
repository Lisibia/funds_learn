# development_commands

## Main commands

### Recommended module
```bash
./venv/bin/python -m fund_traceback.main
python3 -m fund_traceback.main
```

说明：`fund_traceback` 使用包内相对导入，不要用 `python3 -m main.py`，也不要直接把 `fund_traceback/main.py` 当普通脚本模块名执行。

### Syntax check
```bash
./venv/bin/python -m py_compile fund_traceback/*.py
```

### Legacy scripts
```bash
python3 main.py
python3 main_fund.py
python3 index_find.py
```

## Configuration-driven workflow

`fund_traceback` 当前不依赖 CLI 参数，主要通过 `fund_traceback/config.py` 控制：
- `STRATEGY`
- `DATE_RANGE`
- `FUNDS`
- `REBALANCE_CONFIG`
- `FEES`
- `OUTPUT`

## Notes

- 推荐优先维护 `fund_traceback/`，根目录 `main.py` 和 `main_fund.py` 属于历史脚本。
- 运行真实回测前需要确保 `config.py` 中的 Tushare token 可用。
- 若要关闭图表，修改 `OUTPUT['show_plot'] = False`。
