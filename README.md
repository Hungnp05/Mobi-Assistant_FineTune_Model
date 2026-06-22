# Gemma Fine-tune Toolkit cho Mobi-Assistant

Bộ công cụ fine-tune model Gemma để hiểu lệnh tiếng Việt/Anh, chạy hoàn toàn
offline trên điện thoại Android qua MediaPipe LLM Inference.

## Quy trình tổng quan

```
1. generate_dataset.py      → Sinh dữ liệu huấn luyện (Faker)
2. finetune_gemma.py        → Fine-tune bằng LoRA (cần GPU)
3. evaluate_model.py        → Đánh giá độ chính xác
4. merge_lora.py            → Merge LoRA adapter vào model gốc
5. convert_to_mediapipe.py  → Convert sang .task cho Android
6. adb push                 → Đưa file .task vào điện thoại
```

---

## Bước 0 — Cài đặt môi trường (VS Code)

```bash
# Tạo virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Cài dependencies
pip install -r requirements.txt

# Đăng nhập HuggingFace để tải model Gemma (cần accept license)
huggingface-cli login
```

Trước khi login, vào https://huggingface.co/google/gemma-2-2b-it và bấm
**Agree and access repository** để được phép tải model.

---

## Bước 1 — Sinh dữ liệu huấn luyện

```bash
cd scripts
python generate_dataset.py --count 8000 --output ../data/train.jsonl --seed 42
```

Script sinh dữ liệu cho 9 intent: `SET_ALARM`, `CANCEL_ALARM`, `FETCH_NEWS`,
`SUMMARIZE_EMAIL`, `SET_APP_LIMIT`, `BLOCK_APP`/`UNBLOCK_APP`, `QUERY_USAGE`,
`SET_WIFI_SCHEDULE`/`SET_DND_SCHEDULE`, và `UNKNOWN` (câu mơ hồ).

Các ngữ cảnh thời gian được sinh đa dạng: "ngày mai", "ngày kia", "hàng ngày",
"9h tối", "7h30 sáng", "tuần sau", v.v. — đúng yêu cầu hiểu ngữ cảnh thời gian.

**Khuyến nghị số lượng mẫu:**
| Mục đích | Số mẫu |
|---|---|
| Test nhanh pipeline | 500 |
| Fine-tune cơ bản | 3,000 - 5,000 |
| Production chất lượng cao | 8,000 - 15,000 |

File output: `data/train.jsonl` (90%) và `data/val.jsonl` (10%).

### Tùy biến thêm intent riêng

Mở `generate_dataset.py`, thêm hàm `gen_<intent_mới>(n)` theo mẫu các hàm
có sẵn, rồi thêm vào dict `GENERATORS` ở cuối file với tỉ lệ mong muốn.

---

## Bước 2 — Fine-tune model

**Yêu cầu GPU:**
| Model | VRAM tối thiểu | Khuyến nghị |
|---|---|---|
| gemma-2-2b-it | 8GB | RTX 3060 12GB+ |
| gemma-2-9b-it | 20GB | RTX 4090 24GB |

**Không có GPU?** Dùng Google Colab miễn phí (T4 GPU 16GB):
1. Upload toàn bộ thư mục `gemma-finetune/` lên Google Drive
2. Mở Colab notebook mới, mount Drive, `cd` vào thư mục
3. Chạy y nguyên các lệnh dưới đây trong Colab cell

```bash
cd scripts
python finetune_gemma.py \
    --base-model google/gemma-2-2b-it \
    --train-file ../data/train.jsonl \
    --val-file ../data/val.jsonl \
    --output-dir ../output/gemma-mobi-assistant \
    --epochs 3 \
    --batch-size 4 \
    --learning-rate 2e-4
```

Thời gian train (ước tính với 5,000 mẫu, 3 epoch):
- RTX 3060: ~25-35 phút
- RTX 4090: ~10-15 phút
- Colab T4: ~30-45 phút

Theo dõi `eval_loss` trong log — nếu loss không giảm sau epoch 2, dữ liệu
có thể chưa đủ đa dạng, quay lại Bước 1 sinh thêm.

---

## Bước 3 — Đánh giá chất lượng

```bash
python evaluate_model.py \
    --model-dir ../output/gemma-mobi-assistant \
    --val-file ../data/val.jsonl \
    --max-samples 200
```

**Lưu ý:** Bước này load trực tiếp từ checkpoint LoRA adapter (chưa merge),
transformers sẽ tự load đúng nếu adapter và base model cùng thư mục cha
phù hợp. Nếu lỗi, merge trước (Bước 4) rồi evaluate lại trên model đã merge.

Mục tiêu: **accuracy ≥ 90%** trên action classification trước khi convert.
Nếu thấp hơn, tăng `--count` ở Bước 1 hoặc `--epochs` ở Bước 2.

---

## Bước 4 — Merge LoRA vào model gốc

```bash
python merge_lora.py \
    --base-model google/gemma-2-2b-it \
    --adapter-dir ../output/gemma-mobi-assistant \
    --output-dir ../output/gemma-mobi-assistant-merged
```

---

## Bước 5 — Convert sang .task cho Android

```bash
pip install ai-edge-torch-nightly mediapipe

python convert_to_mediapipe.py \
    --model-dir ../output/gemma-mobi-assistant-merged \
    --output-file ../output/gemma_finetuned.task \
    --quantize int8
```

**Chọn mức quantize theo máy đích:**
| Mức | Kích thước file | Phù hợp với |
|---|---|---|
| `int8` | ~1.2-1.5GB (model 2B) | Điện thoại tầm trung-cao (RAM 6GB+) |
| `int4` | ~600-800MB (model 2B) | Điện thoại tầm trung (RAM 4GB), chạy nhanh hơn |

Với Samsung A12 (Helio G35, RAM 4GB) — khuyến nghị `int4` để tránh quá tải RAM.

---

## Bước 6 — Đưa model vào điện thoại

```bash
adb push ../output/gemma_finetuned.task /data/local/tmp/

adb shell run-as com.mobi.assistant cp \
    /data/local/tmp/gemma_finetuned.task \
    /data/data/com.mobi.assistant/files/gemma_finetuned.task
```

Mở app Mobi-Assistant → **Cài đặt** → **Chế độ AI** → chọn **"Offline (Model
Fine-tune)"**. App sẽ tự nhận diện file và chuyển sang dùng model fine-tune.

---

## Cấu trúc thư mục

```
gemma-finetune/
├── requirements.txt
├── README.md                      (file này)
├── data/
│   ├── train.jsonl                (sinh từ Bước 1)
│   └── val.jsonl
├── scripts/
│   ├── generate_dataset.py        (Bước 1)
│   ├── finetune_gemma.py          (Bước 2)
│   ├── evaluate_model.py          (Bước 3)
│   ├── merge_lora.py              (Bước 4)
│   └── convert_to_mediapipe.py    (Bước 5)
└── output/
    ├── gemma-mobi-assistant/          (LoRA adapter, vài chục MB)
    ├── gemma-mobi-assistant-merged/   (model đầy đủ, vài GB)
    └── gemma_finetuned.task           (file cuối cùng, đưa vào điện thoại)
```

---

## Khắc phục lỗi thường gặp

**`OutOfMemoryError` khi training** → giảm `--batch-size` xuống 2 hoặc 1,
tăng `gradient_accumulation_steps` trong `finetune_gemma.py` để bù lại.

**`401 Unauthorized` khi tải model Gemma** → chưa accept license trên
HuggingFace hoặc chưa `huggingface-cli login`.

**`ai_edge_torch` import error** → công cụ này cập nhật API thường xuyên,
kiểm tra phiên bản nightly mới nhất: `pip install ai-edge-torch-nightly --upgrade`

**Model trả JSON sai cấu trúc sau fine-tune** → kiểm tra lại
`evaluate_model.py`, có thể cần thêm dữ liệu cho intent đang sai nhiều nhất.

**App Android báo "RET_CHECK failure" khi chạy model fine-tune** → thường do
quantize quá mạnh (int4) làm model không ổn định trên một số chip. Thử lại
với `int8`, hoặc dùng model 2B thay vì 4B.
