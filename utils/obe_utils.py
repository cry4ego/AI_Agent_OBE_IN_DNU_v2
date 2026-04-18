"""
OBE Utilities - Dữ liệu chuẩn OBE/AUN-QA cho Khoa CNTT - ĐH Đà Nẵng
Bao gồm: Bloom Taxonomy, PLO, PI, IRMA levels và các helper functions
"""

from typing import Dict, List, Tuple

# ============================================================
# BLOOM'S TAXONOMY
# ============================================================

BLOOM_LEVELS = {
    1: "Remember",
    2: "Understand",
    3: "Apply",
    4: "Analyze",
    5: "Evaluate",
    6: "Create",
}

BLOOM_VERBS: Dict[int, List[str]] = {
    1: [
        "define", "list", "recall", "recognize", "state", "identify", "name", "repeat",
        "nhớ lại", "liệt kê", "nhận biết", "xác định", "nêu", "ghi nhớ",
    ],
    2: [
        "explain", "describe", "summarize", "classify", "interpret", "paraphrase",
        "giải thích", "mô tả", "tóm tắt", "phân loại", "diễn giải", "trình bày",
    ],
    3: [
        "apply", "use", "implement", "solve", "demonstrate", "execute", "perform",
        "áp dụng", "sử dụng", "thực hiện", "giải", "lập trình", "triển khai", "xây dựng",
    ],
    4: [
        "analyze", "compare", "differentiate", "examine", "decompose", "distinguish",
        "phân tích", "so sánh", "phân biệt", "kiểm tra", "phân rã", "đánh giá chi tiết",
    ],
    5: [
        "evaluate", "judge", "assess", "critique", "justify", "argue",
        "đánh giá", "nhận xét", "phê bình", "chứng minh", "lựa chọn", "phán xét",
    ],
    6: [
        "design", "build", "create", "formulate", "develop", "construct", "compose",
        "thiết kế", "tạo ra", "lập", "phát triển", "xây dựng hệ thống", "đề xuất",
    ],
}

BLOOM_LEVEL_VI = {
    1: "Nhớ (Remember)",
    2: "Hiểu (Understand)",
    3: "Áp dụng (Apply)",
    4: "Phân tích (Analyze)",
    5: "Đánh giá (Evaluate)",
    6: "Sáng tạo (Create)",
}


def get_bloom_level(verb: str) -> Tuple[int, str]:
    """Xác định mức Bloom từ động từ. Trả về (level_number, level_name_vi)."""
    verb_lower = verb.lower()
    for level, verbs in BLOOM_VERBS.items():
        if any(v in verb_lower for v in verbs):
            return level, BLOOM_LEVEL_VI[level]
    return 2, BLOOM_LEVEL_VI[2]  # default: Understand


def get_bloom_verbs_for_level(level: int) -> List[str]:
    """Lấy danh sách động từ Bloom cho mức cho trước."""
    return BLOOM_VERBS.get(level, BLOOM_VERBS[2])


# ============================================================
# PLO - PROGRAM LEARNING OUTCOMES
# Khoa Công nghệ Thông tin - ĐH Đà Nẵng (Chuẩn AUN-QA / ABET)
# ============================================================

PLO_DATA: Dict[str, str] = {
    "PLO1": "Áp dụng được kiến thức nền tảng về toán học, khoa học và công nghệ thông tin để giải quyết các bài toán kỹ thuật phần mềm",
    "PLO2": "Phân tích được yêu cầu, xác định và phát biểu bài toán trong lĩnh vực công nghệ thông tin",
    "PLO3": "Thiết kế, cài đặt và đánh giá được hệ thống phần mềm đáp ứng các yêu cầu đặc tả kỹ thuật",
    "PLO4": "Áp dụng được các kỹ thuật, công cụ và phương pháp hiện đại trong phát triển phần mềm",
    "PLO5": "Giao tiếp hiệu quả bằng văn bản và lời nói trong môi trường kỹ thuật và phi kỹ thuật",
    "PLO6": "Làm việc hiệu quả trong nhóm đa ngành, đảm nhận các vai trò khác nhau kể cả vai trò lãnh đạo",
    "PLO7": "Hiểu được trách nhiệm nghề nghiệp, xã hội, pháp lý và đạo đức trong lĩnh vực CNTT",
    "PLO8": "Nhận thức và thực hành học tập suốt đời để cập nhật kiến thức trong lĩnh vực CNTT phát triển nhanh",
    "PLO9": "Hiểu tác động của giải pháp kỹ thuật trong bối cảnh toàn cầu, kinh tế, môi trường và xã hội",
    "PLO10": "Nắm bắt và phân tích các vấn đề, xu hướng đương đại trong lĩnh vực công nghệ thông tin",
}

# ============================================================
# PI - PERFORMANCE INDICATORS
# Mỗi PLO có từ 2-4 PI cụ thể, đo lường được
# ============================================================

PI_DATA: Dict[str, Dict[str, str]] = {
    "PLO1": {
        "PI1.1": "Áp dụng kiến thức toán học (đại số tuyến tính, xác suất thống kê, toán rời rạc) vào phân tích và giải quyết bài toán CNTT",
        "PI1.2": "Sử dụng kiến thức về cấu trúc dữ liệu và giải thuật để lựa chọn và tối ưu hóa giải pháp",
        "PI1.3": "Ứng dụng lý thuyết về hệ thống, mạng và kiến trúc máy tính trong thiết kế giải pháp",
    },
    "PLO2": {
        "PI2.1": "Thu thập, phân tích và đặc tả yêu cầu người dùng từ các tình huống thực tế",
        "PI2.2": "Mô hình hóa bài toán bằng các ký hiệu, biểu đồ chuẩn (UML, flowchart, ER diagram)",
        "PI2.3": "Xác định ràng buộc, điều kiện giới hạn và đề xuất các tiêu chí chấp nhận giải pháp",
    },
    "PLO3": {
        "PI3.1": "Thiết kế kiến trúc hệ thống phần mềm theo các mô hình chuẩn (MVC, microservices, layered)",
        "PI3.2": "Cài đặt, kiểm thử và tích hợp phần mềm theo quy trình kỹ thuật chuyên nghiệp",
        "PI3.3": "Đánh giá chất lượng phần mềm theo các tiêu chí kỹ thuật và nghiệp vụ",
    },
    "PLO4": {
        "PI4.1": "Sử dụng thành thạo các IDE, framework và công cụ phát triển phần mềm hiện đại",
        "PI4.2": "Áp dụng các phương pháp phát triển phần mềm linh hoạt (Agile, Scrum, DevOps)",
        "PI4.3": "Sử dụng công cụ kiểm thử tự động, quản lý mã nguồn (Git) và CI/CD pipeline",
    },
    "PLO5": {
        "PI5.1": "Viết tài liệu kỹ thuật (đặc tả, thiết kế, hướng dẫn) rõ ràng và chính xác",
        "PI5.2": "Trình bày và bảo vệ giải pháp kỹ thuật trước nhóm chuyên gia và người dùng",
        "PI5.3": "Giao tiếp hiệu quả với khách hàng và các bên liên quan không có nền tảng kỹ thuật",
    },
    "PLO6": {
        "PI6.1": "Đóng góp tích cực và chủ động trong nhóm dự án phần mềm đa thành viên",
        "PI6.2": "Sử dụng các công cụ cộng tác (Git, Jira, Trello) để quản lý và phối hợp công việc nhóm",
        "PI6.3": "Thể hiện khả năng lãnh đạo, phân công và điều phối công việc trong nhóm dự án",
    },
    "PLO7": {
        "PI7.1": "Nhận diện và xử lý các tình huống có xung đột đạo đức nghề nghiệp trong CNTT",
        "PI7.2": "Tôn trọng bản quyền phần mềm, quyền riêng tư dữ liệu và an toàn thông tin",
        "PI7.3": "Tuân thủ các quy định pháp lý và tiêu chuẩn nghề nghiệp trong phát triển phần mềm",
    },
    "PLO8": {
        "PI8.1": "Chủ động tự học công nghệ mới thông qua tài liệu, khóa học online và cộng đồng kỹ thuật",
        "PI8.2": "Phản ánh và cải thiện kỹ năng chuyên môn dựa trên phản hồi và kinh nghiệm thực tế",
    },
    "PLO9": {
        "PI9.1": "Phân tích tác động kinh tế, xã hội của giải pháp phần mềm đối với người dùng và cộng đồng",
        "PI9.2": "Xem xét các yếu tố bền vững, hiệu quả năng lượng trong thiết kế và vận hành hệ thống",
    },
    "PLO10": {
        "PI10.1": "Nắm bắt và phân tích các xu hướng công nghệ mới (AI/ML, Cloud, IoT, Blockchain, Cybersecurity)",
        "PI10.2": "Đánh giá tác động của chuyển đổi số và công nghệ mới tới các lĩnh vực kinh tế - xã hội",
    },
}

# ============================================================
# IRMA LEVELS
# ============================================================

IRMA_LEVELS = {
    "I": "Introduce - Giới thiệu khái niệm, mức độ nhận biết cơ bản",
    "R": "Reinforce - Củng cố, luyện tập với sự hỗ trợ",
    "M": "Master - Thành thạo, thực hiện độc lập",
    "A": "Apply - Áp dụng sáng tạo vào tình huống mới",
}

IRMA_BLOOM_MAP = {
    "I": [1, 2],       # Remember, Understand
    "R": [2, 3],       # Understand, Apply
    "M": [3, 4],       # Apply, Analyze
    "A": [4, 5, 6],    # Analyze, Evaluate, Create
}


def suggest_irma_for_bloom(bloom_level: int) -> str:
    """Gợi ý mức IRMA phù hợp với mức Bloom."""
    if bloom_level <= 2:
        return "I"
    elif bloom_level == 3:
        return "R"
    elif bloom_level == 4:
        return "M"
    else:
        return "A"


# ============================================================
# CREDIT SYSTEM (Hệ thống tín chỉ Việt Nam)
# 1 tín chỉ lý thuyết = 15 tiết học
# 1 tín chỉ thực hành = 30 tiết học (15 buổi × 2 tiết)
# ============================================================

def calculate_sessions(credits: str, theory_ratio: float = 0.7) -> Dict:
    """
    Tính số buổi học dựa theo số tín chỉ.
    
    Args:
        credits: Số tín chỉ (str, vd "3")
        theory_ratio: Tỷ lệ lý thuyết (0.7 = 70% LT, 30% TH)
    
    Returns:
        Dict với total_sessions, theory_sessions, lab_sessions, weeks
    """
    try:
        c = int(credits)
    except (ValueError, TypeError):
        c = 3

    # 1 tín chỉ = 15 tiết → 1 buổi = 1 tiết (hoặc 2 tiết tùy trường)
    # Tại ĐH Đà Nẵng: 1 tín chỉ ≈ 15 tiết = 15 buổi 50 phút
    total_periods = c * 15
    theory_periods = round(total_periods * theory_ratio)
    lab_periods = total_periods - theory_periods

    return {
        "credits": c,
        "total_periods": total_periods,
        "theory_periods": theory_periods,
        "lab_periods": lab_periods,
        "total_sessions": total_periods,  # 1 buổi = 1 tiết
        "weeks": c * 5,  # ~5 tuần / tín chỉ
    }


# ============================================================
# ASSESSMENT WEIGHTS (Trọng số đánh giá chuẩn)
# ============================================================

DEFAULT_ASSESSMENT_WEIGHTS = {
    "A1": {
        "name": "Đánh giá quá trình",
        "description": "Chuyên cần, bài tập, quiz, thảo luận",
        "weight": 0.10,
    },
    "A2.1": {
        "name": "Kiểm tra giữa kỳ",
        "description": "Kiểm tra lý thuyết giữa học kỳ (trắc nghiệm/tự luận)",
        "weight": 0.20,
    },
    "A2.2": {
        "name": "Thực hành / Bài tập lớn",
        "description": "Bài thực hành, dự án nhóm, báo cáo",
        "weight": 0.30,
    },
    "A3": {
        "name": "Thi cuối kỳ",
        "description": "Thi cuối học kỳ (lý thuyết + thực hành)",
        "weight": 0.40,
    },
}


# ============================================================
# PLO-PI HELPER FUNCTIONS
# ============================================================

def get_all_pi_codes() -> List[str]:
    """Lấy tất cả mã PI."""
    codes = []
    for plo, pis in PI_DATA.items():
        codes.extend(pis.keys())
    return codes


def get_pi_description(pi_code: str) -> str:
    """Lấy mô tả của PI theo mã."""
    for plo, pis in PI_DATA.items():
        if pi_code in pis:
            return pis[pi_code]
    return ""


def get_plo_for_pi(pi_code: str) -> str:
    """Xác định PLO chứa PI này."""
    for plo, pis in PI_DATA.items():
        if pi_code in pis:
            return plo
    return ""


def get_pi_list_text() -> str:
    """Trả về danh sách PI dạng text để đưa vào prompt LLM."""
    lines = []
    for plo_code, pis in PI_DATA.items():
        plo_desc = PLO_DATA.get(plo_code, "")
        lines.append(f"\n{plo_code}: {plo_desc}")
        for pi_code, pi_desc in pis.items():
            lines.append(f"  {pi_code}: {pi_desc}")
    return "\n".join(lines)


def get_plo_list_text(program: str = "GENERIC") -> str:
    """Trả về danh sách PLO dạng text để đưa vào prompt LLM."""
    data = PROGRAM_DATA.get(program, PROGRAM_DATA["GENERIC"])["plo"] if "PROGRAM_DATA" in dir() else PLO_DATA
    lines = []
    for plo_code, desc in data.items():
        lines.append(f"{plo_code}: {desc}")
    return "\n".join(lines)


# ============================================================
# HTTT - HỆ THỐNG THÔNG TIN
# PLO và PI chuẩn thực tế từ CTĐT ngành HTTT - ĐH Đà Nẵng
# ============================================================

HTTT_PLO_DATA: Dict[str, str] = {
    "PLO-IS01": (
        "Sinh viên tốt nghiệp ngành HTTT có khả năng thực hiện hoạt động học thuật và nghề nghiệp "
        "HTTT tuân thủ pháp luật, liêm chính học thuật, yêu cầu tuân thủ doanh nghiệp, và đánh giá "
        "được rủi ro đạo đức (riêng tư, bảo mật, tác động tổ chức) của giải pháp HTTT."
    ),
    "PLO-IS02": (
        "Sinh viên tốt nghiệp ngành HTTT có khả năng vận dụng kiến thức nền tảng tính toán "
        "(lập trình, mạng, CSDL ở mức phù hợp) và công cụ số để diễn giải và lựa chọn phương án "
        "kỹ thuật đáp ứng yêu cầu nghiệp vụ."
    ),
    "PLO-IS03": (
        "Sinh viên tốt nghiệp ngành HTTT có khả năng thu thập, phân tích và đặc tả yêu cầu nghiệp vụ "
        "để tạo BRD/SRS có truy vết, làm cơ sở thiết kế và kiểm thử, đánh giá."
    ),
    "PLO-IS04": (
        "Sinh viên tốt nghiệp ngành HTTT có khả năng mô hình hoá quy trình nghiệp vụ và thiết kế "
        "giải pháp HTTT để cải tiến quy trình, đảm bảo phù hợp vận hành tổ chức và ràng buộc kiểm soát."
    ),
    "PLO-IS05": (
        "Sinh viên tốt nghiệp ngành HTTT có khả năng thiết kế mô hình dữ liệu và cơ chế quản trị dữ liệu "
        "để đảm bảo chất lượng, nhất quán, quyền sở hữu và khả năng khai thác dữ liệu trong tổ chức."
    ),
    "PLO-IS06": (
        "Sinh viên tốt nghiệp ngành HTTT có khả năng xây dựng chỉ số KPI và báo cáo, trực quan hoá dữ liệu "
        "để hỗ trợ ra quyết định, đảm bảo tính đúng, khả giải thích và phù hợp mục tiêu kinh doanh."
    ),
    "PLO-IS07": (
        "Sinh viên tốt nghiệp ngành HTTT có khả năng thiết kế và triển khai tích hợp giữa các hệ thống "
        "thông tin doanh nghiệp (ERP/CRM/DWH/ứng dụng) theo kiến trúc phù hợp, đảm bảo dòng dữ liệu, "
        "tính toàn vẹn và khả vận hành."
    ),
    "PLO-IS08": (
        "Sinh viên tốt nghiệp ngành HTTT có khả năng lập kế hoạch, phối hợp dự án HTTT và quản lý thay đổi "
        "để triển khai thành công trong tổ chức, giao tiếp hiệu quả với stakeholder và cải tiến liên tục."
    ),
}

HTTT_PI_DATA: Dict[str, Dict[str, str]] = {
    "PLO-IS01": {
        "PI-IS01.1": "Trích dẫn đúng nguồn dữ liệu/phần mềm và nêu rõ giấy phép sử dụng.",
        "PI-IS01.2": "Lập checklist tuân thủ và risk register cho giải pháp HTTT.",
        "PI-IS01.3": "Phân tích rủi ro đạo đức, riêng tư, bảo mật và tác động tổ chức, đề xuất biện pháp kiểm soát cơ bản.",
    },
    "PLO-IS02": {
        "PI-IS02.1": "Biện minh lựa chọn kỹ thuật theo ràng buộc nghiệp vụ.",
        "PI-IS02.2": "Cấu hình/tích hợp thành phần kỹ thuật theo tài liệu, kể cả tài liệu tiếng Anh, và tái lập được kết quả.",
        "PI-IS02.3": "Ghi nhận quyết định kỹ thuật bằng technical decision record hoặc log nghiên cứu/cấu hình.",
    },
    "PLO-IS03": {
        "PI-IS03.1": "Thu thập và xác nhận yêu cầu nghiệp vụ từ stakeholder bằng kỹ thuật phù hợp.",
        "PI-IS03.2": "Chuyển hóa yêu cầu thành BRD/SRS hoặc user stories kèm acceptance criteria.",
        "PI-IS03.3": "Thiết lập truy vết yêu cầu từ yêu cầu → thiết kế → kiểm thử và quản lý thay đổi liên quan.",
    },
    "PLO-IS04": {
        "PI-IS04.1": "Mô hình hóa quy trình nghiệp vụ AS-IS/TO-BE bằng ký pháp phù hợp (BPMN/UML).",
        "PI-IS04.2": "Xây dựng mô hình/use case/UML và solution blueprint ở mức đủ để truyền đạt giải pháp.",
        "PI-IS04.3": "Nhận diện và biểu diễn các điểm kiểm soát nội bộ/ràng buộc kiểm soát trong giải pháp HTTT.",
    },
    "PLO-IS05": {
        "PI-IS05.1": "Thiết kế mô hình dữ liệu/ERD và data dictionary gắn với nghiệp vụ.",
        "PI-IS05.2": "Xác định data ownership, phân quyền và data catalog ở mức phù hợp.",
        "PI-IS05.3": "Xây dựng quy tắc chất lượng dữ liệu và cách đo/giám sát dữ liệu.",
    },
    "PLO-IS06": {
        "PI-IS06.1": "Xây dựng KPI tree và KPI definition sheet phù hợp mục tiêu kinh doanh.",
        "PI-IS06.2": "Tạo dashboard/report BI kèm dataset/query và đối soát tính đúng của dữ liệu.",
        "PI-IS06.3": "Diễn giải insight và đề xuất hành động cho stakeholder từ kết quả phân tích.",
    },
    "PLO-IS07": {
        "PI-IS07.1": "Xây dựng integration spec và mapping dữ liệu giữa các hệ thống.",
        "PI-IS07.2": "Triển khai tích hợp tối thiểu và kiểm thử luồng dữ liệu/chức năng tích hợp.",
        "PI-IS07.3": "Lập architecture diagram và ADR để biện minh cho giải pháp tích hợp và khả vận hành.",
    },
    "PLO-IS08": {
        "PI-IS08.1": "Lập project plan, risk register và RACI cho dự án/hoạt động triển khai HTTT.",
        "PI-IS08.2": "Quản lý change request log và thực hiện impact analysis ở mức phù hợp.",
        "PI-IS08.3": "Chuẩn bị training materials, UAT summary/report và biên bản họp để hỗ trợ stakeholder và cải tiến sau triển khai.",
    },
}

# NL3 mapping cho HTTT
HTTT_NL3_PLO_MAP: Dict[str, str] = {
    "NL3-01": "PLO-IS03",  # Khai thác & xác nhận yêu cầu nghiệp vụ
    "NL3-02": "PLO-IS04",  # Mô hình hoá quy trình & truy vết yêu cầu
    "NL3-03": "PLO-IS05",  # Thiết kế giải pháp HTTT theo định hướng dữ liệu
    "NL3-04": "PLO-IS06",  # Xây dựng mô hình dữ liệu & dashboard KPI
    "NL3-05": "PLO-IS07",  # Thực hiện fit-gap & cấu hình ERP/CRM
    "NL3-06": "PLO-IS02",  # Thiết kế & thực thi kiểm thử/UAT
    "NL3-07": "PLO-IS08",  # Tổ chức truyền thông & bàn giao vận hành
    "NL3-08": "PLO-IS01",  # Áp dụng kiểm soát rủi ro, tuân thủ & an toàn thông tin
}

# PO (Program Outcomes) ngành HTTT
HTTT_PO_DATA: Dict[str, str] = {
    "PO1": (
        "Sau 3–5 năm tốt nghiệp, người học có thể đảm nhiệm vai trò Business/System Analyst, dẫn dắt "
        "phân tích yêu cầu và mô hình hoá quy trình–dữ liệu để tạo BRD/SRS có truy vết cho dự án HTTT "
        "doanh nghiệp, tuân thủ chuẩn mực nghề nghiệp."
    ),
    "PO2": (
        "Sau 3–5 năm tốt nghiệp, người học có thể đảm nhiệm vai trò tư vấn phân tích–thiết kế giải pháp "
        "HTTT, chuyển hoá nhu cầu vận hành thành kiến trúc, thiết kế dữ liệu và đặc tả I/O hỗ trợ "
        "triển khai–tích hợp, tuân thủ quy định liên quan."
    ),
    "PO3": (
        "Sau 3–5 năm tốt nghiệp, người học có thể đảm nhiệm vai trò QA/UAT hoặc quản trị chất lượng "
        "HTTT, thiết kế và kiểm soát kiểm thử–nghiệm thu kèm bằng chứng, bảo đảm an toàn, bảo mật–riêng "
        "tư dữ liệu và tuân thủ quy định."
    ),
    "PO4": (
        "Sau 3–5 năm tốt nghiệp, người học có thể đảm nhiệm vai trò chuyên viên triển khai/CSKH HTTT, "
        "phối hợp stakeholder đa bên để tư vấn, đào tạo người dùng và quản trị thay đổi, đảm bảo "
        "bàn giao–vận hành theo SLA trong bối cảnh dự án/sản phẩm."
    ),
    "PO5": (
        "Người học phát triển năng lực tự học suốt đời và chuẩn hoá tri thức nghiệp vụ–dữ liệu để "
        "tạo giá trị cải tiến liên tục; có khả năng đổi mới qua portfolio/case study và thích ứng "
        "chuyển đổi số/AI nhằm nâng cao hiệu quả nghề nghiệp."
    ),
}


# ============================================================
# KHMT - KHOA HỌC MÁY TÍNH
# PLO và PI chuẩn thực tế từ CTĐT ngành KHMT - ĐH Đà Nẵng
# ============================================================

KHMT_PLO_DATA: Dict[str, str] = {
    "PLO-CS01": (
        "Sinh viên tốt nghiệp ngành KHMT có khả năng thực hiện hoạt động học thuật và nghề nghiệp KHMT "
        "tuân thủ pháp luật, liêm chính nghiên cứu, và đánh giá được rủi ro đạo đức (riêng tư, thiên lệch, "
        "an toàn) của mô hình/giải pháp."
    ),
    "PLO-CS02": (
        "Sinh viên tốt nghiệp ngành KHMT có khả năng vận dụng nền tảng toán học, khoa học tính toán để "
        "lập luận, diễn giải và biện minh lựa chọn mô hình, thuật toán phù hợp bài toán."
    ),
    "PLO-CS03": (
        "Sinh viên tốt nghiệp ngành KHMT có khả năng mô hình hoá bài toán, phân tích, thiết kế thuật toán "
        "và kiểm chứng độ chính xác, phức tạp bằng kiểm thử, đánh giá hoặc phân tích thực nghiệm."
    ),
    "PLO-CS04": (
        "Sinh viên tốt nghiệp ngành KHMT có khả năng thiết kế và thực hiện thí nghiệm các phương pháp "
        "đánh giá để so sánh mô hình, giải pháp về dữ liệu, A.I."
    ),
    "PLO-CS05": (
        "Sinh viên tốt nghiệp ngành KHMT có khả năng xây dựng và đánh giá mô hình học máy, học sâu để "
        "khai thác, xử lý, phân tích dữ liệu và tạo ra kết quả cho bài toán thực tế."
    ),
    "PLO-CS06": (
        "Sinh viên tốt nghiệp ngành KHMT có khả năng áp dụng nguyên lý hệ thống (mạng, HĐH, CSDL, an toàn) "
        "để thiết kế và đánh giá kiến trúc và giải pháp tính toán phục vụ bài toán về dữ liệu, A.I."
    ),
    "PLO-CS07": (
        "Sinh viên tốt nghiệp ngành KHMT có khả năng giao tiếp rõ ràng (kỹ thuật và phi kỹ thuật), "
        "làm việc nhóm để thống nhất yêu cầu, giải pháp và trình bày kết quả phân tích/mô hình hoá."
    ),
    "PLO-CS08": (
        "Sinh viên tốt nghiệp ngành KHMT có khả năng lập kế hoạch tự học, tự nghiên cứu, thích ứng công nghệ "
        "và đề xuất cải tiến, ý tưởng đổi mới trong bối cảnh nghề nghiệp KHMT."
    ),
}

KHMT_PI_DATA: Dict[str, Dict[str, str]] = {
    "PLO-CS01": {
        "PI-CS01.1": "Trích dẫn đúng nguồn dữ liệu/mã nguồn, nêu rõ giấy phép và giới hạn sử dụng của dữ liệu, mô hình hoặc thành phần tái sử dụng.",
        "PI-CS01.2": "Phân tích được rủi ro đạo đức – pháp lý – riêng tư – thiên lệch – an toàn của mô hình/giải pháp, và đề xuất biện pháp giảm thiểu ở mức phù hợp.",
        "PI-CS01.3": "Tuân thủ các yêu cầu liêm chính học thuật/nghiên cứu và checklist tuân thủ trong quá trình phát triển, thử nghiệm, công bố kết quả.",
    },
    "PLO-CS02": {
        "PI-CS02.1": "Thiết lập giả định, tiêu chí đánh giá và metric phù hợp cho bài toán hoặc mô hình.",
        "PI-CS02.2": "Thực hiện phân tích thống kê cơ bản trên dữ liệu/đầu ra mô hình để hỗ trợ lập luận và ra quyết định.",
        "PI-CS02.3": "Biện minh có căn cứ cho việc lựa chọn mô hình/thuật toán dựa trên dữ liệu, giả định, metric và kết quả phân tích.",
    },
    "PLO-CS03": {
        "PI-CS03.1": "Đặc tả bài toán rõ ràng theo đầu vào/đầu ra, ràng buộc, tiêu chí chấp nhận và bộ dữ liệu hoặc ca kiểm thử tương ứng.",
        "PI-CS03.2": "Phân tích được độ đúng, độ phức tạp hoặc tính phù hợp của thuật toán/giải pháp ở mức thích hợp.",
        "PI-CS03.3": "So sánh được các thuật toán/giải pháp bằng benchmark hoặc thực nghiệm tối thiểu và rút ra kết luận.",
    },
    "PLO-CS04": {
        "PI-CS04.1": "Thiết kế protocol thí nghiệm gồm chia dữ liệu, metric, baseline và cách kiểm soát biến phù hợp với bài toán.",
        "PI-CS04.2": "Ghi log thí nghiệm, lưu cấu hình/môi trường và tái lập được kết quả ở mức phù hợp.",
        "PI-CS04.3": "Thực hiện được ablation hoặc so sánh tham số/mô hình và diễn giải kết quả thực nghiệm.",
    },
    "PLO-CS05": {
        "PI-CS05.1": "Tiền xử lý dữ liệu và xây dựng pipeline tối thiểu để chuẩn bị dữ liệu cho phân tích/học máy.",
        "PI-CS05.2": "Huấn luyện mô hình và đánh giá kết quả bằng metric phù hợp với bài toán.",
        "PI-CS05.3": "Trực quan hóa, diễn giải và chuyển hóa kết quả mô hình thành đầu ra hữu ích cho bài toán thực tế.",
    },
    "PLO-CS06": {
        "PI-CS06.1": "Thiết kế được dữ liệu, luồng xử lý hoặc kiến trúc giải pháp ở mức phù hợp với bài toán dữ liệu/AI.",
        "PI-CS06.2": "Đề xuất được các kiểm soát an toàn dữ liệu, quyền riêng tư và kiểm soát truy cập cơ bản trong giải pháp.",
        "PI-CS06.3": "Đánh giá được kiến trúc/giải pháp theo các tiêu chí hiệu năng, độ tin cậy, khả vận hành ở mức cơ bản.",
    },
    "PLO-CS07": {
        "PI-CS07.1": "Trình bày kết quả phân tích/mô hình hóa bằng báo cáo hoặc slide theo cấu trúc khoa học, rõ với cả đối tượng kỹ thuật và phi kỹ thuật.",
        "PI-CS07.2": "Phối hợp nhóm, phản hồi review và retrospective theo quy trình làm việc đã thống nhất.",
        "PI-CS07.3": "Diễn giải được kết quả, insight hoặc quyết định kỹ thuật cho stakeholder kèm căn cứ dữ liệu/metric.",
    },
    "PLO-CS08": {
        "PI-CS08.1": "Lập được kế hoạch tự học/tự nghiên cứu và xây dựng portfolio minh chứng cho quá trình phát triển năng lực.",
        "PI-CS08.2": "Thực hiện được mini research ở mức phù hợp, gồm survey tài liệu và baseline experiment.",
        "PI-CS08.3": "Đề xuất được hướng nghề, hướng ứng dụng hoặc ý tưởng cải tiến và đánh giá sơ bộ tính khả thi.",
    },
}

# NL3 mapping cho KHMT
KHMT_NL3_PLO_MAP: Dict[str, str] = {
    "NL3-01": "PLO-CS05",  # Thu thập–trích xuất–chuẩn hoá dữ liệu (BI)
    "NL3-02": "PLO-CS02",  # Phân tích xu hướng và diễn giải nguyên nhân bằng dữ liệu
    "NL3-03": "PLO-CS07",  # Thiết kế và công bố dashboard/báo cáo KPI
    "NL3-04": "PLO-CS06",  # Thiết lập và vận hành CI/CD
    "NL3-05": "PLO-CS08",  # Triển khai và chuẩn hoá môi trường chạy (Linux/container)
    "NL3-06": "PLO-CS01",  # Giám sát và xử lý sự cố hệ thống (ITSM)
    "NL3-07": "PLO-CS03",  # Thiết kế và thực thi kiểm thử
    "NL3-08": "PLO-CS04",  # Phát triển và tối ưu phần mềm nhúng (MCU/RTOS)
}


# ============================================================
# PROGRAM REGISTRY - Danh mục các chương trình đào tạo
# ============================================================

PROGRAM_DATA: Dict[str, dict] = {
    "GENERIC": {
        "name": "Chương trình chung (Khoa CNTT)",
        "code": "GENERIC",
        "plo": PLO_DATA,
        "pi": PI_DATA,
        "nl3_plo_map": {},
        "po": {},
        "docs_path": None,
    },
    "HTTT": {
        "name": "Hệ thống thông tin",
        "code": "HTTT",
        "plo": HTTT_PLO_DATA,
        "pi": HTTT_PI_DATA,
        "nl3_plo_map": HTTT_NL3_PLO_MAP,
        "po": HTTT_PO_DATA,
        "docs_path": "TailieuMD/HTTT",
    },
    "KHMT": {
        "name": "Khoa học máy tính",
        "code": "KHMT",
        "plo": KHMT_PLO_DATA,
        "pi": KHMT_PI_DATA,
        "nl3_plo_map": KHMT_NL3_PLO_MAP,
        "po": {},
        "docs_path": "TailieuMD/KHMT",
    },
}

# Combined lookup (tất cả chương trình)
ALL_PLO_DATA: Dict[str, str] = {**PLO_DATA, **HTTT_PLO_DATA, **KHMT_PLO_DATA}
ALL_PI_DATA: Dict[str, Dict[str, str]] = {**PI_DATA, **HTTT_PI_DATA, **KHMT_PI_DATA}


# ============================================================
# EXTENDED HELPER FUNCTIONS (multi-program aware)
# ============================================================

def get_program_plo_data(program: str) -> Dict[str, str]:
    """Lấy PLO_DATA cho chương trình cụ thể."""
    return PROGRAM_DATA.get(program, PROGRAM_DATA["GENERIC"])["plo"]


def get_program_pi_data(program: str) -> Dict[str, Dict[str, str]]:
    """Lấy PI_DATA cho chương trình cụ thể."""
    return PROGRAM_DATA.get(program, PROGRAM_DATA["GENERIC"])["pi"]


def get_program_list() -> List[str]:
    """Trả về danh sách mã chương trình đào tạo."""
    return list(PROGRAM_DATA.keys())


def get_pi_description_extended(pi_code: str) -> str:
    """Lấy mô tả PI từ tất cả chương trình."""
    for plo, pis in ALL_PI_DATA.items():
        if pi_code in pis:
            return pis[pi_code]
    return ""


def get_plo_for_pi_extended(pi_code: str) -> str:
    """Xác định PLO chứa PI này từ tất cả chương trình."""
    for plo, pis in ALL_PI_DATA.items():
        if pi_code in pis:
            return plo
    return ""


def get_pi_list_text_for_program(program: str = "GENERIC") -> str:
    """Trả về danh sách PI dạng text cho chương trình cụ thể."""
    plo_data = get_program_plo_data(program)
    pi_data = get_program_pi_data(program)
    lines = []
    for plo_code, pis in pi_data.items():
        plo_desc = plo_data.get(plo_code, "")
        lines.append(f"\n{plo_code}: {plo_desc}")
        for pi_code, pi_desc in pis.items():
            lines.append(f"  {pi_code}: {pi_desc}")
    return "\n".join(lines)


def get_plo_list_text_for_program(program: str = "GENERIC") -> str:
    """Trả về danh sách PLO dạng text cho chương trình cụ thể."""
    plo_data = get_program_plo_data(program)
    lines = [f"{code}: {desc}" for code, desc in plo_data.items()]
    return "\n".join(lines)


def detect_program_from_plo(plo_code: str) -> str:
    """Xác định chương trình từ mã PLO."""
    if plo_code.startswith("PLO-IS"):
        return "HTTT"
    if plo_code.startswith("PLO-CS"):
        return "KHMT"
    return "GENERIC"
