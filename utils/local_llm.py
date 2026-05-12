import json
import torch
import re
from transformers import AutoModelForCausalLM, AutoTokenizer
from config import LOCAL_MODEL_NAME

_model = None
_tokenizer = None

def load_model():
    global _model, _tokenizer
    if _model is not None:
        return _model, _tokenizer
    print(f"Đang tải model {LOCAL_MODEL_NAME} lên GPU...")
    _tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL_NAME)
    _model = AutoModelForCausalLM.from_pretrained(
        LOCAL_MODEL_NAME,
        dtype=torch.bfloat16,
        device_map="auto",
        offload_folder=None,
    )
    print(f"Model đã sẵn sàng trên thiết bị: {_model.device}")
    print(f"GPU memory allocated: {torch.cuda.memory_allocated()/1024**3:.1f} GB")
    return _model, _tokenizer

def _repair_truncated_json(raw_text: str) -> str:
    """Cố gắng sửa JSON bị cắt bằng cách đóng các ngoặc còn mở."""
    # Đếm số dấu { } [ ]
    open_braces = raw_text.count('{') - raw_text.count('}')
    open_brackets = raw_text.count('[') - raw_text.count(']')
    # Thêm dấu đóng còn thiếu
    repaired = raw_text + '}' * open_braces + ']' * open_brackets
    return repaired

def generate_response(messages, max_new_tokens=4096, temperature=0.0):
    model, tokenizer = load_model()
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    if temperature == 0.0:
        gen_kwargs = dict(max_new_tokens=max_new_tokens, do_sample=False)
    else:
        gen_kwargs = dict(max_new_tokens=max_new_tokens, do_sample=True, temperature=temperature)

    with torch.no_grad():
        outputs = model.generate(**inputs, **gen_kwargs)

    input_len = inputs.input_ids.shape[1]
    generated_ids = outputs[:, input_len:]
    raw_response = tokenizer.decode(generated_ids[0], skip_special_tokens=True)

    # --- Post‑process để tăng cơ hội parse được JSON ---

    # 1. Bóc markdown code block nếu có
    md_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw_response)
    if md_match:
        raw_response = md_match.group(1).strip()

    # 2. Nếu response bắt đầu bằng {, thử parse ngay
    stripped = raw_response.strip()
    if stripped.startswith('{'):
        try:
            json.loads(stripped)
            return stripped
        except json.JSONDecodeError:
            # Thử sửa JSON bị cắt
            repaired = _repair_truncated_json(stripped)
            try:
                json.loads(repaired)
                return repaired
            except json.JSONDecodeError:
                pass

    # 3. Nếu không có { ở đầu, tìm vị trí bắt đầu JSON
    start = raw_response.find('{')
    if start != -1:
        json_candidate = raw_response[start:]
        try:
            json.loads(json_candidate)
            return json_candidate
        except json.JSONDecodeError:
            repaired = _repair_truncated_json(json_candidate)
            try:
                json.loads(repaired)
                return repaired
            except json.JSONDecodeError:
                pass

    # 4. Trả về raw nếu mọi cách đều thất bại
    return raw_response
