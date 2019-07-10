import codecs
import gzip
import os
import pickle
from pathlib import Path

import seaborn as sns

BASE_PATH = Path(os.path.abspath(os.path.dirname(__file__)))


def load_csv_to_list(file_path):
    """
    Loads a csv file from the given filepath and returns its contents as a list of strings.

    >>> from pathlib import Path
    >>> from gender_analysis import common
    >>> corpus_metadata_path = Path(common.BASE_PATH, 'testing', 'corpora', 'sample_novels', 'sample_novels.csv')
    >>> corpus_metadata = load_csv_to_list(corpus_metadata_path)
    >>> type(corpus_metadata)
    <class 'list'>

    :param file_path: can be a string or Path object
    :return: a list of strings
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    file_type = file_path.suffix

    if file_type != '.csv':
        raise Exception(
            'Cannot load if current file type is not .csv'
        )
    else:
        file = open(file_path, encoding='utf-8')
        result = file.readlines()

    file.close()
    return result


def load_txt_to_string(file_path):
    """
    Loads a txt file and returns a str representation of it.

    >>> from pathlib import Path
    >>> from gender_analysis import common
    >>> novel_path = Path(common.BASE_PATH, 'testing', 'corpora', 'sample_novels', 'texts', 'austen_persuasion.txt')
    >>> novel_text = load_txt_to_string(novel_path)
    >>> type(novel_text), len(novel_text)
    (<class 'str'>, 486253)

    :param file_path: can be a string or Path object
    :return: the text as a string type
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    file_type = file_path.suffix

    if file_type != '.txt':
        raise Exception(
            'Cannot load if current file type is not .txt'
        )
    else:
        try:
            file = open(file_path, encoding='utf-8')
            result = file.read()
        except UnicodeDecodeError as err:
            print(f'Unicode file loading error {file_path}.')
            raise err

    file.close()
    return result


def store_pickle(obj, filepath):
    """
    Store a compressed "pickle" of the object in the "pickle_data" directory
    and return the full path to it.

    Example in lieu of Doctest to avoid writing out a file.

        my_object = {'a': 4, 'b': 5, 'c': [1, 2, 3]}
        gender_analysis.common.store_pickle(my_object, 'path_to_pickle/example_pickle.pgz')

    :param obj: Any Python object that can be pickled
    :param filepath: str | Path
    :return: Path
    """
    if isinstance(filepath, str):
        filepath = Path(filepath)
    if not isinstance(filepath, Path):
        raise ValueError(f'filepath must be a str or path object, not type {type(filepath)}')

    if filepath.stem == '':
        filepath = Path(str(filepath) + '.pgz')

    with gzip.GzipFile(filepath, 'w') as fileout:
        pickle.dump(obj, fileout)
    return filepath


def load_pickle(filepath):
    """
    Loads the pickle stored at a given filepath, and returns the Python object that was stored.

    Example in lieu of Doctest to avoid writing out a file.

        my_object = gender_analysis.common.load_pickle('path_to_pickle/example_pickle.pgz')
        my_object
        {'a': 4, 'b': 5, 'c': [1, 2, 3]}

    :param filepath: str | Path
    :return: object
    """
    if filepath is None:
        raise IOError('No path supplied')

    if isinstance(filepath, str):
        filepath = Path(filepath)
    if not isinstance(filepath, Path):
        raise ValueError(f'filepath must be an str or Path object, not type {type(filepath)}')

    if filepath.stem == '':
        filepath = Path(str(filepath) + '.pgz')

    with gzip.GzipFile(filepath, 'r') as filein:
        obj = pickle.load(filein)
    return obj


def get_text_file_encoding(filepath):
    """
    Returns the text encoding as a string for a txt file at the given filepath.

    >>> from gender_analysis import common
    >>> from pathlib import Path
    >>> import os

    >>> path=Path(common.BASE_PATH,'testing', 'corpora','sample_novels','texts','hawthorne_scarlet.txt')
    >>> common.get_text_file_encoding(path)
    'UTF-8-SIG'

    Note: For files containing only ascii characters, this function will return 'ascii' even if
    the file was encoded with utf-8

    >>> import os
    >>> from pathlib import Path
    >>> from gender_analysis import common
    >>> text = 'here is an ascii text'
    >>> file_path = Path(common.BASE_PATH, 'example_file.txt')
    >>> with codecs.open(file_path, 'w', 'utf-8') as source:
    ...     source.write(text)
    ...     source.close()
    >>> common.get_text_file_encoding(file_path)
    'ascii'
    >>> file_path = Path(common.BASE_PATH, 'example_file.txt')
    >>> os.remove(file_path)

    :param filepath: str or Path object
    :return: str
    """
    from chardet.universaldetector import UniversalDetector
    detector = UniversalDetector()

    with open(filepath, 'rb') as file:
        for line in file:
            detector.feed(line)
            if detector.done:
                break
        detector.close()
    return detector.result['encoding']


def convert_text_file_to_new_encoding(source_path, target_path, target_encoding):
    """
    Converts a text file in source_path to the specified encoding in target_encoding
    Note: Currently only supports encodings utf-8, ascii and iso-8859-1

    :param source_path: str or Path
    :param target_path: str or Path
    :param target_encoding: str

    >>> from gender_analysis.common import BASE_PATH
    >>> text = ' ¶¶¶¶ here is a test file'
    >>> source_path = Path(BASE_PATH, 'source_file.txt')
    >>> target_path = Path(BASE_PATH, 'target_file.txt')
    >>> with codecs.open(source_path, 'w', 'iso-8859-1') as source:
    ...     source.write(text)
    >>> get_text_file_encoding(source_path)
    'ISO-8859-1'
    >>> convert_text_file_to_new_encoding(source_path, target_path, target_encoding='utf-8')
    >>> get_text_file_encoding(target_path)
    'utf-8'
    >>> import os
    >>> os.remove(source_path)
    >>> os.remove(target_path)

    :return:
    """

    valid_encodings = ['utf-8', 'utf8', 'UTF-8-SIG', 'ascii', 'iso-8859-1', 'ISO-8859-1',
                       'Windows-1252']

    # if the source_path or target_path is a string, turn to Path object.
    if isinstance(source_path, str):
        source_path = Path(source_path)
    if isinstance(target_path, str):
        target_path = Path(target_path)

    # check if source and target encodings are valid
    source_encoding = get_text_file_encoding(source_path)
    if source_encoding not in valid_encodings:
        raise ValueError('convert_text_file_to_new_encoding() only supports the following source '
                         f'encodings: {valid_encodings} but not {source_encoding}.')
    if target_encoding not in valid_encodings:
        raise ValueError('convert_text_file_to_new_encoding() only supports the following target '
                         f'encodings: {valid_encodings} but not {target_encoding}.')

    # print warning if filenames don't end in .txt
    if not source_path.parts[-1].endswith('.txt') or not target_path.parts[-1].endswith('.txt'):
        print(f"WARNING: Changing encoding to {target_encoding} on a file that does not end with "
              f".txt. Source: {source_path}. Target: {target_path}")

    with codecs.open(source_path, 'rU', encoding=source_encoding) as source_file:
        text = source_file.read()
    with codecs.open(target_path, 'w', encoding=target_encoding) as target_file:
        target_file.write(text)


def load_graph_settings(show_grid_lines=True):
    """
    This function sets the seaborn graph settings to the defaults for the project.
    Defaults to displaying gridlines. To remove gridlines, call with False.
    :return:
    """
    show_grid_lines_string = str(show_grid_lines)
    palette = "colorblind"
    style_name = "white"
    background_color = (252/255,245/255,233/255,0.4)
    style_list = {'axes.edgecolor': '.6', 'grid.color': '.9', 'axes.grid': show_grid_lines_string,
                  'font.family': 'serif', 'axes.facecolor':background_color,
                  'figure.facecolor':background_color}
    sns.set_color_codes(palette)
    sns.set_style(style_name, style_list)

    
class MissingMetadataError(Exception):
    """
    Raised when a function that assumes certain metadata is called on a corpus without that
    metadata
    """
    def __init__(self, metadata_fields, message=None):
        self.metadata_fields = metadata_fields
        self.message = message if message else ''

    def __str__(self):
        metadata_string = ''
        for i in range(len(self.metadata_fields)):
            metadata_string += self.metadata_fields[i]
            if i != len(self.metadata_fields) - 1:
                metadata_string += ', '

        return 'This corpus is missing the metadata field(s): ' + metadata_string + '. ' + \
               self.message + ' In order to run this function, you must create a new ' \
                              'metadata csv with (' + metadata_string + ') fields and create a ' \
                                                                        'new Corpus with this csv.'


if __name__ == '__main__':
    from dh_testers.testRunner import main_test
    main_test(import_plus_relative=True)  # this allows for relative calls in the import.
