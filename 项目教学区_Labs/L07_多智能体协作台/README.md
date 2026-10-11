# L07 多智能体协作台（对应 K07）

> 把 K7 的"多角色协作"落成代码：Researcher / Writer / Critic 三角色经 message bus 解耦协作，Orchestrator 路由并驱动评审循环。无需 API Key。

## 目标
- 理解多智能体相对"单 Agent + 子程序"的价值（专业化、可协作）与代价（协调开销）。
- 体会 role / message bus / orchestrator 三件套：角色解耦、总线传消息、编排者路由与终止。
- 认识评审循环：Critic 未通过则 Writer 重修，直到"通过"或 `max_rounds`（终止条件是保险丝）。

## 拓扑示意
```mermaid
flowchart LR
    R[Researcher] --> W[Writer] --> C[Critic]
    C -->|需修改| W
```

## 实现步骤
1. `message_bus.py`：`MessageBus` 持有 `history`，角色 `post`/`last_from` 解耦取用——避免上下文互灌爆炸（K7 陷阱③）。
2. `roles.py`：`Researcher`/`Writer`/`Critic` 各读必要上下文产出；Critic 首次要求补风险段、第二次给通过，演示评审循环。
3. `orchestrator.py`：`Orchestrator` 先流水线（研究→写稿），再评审循环（Critic 评审→未过则 Writer 重修），带 `max_rounds` 终止。

## 运行
```
cd 项目教学区_Labs/L07_多智能体协作台
python loop.py
```
将看到三角色依次产出，Critic 首轮"需修改"触发 Writer 重修，次轮"通过"。

## 验收标准
- [ ] 能口述何时该用多 Agent、Orchestrator 的职责、终止条件为何必要。
- [ ] `pytest test_multi.py` 全绿：三角色产出、评审循环收敛（Writer 出现 2 次）。
- [ ] 能说出"各角色上下文不能无脑互灌"的原因。

## 技能演练（亲手做）
1. 接真 LLM：把 `roles.py` 三个角色的 `act` 换成 `OpenAIClient` 驱动（prompt 各司其职），Orchestrator 不变——验证"角色解耦、编排复用"。
2. 加**辩论拓扑**：新增 `DebaterA`/`DebaterB`，Orchestrator 支持环形多轮对抗（呼应 K7 辩论拓扑）。
3. 把 Orchestrator 升级为"内含 K5 planner + K6 reflector"的复合编排者：先规划子任务分给角色，角色产出后经反思再 handoff——闭合规划—执行—反思—协作全链路。
