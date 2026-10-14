import glob
import os.path
import shutil
import string
import time
from pathlib import Path

ACTIVITY_DIR = Path(__file__).resolve().parents[1]
DATA_FOLDER = ACTIVITY_DIR / "data"
INPUT_FOLDER = ACTIVITY_DIR / "temp" / "input"
OUTPUT_FOLDER = ACTIVITY_DIR / "temp" / "output"
SUBMISSION_FOLDER = ACTIVITY_DIR / "submission"


# -----------------------------------------------------------------------------
# Utilidades de carpetas
# -----------------------------------------------------------------------------
def clear_folder(folder):
    for file in glob.glob(f"{folder}/*"):
        os.remove(file)


def initialize_folder(folder):
    """Deja la carpeta existente y vacia."""
    if os.path.exists(folder):
        clear_folder(folder)
    else:
        os.makedirs(folder)


def delete_folder(folder):
    if os.path.exists(folder):
        shutil.rmtree(folder)


def generate_file_copies(n):
    for file in glob.glob(f"{DATA_FOLDER}/*"):
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()

        raw_filename_with_extension = os.path.basename(file)
        raw_filename_without_extension = os.path.splitext(raw_filename_with_extension)[0]

        for i in range(1, n + 1):
            new_filename = f"{raw_filename_without_extension}_{i:05d}.txt"
            with open(f"{INPUT_FOLDER}/{new_filename}", "w", encoding="utf-8") as f2:
                f2.write(text)


# -----------------------------------------------------------------------------
# Mapper y reducer
# -----------------------------------------------------------------------------
PUNCTUATION_TABLE = str.maketrans("", "", string.punctuation)


def mapper(sequence):
    pairs_sequence = []
    for _, line in sequence:
        line = line.lower()
        line = line.translate(PUNCTUATION_TABLE)
        line = line.replace("\n", "")
        words = line.split()
        pairs_sequence.extend([(word, 1) for word in words])
    return pairs_sequence


def reducer(pairs_sequence):
    result = []
    for key, value in pairs_sequence:
        if result and result[-1][0] == key:
            result[-1] = (key, result[-1][1] + value)
        else:
            result.append((key, value))
    return result


# -----------------------------------------------------------------------------
# Simulacion de Hadoop
# -----------------------------------------------------------------------------
def hadoop(input_folder, output_folder, mapper, reducer):

    def create_output_directory(output_dir):
        # Como en Hadoop real: falla si la salida ya existe
        if os.path.exists(output_dir):
            raise FileExistsError(f"La carpeta {output_dir} ya existe.")
        os.makedirs(output_dir)

    def read_records_from_input(input_dir):
        sequence = []
        files = glob.glob(f"{input_dir}/*")
        for file in files:
            with open(file, "r", encoding="utf-8") as f:
                for line in f:
                    sequence.append((file, line))
        return sequence

    def shuffle_and_sort(pairs_sequence):
        return sorted(pairs_sequence)

    def save_results_to_output(output_dir, result):
        with open(f"{output_dir}/part-00000", "w", encoding="utf-8") as f:
            for key, value in result:
                f.write(f"{key}\t{value}\n")

    def create_success_file(output_dir):
        with open(f"{output_dir}/_SUCCESS", "w", encoding="utf-8") as f:
            f.write("")

    create_output_directory(output_folder)
    sequence = read_records_from_input(input_folder)
    pairs_sequence = mapper(sequence)
    pairs_sequence = shuffle_and_sort(pairs_sequence)
    result = reducer(pairs_sequence)
    save_results_to_output(output_folder, result)
    create_success_file(output_folder)


# -----------------------------------------------------------------------------
# Ejecucion
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    n = 1000

    initialize_folder(INPUT_FOLDER)
    delete_folder(OUTPUT_FOLDER)
    generate_file_copies(n)

    start_time = time.time()

    hadoop(
        input_folder=INPUT_FOLDER,
        output_folder=OUTPUT_FOLDER,
        mapper=mapper,
        reducer=reducer,
    )

    end_time = time.time()
    print(f"Tiempo de ejecución: {end_time - start_time:.2f} segundos")

    # Copiar el resultado a submission/ (lo que revisa el test)
    delete_folder(SUBMISSION_FOLDER)
    shutil.copytree(OUTPUT_FOLDER, SUBMISSION_FOLDER)