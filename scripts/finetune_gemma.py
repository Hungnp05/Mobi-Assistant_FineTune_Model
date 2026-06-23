import argparse
import json
import os

import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from trl import SFTTrainer, SFTConfig


# 1. FORMAT PROMPT — ghép instruction + input + output theo chuẩn Gemma
def format_example(example):
    """
    Gemma chat template:
    <start_of_turn>user
    {instruction}\n{input}<end_of_turn>
    <start_of_turn>model
    {output}<end_of_turn>
    """
    text = (
        f"<start_of_turn>user\n{example['instruction']}\n\n"
        f"User: \"{example['input']}\"\nResponse:<end_of_turn>\n"
        f"<start_of_turn>model\n{example['output']}<end_of_turn>"
    )
    return {"text": text}


def load_and_prepare_dataset(train_file, val_file, tokenizer):
    train_ds = load_dataset("json", data_files=train_file, split="train")
    val_ds = load_dataset("json", data_files=val_file, split="train")

    train_ds = train_ds.map(format_example, remove_columns=train_ds.column_names)
    val_ds = val_ds.map(format_example, remove_columns=val_ds.column_names)

    print(f"Train examples: {len(train_ds)}")
    print(f"Val examples:   {len(val_ds)}")
    print("\n--- Ví dụ 1 mẫu đã format ---")
    print(train_ds[0]["text"])
    print("--- Hết ví dụ ---\n")

    return train_ds, val_ds


# 2. LOAD MODEL với 4-bit quantization để fit GPU nhỏ (QLoRA)
def load_model_and_tokenizer(base_model_name, use_4bit=True):
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    tokenizer.pad_token = tokenizer.eos_token

    if use_4bit and torch.cuda.is_available():
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            quantization_config=bnb_config,
            device_map="auto",
            torch_dtype=torch.bfloat16,
        )
        model = prepare_model_for_kbit_training(model)
    else:
        # CPU fallback hoặc full precision (chậm hơn nhiều, chỉ dùng khi test)
        model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=torch.float32,
            device_map="cpu",
        )

    return model, tokenizer


# 3. LORA CONFIG — chỉ train một phần nhỏ tham số, nhẹ và nhanh
def get_lora_config():
    return LoraConfig(
        r=16,                    # rank — tăng lên 32/64 nếu cần model học sâu hơn
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
    )


# 4. MAIN TRAINING LOOP
def main():
    parser = argparse.ArgumentParser(description="Fine-tune Gemma for Mobi-Assistant intent parsing")
    parser.add_argument("--base-model", type=str, default="google/gemma-2-2b-it",
                         help="Model gốc từ HuggingFace. Dùng gemma-2-2b-it (nhẹ, on-device tốt) "
                              "hoặc gemma-2-9b-it (cần GPU mạnh hơn)")
    parser.add_argument("--train-file", type=str, default="../data/train.jsonl")
    parser.add_argument("--val-file", type=str, default="../data/val.jsonl")
    parser.add_argument("--output-dir", type=str, default="../output/gemma-mobi-assistant")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--max-seq-length", type=int, default=512)
    parser.add_argument("--no-4bit", action="store_true",
                         help="Tắt 4-bit quantization (chỉ dùng khi test trên CPU)")
    args = parser.parse_args()

    print(f"Loading base model: {args.base_model}")
    model, tokenizer = load_model_and_tokenizer(args.base_model, use_4bit=not args.no_4bit)

    print("Preparing LoRA adapters...")
    lora_config = get_lora_config()
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    print("Loading dataset...")
    train_ds, val_ds = load_and_prepare_dataset(args.train_file, args.val_file, tokenizer)

    sft_config = SFTConfig(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=4,
        learning_rate=args.learning_rate,
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=50,
        save_strategy="epoch",
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
        bf16=torch.cuda.is_available(),
        max_seq_length=args.max_seq_length,
        dataset_text_field="text",
        report_to="none",  # đổi thành "wandb" nếu muốn theo dõi trực quan
        save_total_limit=2,
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        tokenizer=tokenizer,
    )

    print("\nBắt đầu training...\n")
    trainer.train()

    print(f"\nLưu model adapter LoRA vào: {args.output_dir}")
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    print("\nHoàn tất! Bước tiếp theo:")
    print("  1. Merge LoRA vào base model:  python merge_lora.py")
    print("  2. Convert sang .task cho Android: python convert_to_mediapipe.py")


if __name__ == "__main__":
    main()
