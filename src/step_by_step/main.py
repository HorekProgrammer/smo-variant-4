import argparse

try:
    from .model import Model
except ImportError:  # Direct launch: python src/step_by_step/main.py
    from model import Model


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="СМО, вариант 4 — пошаговый режим ОД1")
    parser.add_argument("--steps", type=int, default=20, help="максимальное число событий")
    parser.add_argument("--seed", type=int, default=4, help="seed генератора")
    parser.add_argument(
        "--auto", action="store_true", help="не ждать Enter между событиями"
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    model = Model(
        buffer_capacity=3,
        sources_params=[(1.0, 3.0), (1.5, 3.5), (2.0, 4.0)],
        devices_params=[0.45, 0.55],
        seed=args.seed,
    )

    print("=== СМО: СЕРВИС АНАЛИТИЧЕСКИХ ЗАДАНИЙ, ВАРИАНТ 4 (ОД1) ===")
    print("Enter — следующее событие, q — выход. Параметры можно изменить в main.py.\n")
    for _ in range(max(args.steps, 0)):
        if not args.auto and input("Следующее событие? ").strip().lower() == "q":
            break
        if not model.step():
            print("Календарь событий пуст.")
            break
        model.print_state()

    average_wait = (
        model.total_waiting_time / model.total_processed
        if model.total_processed
        else 0.0
    )
    print("\n=== ИТОГИ ===")
    print(f"Создано: {model.total_generated}")
    print(f"Обработано: {model.total_processed}")
    print(f"Отказов: {model.total_rejected}")
    print(f"Вероятность отказа: {model.rejection_probability:.4f}")
    print(f"Среднее ожидание обработанных заявок: {average_wait:.3f}")


if __name__ == "__main__":
    main()

