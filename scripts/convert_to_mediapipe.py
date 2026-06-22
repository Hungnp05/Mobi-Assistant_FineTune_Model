import argparse
import os
import shutil
import tempfile


def convert_to_tflite(model_dir: str, tflite_output: str, quantize: str):
    """
    Convert checkpoint HuggingFace sang TFLite bằng ai-edge-torch.
    Đây là bước nặng nhất, có thể tốn 10-30 phút tùy máy.
    """
    try:
        import ai_edge_torch
        from ai_edge_torch.generative.examples.gemma import gemma2
        from ai_edge_torch.generative.utilities import converter
    except ImportError:
        raise RuntimeError(
            "Chưa cài ai-edge-torch. Chạy: pip install ai-edge-torch-nightly\n"
            "Nếu vẫn lỗi import, xem hướng dẫn mới nhất tại:\n"
            "https://github.com/google-ai-edge/ai-edge-torch"
        )

    print(f"Đang convert model từ: {model_dir}")
    print(f"Quantization: {quantize}")

    # Build model Gemma2 từ checkpoint đã fine-tune
    pytorch_model = gemma2.build_2b_model(model_dir)

    quant_config = None
    if quantize == "int8":
        from ai_edge_torch.generative.quantize import quant_recipes
        quant_config = quant_recipes.full_int8_dynamic_recipe()
    elif quantize == "int4":
        from ai_edge_torch.generative.quantize import quant_recipes
        quant_config = quant_recipes.full_weight_only_recipe()

    converter.convert_to_tflite(
        pytorch_model,
        output_path=os.path.dirname(tflite_output),
        output_name_prefix=os.path.splitext(os.path.basename(tflite_output))[0],
        prefill_seq_len=512,
        quantize=quant_config is not None,
        quant_config=quant_config,
    )

    print(f"Đã tạo file TFLite: {tflite_output}")


def bundle_to_task(tflite_path: str, tokenizer_dir: str, task_output: str):
    """
    Bundle .tflite + tokenizer.model thành 1 file .task duy nhất mà
    MediaPipe LlmInference.createFromOptions() có thể load trực tiếp.
    """
    try:
        from mediapipe.tasks.python.genai import bundler
    except ImportError:
        raise RuntimeError(
            "Chưa cài mediapipe. Chạy: pip install mediapipe"
        )

    tokenizer_path = os.path.join(tokenizer_dir, "tokenizer.model")
    if not os.path.exists(tokenizer_path):
        # Một số tokenizer Gemma lưu dạng .json, thử fallback
        tokenizer_path = os.path.join(tokenizer_dir, "tokenizer.json")

    config = bundler.BundleConfig(
        tflite_model=tflite_path,
        tokenizer_model=tokenizer_path,
        start_token="<bos>",
        stop_tokens=["<eos>", "<end_of_turn>"],
        output_filename=task_output,
        enable_bytes_to_unicode_mapping=True,
    )

    print(f"Đang bundle thành file .task: {task_output}")
    bundler.create_bundle(config)
    print("Hoàn tất bundling!")


def main():
    parser = argparse.ArgumentParser(description="Convert fine-tuned Gemma to MediaPipe .task format")
    parser.add_argument("--model-dir", type=str, default="../output/gemma-mobi-assistant-merged")
    parser.add_argument("--output-file", type=str, default="../output/gemma_finetuned.task")
    parser.add_argument("--quantize", type=str, default="int8", choices=["none", "int8", "int4"],
                         help="int8 = cân bằng tốt nhất cho điện thoại tầm trung. "
                              "int4 = nhẹ hơn nữa nhưng giảm độ chính xác.")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output_file) or ".", exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tflite_path = os.path.join(tmpdir, "model.tflite")

        convert_to_tflite(args.model_dir, tflite_path, args.quantize)
        bundle_to_task(tflite_path, args.model_dir, args.output_file)

    size_mb = os.path.getsize(args.output_file) / (1024 * 1024)
    print(f"\nFile model cuối cùng: {args.output_file} ({size_mb:.1f} MB)")
    print("\nBước cuối — push vào điện thoại:")
    print(f"  adb push {args.output_file} /data/local/tmp/")
    print(f"  adb shell run-as com.mobi.assistant cp /data/local/tmp/"
          f"{os.path.basename(args.output_file)} /data/data/com.mobi.assistant/files/gemma_finetuned.task")
    print("\nSau đó vào app Mobi-Assistant -> Cài đặt -> chọn chế độ 'Offline (Model Fine-tune)'")


if __name__ == "__main__":
    main()
