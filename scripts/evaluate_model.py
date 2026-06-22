import argparse
import json
import re

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def extract_json(text: str):
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def build_prompt(instruction: str, user_input: str) -> str:
    return (
        f"<start_of_turn>user\n{instruction}\n\n"
        f"User: \"{user_input}\"\nResponse:<end_of_turn>\n"
        f"<start_of_turn>model\n"
    )


def main():
    parser = argparse.ArgumentParser(description="Evaluate fine-tuned model on validation set")
    parser.add_argument("--model-dir", type=str, default="../output/gemma-mobi-assistant-merged")
    parser.add_argument("--val-file", type=str, default="../data/val.jsonl")
    parser.add_argument("--max-samples", type=int, default=200)
    parser.add_argument("--show-errors", type=int, default=10,
                         help="Số lượng ví dụ sai để in ra debug")
    args = parser.parse_args()

    print(f"Loading model từ: {args.model_dir}")
    tokenizer = AutoTokenizer.from_pretrained(args.model_dir)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_dir,
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else "cpu",
    )
    model.eval()

    examples = []
    with open(args.val_file, "r", encoding="utf-8") as f:
        for line in f:
            examples.append(json.loads(line))
    examples = examples[: args.max_samples]

    total = 0
    valid_json_count = 0
    correct_action_count = 0
    errors = []

    print(f"\nĐánh giá trên {len(examples)} mẫu validation...\n")

    for ex in examples:
        prompt = build_prompt(ex["instruction"], ex["input"])
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=False,
                temperature=1.0,
                pad_token_id=tokenizer.eos_token_id,
            )

        generated = tokenizer.decode(
            output_ids[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True,
        )

        predicted = extract_json(generated)
        expected = json.loads(ex["output"])

        total += 1
        is_valid_json = predicted is not None
        if is_valid_json:
            valid_json_count += 1

        is_correct_action = is_valid_json and predicted.get("action") == expected.get("action")
        if is_correct_action:
            correct_action_count += 1
        else:
            errors.append({
                "input": ex["input"],
                "expected_action": expected.get("action"),
                "predicted_raw": generated[:200],
            })

    print("=" * 60)
    print(f"Tổng số mẫu:              {total}")
    print(f"JSON hợp lệ:              {valid_json_count}/{total} ({100*valid_json_count/total:.1f}%)")
    print(f"Action dự đoán đúng:      {correct_action_count}/{total} ({100*correct_action_count/total:.1f}%)")
    print("=" * 60)

    if errors and args.show_errors > 0:
        print(f"\n--- {min(args.show_errors, len(errors))} ví dụ DỰ ĐOÁN SAI ---\n")
        for err in errors[: args.show_errors]:
            print(f"Input:    {err['input']}")
            print(f"Expected: {err['expected_action']}")
            print(f"Got:      {err['predicted_raw']}")
            print("-" * 40)

    accuracy = correct_action_count / total if total > 0 else 0
    if accuracy < 0.85:
        print("\n⚠️  Độ chính xác dưới 85%. Khuyến nghị:")
        print("   - Tăng số epoch huấn luyện")
        print("   - Tăng số lượng dữ liệu training (chạy generate_dataset.py với --count lớn hơn)")
        print("   - Kiểm tra lại các template trong generate_dataset.py có đủ đa dạng chưa")
    else:
        print(f"\n✅ Độ chính xác {100*accuracy:.1f}% — đủ tốt để convert sang .task")


if __name__ == "__main__":
    main()
