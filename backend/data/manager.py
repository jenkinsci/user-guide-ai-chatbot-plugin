from data.collection.collectors import start_collectors
from .preprocessing.processors import start_processors
from .formatting.formatters import start_formatters
from .chunking.chunker import start_chunker
from .embedding.embedder import start_embedder

import os
from datetime import datetime
from pathlib import Path
from .tools.common import write_json_file, datetime_serializer
from .models import DataSource, DataPhase


def clear_terminal() -> None:
    "Clear the terminal screen based on the operating system"
    os.system("cls" if os.name == "nt" else "clear")


def collector_menu() -> list[DataSource]:
    "Print a menu which lets you pick which collectors to use."

    selected_sources: set[DataSource] = set()
    available_options: list[DataSource] = list(DataSource)

    while True:
        clear_terminal()

        # Display the application header
        print("=" * 50)
        print(" " * 10 + "DATA MANAGER SETUP")
        print("=" * 50)
        print("\nSelect the sources you want to scrape from.")
        print("Type the number to toggle a source, or 'C' to confirm.\n")

        # Display the interactive options list
        for index, source in enumerate(available_options, start=1):
            checkbox = "[X]" if source in selected_sources else "[ ]"
            # Format the enum name for better readability
            formatted_name = source.name.replace("_", " ").title()
            print(f"    {index}. {checkbox} {formatted_name}")

        print("\n" + "-" * 50)
        print("  [1-4] Toggle selection")
        print("  [C]   Confirm and start")
        print("  [Q]   Quit setup")
        print("-" * 50)

        # Capture user input
        user_input = input("\nYour choice: ").strip().lower()

        # Process the input
        if user_input == "c":
            break
        elif user_input == "q":
            print("\nSetup cancelled. Exiting collector.")
            return []
        elif user_input.isdigit():
            option_index = int(user_input) - 1

            # Validate the numeric input
            if 0 <= option_index < len(available_options):
                chosen_source = available_options[option_index]

                # Toggle the selection state
                if chosen_source in selected_sources:
                    selected_sources.remove(chosen_source)
                else:
                    selected_sources.add(chosen_source)
            else:
                input("\nInvalid number. Press Enter to try again...")
        else:
            input("\nInvalid command. Press Enter to try again...")

    # Finalize the selection
    clear_terminal()
    print("=" * 50)
    print(" " * 15 + "INITIALIZING")
    print("=" * 50)

    if not selected_sources:
        print("\nNo sources selected. Collector will not start.")
        return []

    print("\nStarting data collection for the following sources:\n")
    for source in selected_sources:
        print(f"  -> {source.value}")

    print("\n[Collector is now running...]")

    # Return the list of selected enums for the rest of your application
    return list(selected_sources)


def start_data_pipeline(selected_sources: list[DataSource], script_dir: Path):
    if not selected_sources:
        print("---- NO DATA SOURCE SELECTED ----")
        return

    output_dir = script_dir / "output"

    phase_fun = {
        DataPhase.COLLECTION: start_collectors,
        DataPhase.PREPROCESSING: start_processors,
        DataPhase.FORMATTING: start_formatters,
        DataPhase.CHUNKING: start_chunker,
        DataPhase.EMBEDDING: start_embedder,
    }

    manager_logs = {}
    manager_logs["start_date"] = datetime.now()
    manager_logs["phases"] = []
    manager_logs["selected_sources"] = [source.value for source in selected_sources]

    for phase, fun in phase_fun.items():
        phase_obj = {}

        phase_obj["name"] = phase.value
        phase_obj["start_date"] = datetime.now()

        # Execute the specific phase function
        fun(selected_sources, output_dir)

        phase_obj["end_date"] = datetime.now()
        manager_logs["phases"].append(phase_obj)

    manager_logs["end_date"] = datetime.now()

    LOGS_FILE_PATH = (
        script_dir
        / "logs"
        / f"logs_{manager_logs['start_date'].strftime("%Y-%m-%d_%H-%M-%S")}.json"
    )

    write_json_file(
        LOGS_FILE_PATH,
        manager_logs,
        indent=4,
        default=datetime_serializer,
        ensure_ascii=False,
    )


def start_manager():
    SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

    selected_sources = collector_menu()
    start_data_pipeline(selected_sources, SCRIPT_DIR)


if __name__ == "__main__":
    start_manager()
