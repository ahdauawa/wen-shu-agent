import json
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.config import Settings
from app.knowledge import Knowledge
from app.model import Decision, Model, NoEvidenceError, TicketCreate
from app.store import Store


class State(TypedDict, total=False):
    text: str
    history: list[dict]
    intent: str
    confidence: float
    clarifications: int
    pending_ticket: dict | None
    status: str
    reply: str
    reason: str
    evidence: list[dict]
    tool: str | None
    ticket: dict | None
    handoff_id: str | None
    trace: list[str]
    cited_ids: list[str]


def build_graph(settings: Settings, model: Model, knowledge: Knowledge,
                store: Store, db, owner: str, session_id: str):
    def tagged(state, node, **updates):
        return {"trace": state.get("trace", []) + [node], **updates}

    def classify(state):
        if state.get("pending_ticket") and state["text"].strip() in ("确认", "确认提交", "取消"):
            decision = Decision(intent="ticket_create", confidence=1)
        else:
            try:
                decision = model.classify(state["text"], state["history"])
            except Exception:
                return tagged(state, "classify", intent="unknown", confidence=0, reason="model_failed")
        return tagged(state, "classify", **decision.model_dump())

    def route(state):
        # Direct human requests and complaints always outrank confidence gating.
        if state.get("reason") or state["intent"] in ("complaint", "human_request"):
            return "handoff"
        if state["confidence"] < settings.intent_threshold or state["intent"] == "unknown":
            return "clarify" if state["clarifications"] < 2 else "handoff"
        return {"knowledge_query": "retrieve", "ticket_query": "tools",
                "ticket_create": "tools", "chitchat": "respond"}[state["intent"]]

    def clarify(state):
        return tagged(state, "clarify", clarifications=state["clarifications"] + 1,
                      reply="请问你想咨询产品政策、查询工单，还是提交问题工单？也可以输入“转人工”。")

    def retrieve(state):
        try:
            hits = knowledge.search(state["text"])
            return tagged(state, "retrieve", evidence=hits, reason="" if hits else "no_knowledge")
        except Exception:
            return tagged(state, "retrieve", evidence=[], reason="retrieval_failed")

    def tools(state):
        text = state["text"].strip()
        pending = state.get("pending_ticket")
        if pending and text == "取消":
            return tagged(state, "tools", pending_ticket=None, reply="已取消，本次没有创建工单。")
        if pending and text in ("确认", "确认提交"):
            args = TicketCreate.model_validate(pending)
            ticket = store.create_ticket(db, owner, args.title, args.description)
            return tagged(state, "tools", pending_ticket=None, tool="create_ticket", ticket=ticket,
                          reply=f"工单已创建：{ticket['id']}，状态为待处理。可以用此编号查询。")
        try:
            name, args = model.plan_tool(state["intent"], text)
        except ValueError as error:
            if str(error) == "missing_ticket_id":
                return tagged(state, "tools", reply="请提供 TK 开头的工单编号，我会查询你名下的工单。")
            return tagged(state, "tools", reason="tool_failed")
        except Exception:
            return tagged(state, "tools", reason="tool_failed")
        if name == "query_ticket":
            ticket = store.query_ticket(db, owner, args["ticket_id"])
            reply = (f"工单 {ticket['id']}：{ticket['title']}，当前状态 {ticket['status']}。"
                     if ticket else "未找到你名下的这笔工单，请检查编号。")
            return tagged(state, "tools", tool=name, ticket=ticket, reply=reply)
        return tagged(state, "tools", pending_ticket=args, tool="preview_ticket",
                      reply=f"将创建工单：{args['title']}\n问题：{args['description']}\n请回复“确认提交”或“取消”。")

    def respond(state):
        if state.get("reply"):
            return tagged(state, "respond")
        if state["intent"] == "chitchat":
            return tagged(state, "respond", reply="你好，我是问枢。可以咨询帮助文档、查询工单、提交问题或转人工。")
        try:
            answer = model.answer_grounded(state["text"], state["history"], state["evidence"])
            return tagged(state, "respond", **answer)
        except NoEvidenceError:
            return tagged(state, "respond", reason="insufficient_evidence")
        except Exception:
            return tagged(state, "respond", reason="model_failed")

    def handoff(state):
        reason = state.get("reason") or (state["intent"] if state["intent"] in
                    ("complaint", "human_request") else "max_clarification")
        # Extractive summary keeps facts grounded and avoids another failing model request.
        summary = json.dumps({"current_request": state["text"], "recent_messages": state["history"][-6:],
                              "attempted_nodes": state.get("trace", [])}, ensure_ascii=False)
        handoff_id = store.handoff(db, owner, session_id, reason, summary)
        return tagged(state, "handoff", status="handoff_pending", pending_ticket=None,
                      reason=reason, handoff_id=handoff_id,
                      reply=f"已生成转人工交接记录 {handoff_id}。这是本地演示，尚未接入真实客服坐席。")

    graph = StateGraph(State)
    for name, node in [("classify", classify), ("clarify", clarify), ("retrieve", retrieve),
                       ("tools", tools), ("respond", respond), ("handoff", handoff)]:
        graph.add_node(name, node)
    graph.add_edge(START, "classify")
    graph.add_conditional_edges("classify", route,
        {x: x for x in ("handoff", "clarify", "retrieve", "tools", "respond")})
    graph.add_conditional_edges("retrieve", lambda s: "handoff" if s.get("reason") else "respond")
    graph.add_conditional_edges("tools", lambda s: "handoff" if s.get("reason") else "respond")
    graph.add_conditional_edges("respond", lambda s: "handoff" if s.get("reason") else END)
    graph.add_edge("clarify", END)
    graph.add_edge("handoff", END)
    return graph.compile()
