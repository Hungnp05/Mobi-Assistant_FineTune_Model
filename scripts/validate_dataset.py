import argparse
import json
from collections import Counter

VALID_ACTIONS = {
    "SET_ALARM", "CANCEL_ALARM", "SET_APP_LIMIT", "BLOCK_APP", "UNBLOCK_APP",
    "SET_WIFI_SCHEDULE", "SET_DND_SCHEDULE", "FETCH_NEWS", "SUMMARIZE_EMAIL",
    "QUERY_USAGE", "UNKNOWN",
}


def main():
    parser = argparse.ArgumentParser(description="Validate generated training dataset")
    parser.add_argument("--file", type=str, required=True)
    args = parser.parse_args()

    total = 0
    invalid_json = 0
    invalid_action = 0
    action_counter = Counter()
    lang_counter = Counter()
    input_lengths = []

    with open(args.file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            total += 1
            try:
                ex = json.loads(line)
            except json.JSONDecodeError:
                print(f"[Dòng {line_num}] Lỗi parse JSON ở cấp ngoài (toàn dòng)")
                invalid_json += 1
                continue

            try:
                output = json.loads(ex["output"])
            except (json.JSONDecodeError, KeyError):
                print(f"[Dòng {line_num}] Field 'output' không phải JSON hợp lệ: {ex.get('output', '')[:80]}")
                invalid_json += 1
                continue

            action = output.get("action")
            if action not in VALID_ACTIONS:
                print(f"[Dòng {line_num}] Action không hợp lệ: {action}")
                invalid_action += 1
                continue

            action_counter[action] += 1
            lang_counter[output.get("language", "?")] += 1
            input_lengths.append(len(ex.get("input", "")))

    print("\n" + "=" * 50)
    print(f"Tổng số dòng:        {total}")
    print(f"JSON lỗi:            {invalid_json}")
    print(f"Action không hợp lệ: {invalid_action}")
    print(f"Hợp lệ:              {total - invalid_json - invalid_action} "
          f"({100*(total - invalid_json - invalid_action)/max(total,1):.1f}%)")
    print("=" * 50)

    print("\nPhân bố theo Action:")
    for action, count in action_counter.most_common():
        pct = 100 * count / total
        bar = "█" * int(pct / 2)
        print(f"  {action:20s} {count:5d} ({pct:4.1f}%) {bar}")

    print("\nPhân bố theo Ngôn ngữ:")
    for lang, count in lang_counter.most_common():
        print(f"  {lang:10s} {count:5d} ({100*count/total:.1f}%)")

    if input_lengths:
        avg_len = sum(input_lengths) / len(input_lengths)
        print(f"\nĐộ dài input trung bình: {avg_len:.1f} ký tự "
              f"(min={min(input_lengths)}, max={max(input_lengths)})")

    if invalid_json + invalid_action == 0:
        print("\n Dataset hợp lệ, sẵn sàng để training.")
    else:
        print(f"\n Có {invalid_json + invalid_action} dòng lỗi — kiểm tra lại "
              f"generate_dataset.py nếu số lượng lỗi lớn.")


if __name__ == "__main__":
    main()
