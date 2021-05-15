import os
from time import time
import wget
from alphapept.settings import load_settings
from alphapept.paths import DEFAULT_SETTINGS_PATH
from alphapept.speed import set_speed_mode

from alphapept.settings import load_settings
from alphapept.paths import DEFAULT_SETTINGS_PATH
from alphapept.speed import set_speed_mode
import sys

FILE_DICT = {}
FILE_DICT['thermo_IRT.raw'] = 'https://datashare.biochem.mpg.de/s/GpXsATZtMwgQoQt/download'
FILE_DICT['IRT_fasta.fasta'] = 'https://datashare.biochem.mpg.de/s/p8Qu3KolzbSiCHH/download'


tmp_folder = 'E:/test_temp/'

def delete_folder(dir_name):
    if os.path.exists(dir_name):
        shutil.rmtree(dir_name)


def create_folder(dir_name):
    if not os.path.exists(dir_name):
        logging.info(f'Creating dir {dir_name}.')
        os.makedirs(dir_name)

def main():
    mode = sys.argv[1]
    print(f"Testing with mode {mode}")

    delete_folder(tmp_folder)
    create_folder(tmp_folder)

    for file in FILE_DICT:
        target = os.path.join(tmp_folder, file)
        if not os.path.isfile(target):
            wget.download(FILE_DICT[file], target)

    settings = load_settings(DEFAULT_SETTINGS_PATH)
    settings['experiment']['file_paths'] =  [os.path.join(tmp_folder, 'thermo_IRT.raw')]
    settings['experiment']['fasta_paths'] = [os.path.join(tmp_folder, 'IRT_fasta.fasta')]

    set_speed_mode(mode)
    import alphapept.interface
    for _ in settings['workflow']:
        settings['workflow'][_] = False

    settings['workflow']['import_raw_data'] = True
    settings['workflow']['find_features'] = True

    start = time()
    settings_ = alphapept.interface.run_complete_workflow(settings)
    end = time()

    te = end-start

    print(f'Time elapsed {te}')

if __name__ == "__main__":
    main()
