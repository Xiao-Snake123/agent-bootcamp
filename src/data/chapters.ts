export interface Chapter {
  slug: string;      // URL 片段，对应 content 文件名前缀 01..12
  file: string;      // content/核心机制篇 下的 md 文件名
  demo: string;      // demos/ 下的配套可运行 demo（阶段 3，见 demos/README.md）
  title: string;
  intro: string;
  difficulty: number; // 1-5
}

export const chapters: Chapter[] = [
  { slug: '01', file: '01_推理-行动循环ReAct.md', demo: 'demo_01_react.py', title: '推理-行动循环 ReAct', intro: 'Agent 最基础的闭环：思考→动作→观察，为什么需要它、怎么实现、如何防死循环。', difficulty: 2 },
  { slug: '02', file: '02_工具系统.md', demo: 'demo_02_tools.py', title: '工具系统', intro: '工具声明(JSon Schema)、路由、并行调用、重试/熔断/超时与 HITL。', difficulty: 3 },
  { slug: '03', file: '03_上下文工程.md', demo: 'demo_03_context.py', title: '上下文工程', intro: 'LLM 的“工作记忆”如何组织：KV 缓存、摘要压缩、短期/长期记忆。', difficulty: 3 },
  { slug: '04', file: '04_规划与分解.md', demo: 'demo_04_planning.py', title: '规划与分解', intro: 'Plan-and-Execute、任务 DAG、目标树、重规划与回退。', difficulty: 3 },
  { slug: '05', file: '05_反思与自修正.md', demo: 'demo_05_reflexion.py', title: '反思与自修正', intro: 'Reflexion：让 Agent 基于环境反馈自我批评、纠错，避免无限循环。', difficulty: 3 },
  { slug: '06', file: '06_多智能体.md', demo: 'demo_06_multiagent.py', title: '多 Agent 协作', intro: '角色协议、消息总线、Orchestrator、辩论/共识、资源共享与死锁。', difficulty: 4 },
  { slug: '07', file: '07_RAG深度.md', demo: 'demo_07_rag.py', title: 'RAG 深度', intro: 'chunk 策略、embedding 选型、hybrid 检索、rerank、评测与失败模式。', difficulty: 4 },
  { slug: '08', file: '08_能力扩展(MCP-FC-Skill).md', demo: 'demo_08_mcp_skill.py', title: '能力扩展 MCP/FC/Skill', intro: 'Function Calling、MCP、Skill 三者的层级关系与边界。', difficulty: 3 },
  { slug: '09', file: '09_编排与框架.md', demo: 'demo_09_orchestrator.py', title: '编排与框架', intro: '状态机、checkpoint、中断恢复、幂等；LangGraph/AutoGen 对比。', difficulty: 4 },
  { slug: '10', file: '10_评测与可观测.md', demo: 'demo_10_eval.py', title: '评测与可观测', intro: '轨迹回放、LLM-as-Judge、护栏、成本与延迟度量。', difficulty: 4 },
  { slug: '11', file: '11_安全与合规.md', demo: 'demo_11_guardrail.py', title: '安全与合规', intro: '提示注入、数据泄露、权限最小化、沙箱与红队。', difficulty: 4 },
  { slug: '12', file: '12_生产化SRE.md', demo: 'demo_12_serve.py', title: '生产化 SRE', intro: '部署、流式、并发限流、语义缓存、降级、监控告警与上线清单。', difficulty: 5 },
];
