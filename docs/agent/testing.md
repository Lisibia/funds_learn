# testing

## Current status

当前 `funds_learn` 根项目没有正式测试基础设施：
- 无 `tests/` 目录
- 无 `pytest` 配置
- 无覆盖率命令

目前最直接的校验方式是：
1. 语法校验
2. 真实回测运行
3. 查看控制台指标和交易记录是否合理

## Practical validation commands

```bash
./venv/bin/python -m py_compile fund_traceback/*.py
./venv/bin/python -m fund_traceback.main
```

## What to test first if adding tests

建议优先为 `fund_traceback/` 增加测试，顺序如下：

### 1. `models.py`
- `Portfolio.buy()`
- `Portfolio.sell()`
- `calculate_total_value()`
- `get_current_weights()`

### 2. `strategies.py`
- 买入持有是否只建仓一次
- 再平衡是否按阈值触发
- 月度/季度频率判断是否正确

### 3. `data_manager.py`
- 净值去重逻辑
- 前向填充逻辑
- 名称查询失败时是否回退到基金代码

### 4. `engine.py`
- 是否按日期推进
- 是否记录每日状态
- 是否正确处理部分基金晚于其他基金上市的情况

## Recommended future setup

如果补测试，建议使用：
- `pytest`
- `tests/`
- 伪造净值 DataFrame 做单元测试，避免真实网络请求
- 将 Tushare API 调用替换为 mock 或 fixture 数据

## Conventions to adopt

- 测试文件命名：`test_*.py`
- 每个核心模块对应一个测试文件
- 网络依赖应隔离，不直接在单元测试中请求真实 Tushare
