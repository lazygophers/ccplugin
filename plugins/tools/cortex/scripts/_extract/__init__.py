"""cortex extract — L4 inbox → L1/L2/L3 / 项目 / 领域 路由模块包。

子模块:
  classifier — 三轴 (时效 / 强度 / 复用面) 信号识别
  router     — 路由决策表 (L0 自动落盘 / L3 默认 / L2/L1 promote 候选 / 项目 / 领域)
  writer     — dry-run / apply 落盘 + 增量游标
"""
