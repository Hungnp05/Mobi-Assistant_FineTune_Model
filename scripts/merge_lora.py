import argparse

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


def main():
    parser = argparse.ArgumentParser(description="Merge LoRA adapter into base model")
    parser.add_argument("--base-model", type=str, default="google/gemma-2-2b-it")
    parser.add_argument("--adapter-dir", type=str, default="../output/gemma-mobi-assistant")
    parser.add_argument("--output-dir", type=str, default="../output/gemma-mobi-assistant-merged")
    args = parser.parse_args()

    print(f"Loading base model: {args.base_model}")
    base_model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.bfloat16,
        device_map="cpu",  # merge trên CPU để tránh hết VRAM, không cần GPU ở bước này
    )
    tokenizer = AutoTokenizer.from_pretrained(args.base_model)

    print(f"Loading LoRA adapter từ: {args.adapter_dir}")
    model = PeftModel.from_pretrained(base_model, args.adapter_dir)

    print("Merging adapter vào base model...")
    merged_model = model.merge_and_unload()

    print(f"Lưu model đã merge vào: {args.output_dir}")
    merged_model.save_pretrained(args.output_dir, safe_serialization=True)
    tokenizer.save_pretrained(args.output_dir)

    print("\nHoàn tất! Bước tiếp theo:")
    print("  python convert_to_mediapipe.py --model-dir", args.output_dir)


if __name__ == "__main__":
    main()
