# architecture

## Project structure philosophy

根目录是一个以学习和实验为主的 Python 回测仓库，当前推荐实现是 `fund_traceback/`。`ai-hedge-fund/` 是同仓库下的独立子项目，不应作为本项目主架构说明的一部分。

## Key structure

- `fund_traceback/config.py`：唯一配置入口
- `fund_traceback/models.py`：交易与组合数据结构
- `fund_traceback/data_manager.py`：Tushare 数据访问与基金名称获取
- `fund_traceback/strategies.py`：策略抽象、买入持有、再平衡、策略工厂
- `fund_traceback/engine.py`：回测驱动引擎
- `fund_traceback/analyzer.py`：绩效指标和图表输出
- `fund_traceback/main.py`：程序入口与配置校验

## Architectural patterns

### 1. Strategy pattern
`BaseStrategy` 定义统一接口，当前有：
- `BuyHoldStrategy`
- `RebalanceStrategy`

新增策略时应优先扩展 `strategies.py`，而不是在 `main.py` 中堆叠分支。

### 2. Factory pattern
`StrategyFactory.create()` 根据配置创建策略实例，入口层不直接依赖具体策略实现细节。

### 3. Engine-driven flow
`BacktestEngine` 负责按时间序列推进回测：
1. 读取净值表
2. 初始化组合
3. 调用策略钩子
4. 记录每日组合状态
5. 返回结果给分析器

### 4. Data/service split
`FundDataManager` 独立负责：
- 拉取历史净值
- 清洗数据（排序、去重、前向填充）
- 获取基金名称并在失败时降级为代码

## Data flow

配置 → `FundDataManager` 拉净值/名称 → `StrategyFactory` 创建策略 → `BacktestEngine` 执行回测 → `PerformanceAnalyzer` 输出指标和图表。

## Configuration approach

项目主要采用 Python 配置而不是命令行配置。默认使用 `fund_traceback/config.py` 中的常量控制策略和输入。

## Legacy code

- `main.py`：原始 ETF 回测单文件脚本
- `main_fund.py`：旧版基金回测脚本
- `index_find.py`：指数/代码辅助查询工具

除非任务明确要求，否则优先修改 `fund_traceback/` 而不是旧脚本。
