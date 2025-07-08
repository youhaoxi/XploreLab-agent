

数据封装 v0.2
    整体调用 (runner.py): 调用 Eval, DataManager 两个组件. 
        流程: load data -> rollout -> evaluate & stat
        其中 DataManager 模块负责保存数据, Eval 模块负责评估. 

v0.3

1. 保留 Sample 作为数据模型, 同步到 DB;
2. 其他组件合并为 Benchmark 类, 实现标准化的流程. 去除/集成 Processor, DataManager 等组件.