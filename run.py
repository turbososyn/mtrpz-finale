print("--- [run.py] Початок виконання ---")
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bot_main import main

if __name__ == "__main__":
    print("--- [run.py] Зараз буде запущено main() ---")
    main()
    print("--- [run.py] Виконання main() завершено ---")

