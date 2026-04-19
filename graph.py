# graph.py
"""
LangGraph Orchestration - True Agentic Workflow cho OBE DCCT Agent

Luồng chính:
Supervisor → Understand → Critic → Mapping → Critic → 
Teaching Plan (động) → Critic → Assessment → Critic → 
Final Validator → Decision (Export / Preview / Retry)
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from state import DCCTState

# Import các Agent nodes
from agents.supervisor import supervisor_node
from agents.understand import understand_node
from agents.mapping import mapping_node
from agents.teaching_plan import teaching_plan_node
from agents.assessment import assessment_node
from agents.validator import final_validator_node

# Import Tools
from tools.critic_tool import critic_node
from tools.preview_tool import preview_node
from export.word_generator import export_node


def decide_after_validator(state: DCCTState):
    """
    Quyết định bước tiếp theo sau Final Validator dựa trên confidence_score
    """
    confidence = state.get("confidence_score", 0.0)

    if confidence >= 90:
        return "export"          # Tự động xuất file Word
    elif confidence >= 70:
        return "preview"         # Vào Preview Mode
    else:
        return "supervisor"      # Quay lại Supervisor để chỉnh sửa


def build_graph():
    """Xây dựng LangGraph workflow"""
    workflow = StateGraph(DCCTState)

    # ==================== Thêm Nodes ====================
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("understand", understand_node)
    workflow.add_node("mapping", mapping_node)
    workflow.add_node("teaching_plan", teaching_plan_node)
    workflow.add_node("assessment", assessment_node)
    workflow.add_node("final_validator", final_validator_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("preview", preview_node)
    workflow.add_node("export", export_node)

    # ==================== Entry Point ====================
    workflow.set_entry_point("supervisor")

    # ==================== Supervisor Routing ====================
    # Supervisor quyết định bước tiếp theo dựa trên current_step
    workflow.add_conditional_edges(
        "supervisor",
        lambda s: s.get("current_step", "understand"),
        {
            "understand": "understand",
            "mapping": "mapping",
            "teaching_plan": "teaching_plan",
            "assessment": "assessment",
            "final_validator": "final_validator",
        }
    )

    # ==================== Specialist Agents → Critic ====================
    # Tất cả agent chuyên biệt đều phải qua Critic để tự kiểm chứng
    workflow.add_edge("understand", "critic")
    workflow.add_edge("mapping", "critic")
    workflow.add_edge("teaching_plan", "critic")
    workflow.add_edge("assessment", "critic")

    # ==================== Critic → Supervisor ====================
    # Sau khi Critic kiểm tra, quay về Supervisor để quyết định bước tiếp theo
    workflow.add_edge("critic", "supervisor")

    # ==================== Final Validator → Decision ====================
    workflow.add_conditional_edges(
        "final_validator",
        decide_after_validator,
        {
            "export": "export",
            "preview": "preview",
            "supervisor": "supervisor"
        }
    )

    # ==================== Preview → Export ====================
    # Sau preview, tự động xuất file Word
    workflow.add_edge("preview", "export")

    # ==================== Export là điểm kết thúc ====================
    workflow.add_edge("export", END)

    # ==================== Compile với Memory ====================
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    return app


# Global graph instance
graph = None

def get_graph():
    """Lấy hoặc tạo graph instance"""
    global graph
    if graph is None:
        graph = build_graph()
    return graph