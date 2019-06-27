import csv
import random
from nltk.tokenize import word_tokenize
from pathlib import Path, PosixPath
from collections import Counter
from os import listdir

from gender_analysis import common
from gender_analysis.document import Document
# from gender_analysis.gutenburg_loader import download_gutenberg_if_not_locally_available


class Corpus(common.FileLoaderMixin):

    """The corpus class is used to load the metadata and full
    texts of all documents in a corpus

    Once loaded, each corpus contains a list of Document objects

    >>> from gender_analysis.corpus import Corpus
    >>> from gender_analysis.common import BASE_PATH
    >>> path = BASE_PATH / 'testing' / 'corpora' / 'sample_novels' / 'texts'
    >>> c = Corpus(path)
    >>> type(c.documents), len(c)
    (<class 'list'>, 100)

    """

    def __init__(self, path_to_files, name=None, csv_path=None, pickle_on_load=False):

        """

        :param path_to_files: Must be either the path to a directory of txt files or an already-pickled corpus
        :param name: Optional name of the corpus, for ease of use and readability
        :param csv_path: Optional path to a csv metadata file
        :param pickle_on_load:
        """

        if isinstance(path_to_files, str):
            path_to_files = Path(path_to_files)
        if not isinstance(path_to_files, Path):
            raise ValueError(f'path_to_files must be a str or Path object, not type {type(path_to_files)}')

        self.name = name
        self.csv_path = csv_path
        self.path_to_files = path_to_files
        self.documents = []

        if self.path_to_files.suffix == '.pgz':
            pickle_data = common.load_pickle(self.path_to_files)
            self.documents = pickle_data.documents
        elif self.path_to_files.suffix == '' and not self.csv_path:
            files = listdir(self.path_to_files)
            for file in files:
                if file.endswith('.txt'):
                    metadata_dict = {'filename': file, 'filepath': self.path_to_files / file}
                    self.documents.append(Document(metadata_dict))
        elif self.csv_path and self.path_to_files.suffix == '':
            self.documents = self._load_documents()
        else:
            raise ValueError(f'path_to_files must lead to a a previously pickled corpus or directory of .txt files')

    def __len__(self):
        """
        For convenience: returns the number of documents in
        the corpus.

        >>> from gender_analysis.corpus import Corpus
        >>> from gender_analysis.common import BASE_PATH
        >>> path = BASE_PATH / 'testing' / 'corpora' / 'sample_novels' / 'texts'
        >>> c = Corpus(path)
        >>> len(c)
        100

        :return: int
        """
        return len(self.documents)

    def __iter__(self):
        """
        Yield each of the documents from the .documents list.

        For convenience.

        >>> from gender_analysis.corpus import Corpus
        >>> from gender_analysis.common import BASE_PATH
        >>> path = BASE_PATH / 'testing' / 'corpora' / 'test_corpus'
        >>> c = Corpus(path)
        >>> docs = []
        >>> for doc in c:
        ...    docs.append(doc)
        >>> len(docs)
        10

        """
        for this_document in self.documents:
            yield this_document

    def __eq__(self, other):
        """
        Returns true if both corpora contain the same documents
        Note: ignores differences in the corpus name as that attribute is not used apart from
        initializing a corpus.
        Presumes the documents to be sorted. (They get sorted by the initializer)

        >>> from gender_analysis.corpus import Corpus
        >>> from gender_analysis.common import BASE_PATH
        >>> path = BASE_PATH / 'testing' / 'corpora' / 'sample_novels' / 'texts'
        >>> sample_corpus = Corpus(path)
        >>> sorted_docs = sorted(sample_corpus.documents[:20])
        >>> sample_corpus.documents = sorted_docs
        >>> corp1 = sample_corpus.clone()
        >>> corp1.documents = corp1.documents[:10]
        >>> corp2 = sample_corpus.clone()
        >>> corp2.documents = corp2.documents[10:]
        >>> sample_corpus == corp1 + corp2
        True
        >>> sample_corpus == Corpus(path) + corp1
        False

        :return: bool
        """

        if not isinstance(other, Corpus):
            raise NotImplementedError("Only a Corpus can be compared to another Corpus.")

        if len(self) != len(other):
            return False

        for i in range(len(self)):
            if self.documents[i] != other.documents[i]:
                return False

        return True

    def __add__(self, other):
        """
        Adds two corpora together and returns a copy of the result
        Note: retains the name of the first corpus

        >>> from gender_analysis.corpus import Corpus
        >>> from gender_analysis.common import BASE_PATH
        >>> path = BASE_PATH / 'testing' / 'corpora' / 'sample_novels' / 'texts'
        >>> sample_corpus = Corpus(path)
        >>> sorted_docs = sorted(sample_corpus.documents[:20])
        >>> sample_corpus.documents = sorted_docs
        >>> corp1 = sample_corpus.clone()
        >>> corp1.documents = corp1.documents[:10]
        >>> corp2 = sample_corpus.clone()
        >>> corp2.documents = corp2.documents[10:]
        >>> sample_corpus == corp1 + corp2
        True

        :return: Corpus
        """
        if not isinstance(other, Corpus):
            raise NotImplementedError("Only a Corpus can be added to another Corpus.")

        output_corpus = self.clone()
        for document in other:
            output_corpus.documents.append(document)
        output_corpus.documents = sorted(output_corpus.documents)

        return output_corpus

    def clone(self):
        """
        Return a copy of this Corpus

        >>> from gender_analysis.corpus import Corpus
        >>> from gender_analysis.common import BASE_PATH
        >>> path = BASE_PATH / 'testing' / 'corpora' / 'sample_novels' / 'texts'
        >>> sample_corpus = Corpus(path)
        >>> corpus_copy = sample_corpus.clone()
        >>> len(corpus_copy) == len(sample_corpus)
        True

        :return: Corpus
        """
        from copy import copy
        return copy(self)

    def _load_documents(self):
        documents = []

        try:
            csv_file = self.load_file(self.csv_path)
        except FileNotFoundError:
            err = "Could not find the metadata csv file for the "
            err += f"'{self.name}' corpus in the expected location "
            err += f"({self.csv_path})."
            raise FileNotFoundError(err)
        csv_reader = csv.DictReader(csv_file)

        for document_metadata in csv_reader:
            document_metadata['name'] = self.name
            document_metadata['filepath'] = self.path_to_files / document_metadata['filename']
            this_document = Document(document_metadata)
            documents.append(this_document)

        return sorted(documents)

    def count_authors_by_gender(self, gender):
        """
        This function returns the number of authors in the corpus with the specified gender. NOTE: there must be an
        'author_gender' field in the metadata field of all documents.

        >>> from gender_analysis.corpus import Corpus
        >>> from gender_analysis.common import BASE_PATH
        >>> path = BASE_PATH / 'testing' / 'corpora' / 'test_corpus'
        >>> path_to_csv = BASE_PATH / 'testing' / 'corpora' / 'test_corpus' / 'test_corpus.csv'
        >>> c = Corpus(path, csv_path=path_to_csv)
        >>> c.count_authors_by_gender('female')
        7


        :rtype: int
        """
        count = 0
        for document in self.documents:
            try:
                if document.author_gender.lower() == gender.lower():
                    count += 1
            except AttributeError:
                raise AttributeError(f'{document.filename} does not have an \'author_gender\' metadata field')

        return count

    def filter_by_gender(self, gender):
        """
        Return a new Corpus object that contains only authors whose gender
        matches the given parameter.

        # >>> from gender_analysis.corpus import Corpus
        # >>> from gender_analysis.common import BASE_PATH
        # >>> path = BASE_PATH / 'testing' / 'corpora' / 'sample_novels' / 'texts'
        # >>> c = Corpus(path)
        # >>> female_corpus = c.filter_by_gender('female')
        # >>> len(female_corpus)
        # 39
        # >>> female_corpus.documents[0].title
        # 'The Indiscreet Letter'
        #
        # >>> male_corpus = c.filter_by_gender('male')
        # >>> len(male_corpus)
        # 59
        #
        # >>> male_corpus.documents[0].title
        # 'Lisbeth Longfrock'

        :param gender: gender name
        :return: Corpus
        """

        return self.subcorpus('author_gender', gender)

    def get_wordcount_counter(self):
        """
        This function returns a Counter telling how many times a word appears in an entire
        corpus

        >>> from gender_analysis.corpus import Corpus
        >>> from gender_analysis.common import BASE_PATH
        >>> path = BASE_PATH / 'testing' / 'corpora' / 'sample_novels' / 'texts'
        >>> csvpath = BASE_PATH / 'testing' / 'corpora' / 'sample_novels' / 'sample_novels.csv'
        >>> c = Corpus(path, csv_path=csvpath)
        >>> c.get_wordcount_counter()['fire']
        2269

        """
        corpus_counter = Counter()
        for current_document in self.documents:
            document_counter = current_document.get_wordcount_counter()
            corpus_counter += document_counter
        return corpus_counter

    def get_corpus_metadata(self):
        """
        This function returns a sorted list of all metadata fields
        in the corpus as strings. This is different from the get_metadata_fields;
        this returns the fields which are specific to the corpus it is being called on.
        >>> from gender_analysis.corpus import Corpus
        >>> from gender_analysis.common import BASE_PATH
        >>> path = BASE_PATH / 'testing' / 'corpora' / 'sample_novels' / 'texts'
        >>> c = Corpus(path)
        >>> c.get_corpus_metadata()
        ['filename', 'filepath']

        :return: list
        """
        metadata_fields = set()
        for document in self.documents:
            for field in document.members:
                metadata_fields.add(field)
        return sorted(list(metadata_fields))

    def get_field_vals(self, field):
        """
        This function returns a sorted list of all values for a
        particular metadata field as strings.

        >>> from gender_analysis.corpus import Corpus
        >>> from gender_analysis.common import BASE_PATH
        >>> path = BASE_PATH / 'testing' / 'corpora' / 'sample_novels' / 'texts'
        >>> csvpath = BASE_PATH / 'testing' / 'corpora' / 'sample_novels' / 'sample_novels.csv'
        >>> c = Corpus(path, name='sample_novels', csv_path=csvpath)
        >>> c.get_field_vals('name')
        ['sample_novels']

        :param field: str
        :return: list
        """
        metadata_fields = self.get_corpus_metadata()

        if field not in metadata_fields:
            raise ValueError(
                f'\'{field}\' is not a valid metadata field for this corpus'
            )

        values = set()
        for document in self.documents:
            values.add(getattr(document, field))

        return sorted(list(values))

    def subcorpus(self, metadata_field, field_value):
        """
        This method takes a metadata field and value of that field and returns
        a new Corpus object which includes the subset of documents in the original
        Corpus that have the specified value for the specified field.

        Supported metadata fields are 'author', 'author_gender', 'name',
        'country_publication', 'date'

        >>> from gender_analysis.corpus import Corpus
        >>> from gender_analysis.common import BASE_PATH
        >>> path = BASE_PATH / 'testing' / 'corpora' / 'sample_novels' / 'texts'
        >>> csvpath = BASE_PATH / 'testing' / 'corpora' / 'sample_novels' / 'sample_novels.csv'
        >>> corp = Corpus(path, csv_path=csvpath)
        >>> female_corpus = corp.subcorpus('author_gender','female')
        >>> len(female_corpus)
        39
        >>> female_corpus.documents[0].title
        'The Indiscreet Letter'

        >>> male_corpus = corp.subcorpus('author_gender','male')
        >>> len(male_corpus)
        59
        >>> male_corpus.documents[0].title
        'Lisbeth Longfrock'

        >>> eighteen_fifty_corpus = corp.subcorpus('date','1850')
        >>> len(eighteen_fifty_corpus)
        1
        >>> eighteen_fifty_corpus.documents[0].title
        'The Scarlet Letter'

        >>> jane_austen_corpus = corp.subcorpus('author','Austen, Jane')
        >>> len(jane_austen_corpus)
        2
        >>> jane_austen_corpus.documents[0].title
        'Emma'

        >>> england_corpus = corp.subcorpus('country_publication','England')
        >>> len(england_corpus)
        51
        >>> england_corpus.documents[0].title
        'Flatland'

        :param metadata_field: str
        :param field_value: str
        :return: Corpus
        """

        supported_metadata_fields = self.get_corpus_metadata()
        
        if metadata_field not in supported_metadata_fields:
            raise ValueError(
                f'Metadata field must be {", ".join(supported_metadata_fields)} '
                + f'but not {metadata_field}.')

        corpus_copy = self.clone()
        corpus_copy.documents = []

        # adds documents to corpus_copy
        if metadata_field == 'date':
            for this_document in self.documents:
                if this_document.date == int(field_value):
                    corpus_copy.documents.append(this_document)
        else:
            for this_document in self.documents:
                try:
                    this_value = getattr(this_document, metadata_field, None)
                    if this_value is not None and this_value.lower() == field_value.lower():
                        corpus_copy.documents.append(this_document)
                except AttributeError:
                    continue

        # if not corpus_copy:
        #     # displays for possible errors in field.value
        #     err = f'This corpus is empty. You may have mistyped something.'
        #     raise AttributeError(err)

        return corpus_copy

    def multi_filter(self, characteristic_dict):
        """
        Returns a copy of the corpus, but with only the documents that fulfill the metadata parameters passed in by
        characteristic_dict. Multiple metadata keys can be searched at one time, provided that the metadata is
        available for the documents in the corpus.


        :param characteristic_dict: Dictionary of metadata keys and search terms as
        :return:

        >>> from gender_analysis.corpus import Corpus
        >>> from gender_analysis.common import BASE_PATH
        >>> path = BASE_PATH / 'testing' / 'corpora' / 'sample_novels' / 'texts'
        >>> path_to_csv = BASE_PATH / 'testing' / 'corpora' / 'sample_novels' / 'sample_novels.csv'
        >>> c = Corpus(path, csv_path=path_to_csv)
        >>> corpus_filter = {'author_gender': 'male'}
        >>> len(c.multi_filter(corpus_filter))
        59

        >>> corpus_filter['filename'] = 'aanrud_longfrock.txt'
        >>> len(c.multi_filter(corpus_filter))
        1
        """
        supported_metadata_fields = self.get_corpus_metadata()

        corpus_copy = self.clone()
        corpus_copy.documents = []

        for metadata_field in characteristic_dict:
            if metadata_field not in supported_metadata_fields:
                raise ValueError(
                    f'Metadata field must be {", ".join(supported_metadata_fields)} '
                    + f'but not {metadata_field}.')

        for this_document in self.documents:
            add_document = True
            for metadata_field in characteristic_dict:
                if metadata_field == 'date':
                    if this_document.date != int(characteristic_dict['date']):
                        add_document = False
                else:
                    if getattr(this_document, metadata_field) != characteristic_dict[metadata_field]:
                        add_document = False
            if add_document:
                corpus_copy.documents.append(this_document)

        if not corpus_copy:
            # displays for possible errors in field.value
            err = f'This corpus is empty. You may have mistyped something.'
            raise AttributeError(err)

        return corpus_copy

    def get_document(self, metadata_field, field_val):
        """
        Returns a specific Document object from self.documents that has metadata matching field_val for
        metadata_field.  Otherwise raises a ValueError.
        N.B. This function will only return the first document in the self.documents (which is sorted as
        defined by the Document.__lt__ function).  It should only be used if you're certain there is
        only one match in the Corpus or if you're not picky about which Document you get.  If you want
        more selectivity use get_document_multiple_fields, or if you want multiple documents use the subcorpus
        function.

        >>> from gender_analysis.corpus import Corpus
        >>> from gender_analysis.common import BASE_PATH
        >>> path = BASE_PATH / 'testing' / 'corpora' / 'sample_novels' / 'texts'
        >>> csvpath = BASE_PATH / 'testing' / 'corpora' / 'sample_novels' / 'sample_novels.csv'
        >>> c = Corpus(path, csv_path=csvpath)
        >>> c.get_document("author", "Dickens, Charles")
        <Document (dickens_twocities)>
        >>> c.get_document("date", '1857')
        <Document (bronte_professor)>
        >>> try:
        ...     c.get_document("meme_quality", "over 9000")
        ... except AttributeError as exception:
        ...     print(exception)
        Metadata field meme_quality invalid for this corpus

        :param metadata_field: str
        :param field_val: str/int
        :return: Document
        """

        if metadata_field not in get_metadata_fields(self.name):
            raise AttributeError(f"Metadata field {metadata_field} invalid for this corpus")

        if (metadata_field == "date" or metadata_field == "gutenberg_id"):
            field_val = int(field_val)

        for document in self.documents:
            if getattr(document, metadata_field) == field_val:
                return document

        raise ValueError("Document not found")

    def get_sample_text_passages(self, expression, no_passages):
        """
        Returns a specified number of example passages that include a certain expression.

        >>> from gender_analysis.corpus import Corpus
        >>> from gender_analysis.common import BASE_PATH
        >>> filepath = BASE_PATH / 'testing' / 'corpora' / 'sample_novels' / 'texts'
        >>> corpus = Corpus(filepath)
        >>> results = corpus.get_sample_text_passages('he cried', 2)
        >>> 'he cried' in results[0][1]
        True
        >>> 'he cried' in results[1][1]
        True
        """
        count = 0
        output = []
        phrase = word_tokenize(expression)
        random.seed(expression)
        random_documents = self.documents.copy()
        random.shuffle(random_documents)

        for document in random_documents:
            if count >= no_passages:
                break
            current_document = document.get_tokenized_text()
            for index in range(len(current_document)):
                if current_document[index] == phrase[0]:
                    if current_document[index:index+len(phrase)] == phrase:
                        passage = " ".join(current_document[index-20:index+len(phrase)+20])
                        output.append((document.filename, passage))
                        count += 1

        '''
        random.shuffle(output)
        print_count = 0
        for entry in output:
            if print_count == no_passages:
                break
            print_count += 1
            print(entry)
        '''
        if len(output) <= no_passages:
            return output
        return output[:no_passages]

    def get_document_multiple_fields(self, metadata_dict):
        """
        Returns a specific Document object from self.documents that has metadata that matches a partial
        dict of metadata.  Otherwise raises a ValueError.
        N.B. This method will only return the first document in the self.documents (which is sorted as
        defined by the Document.__lt__ function).  It should only be used if you're certain there is
        only one match in the Corpus or if you're not picky about which Document you get.  If you want
        multiple documents use the subcorpus function.

        >>> from gender_analysis.corpus import Corpus
        >>> from gender_analysis.common import BASE_PATH
        >>> path = BASE_PATH / 'testing' / 'corpora' / 'sample_novels' / 'texts'
        >>> csvpath = BASE_PATH / 'testing' / 'corpora' / 'sample_novels' / 'sample_novels.csv'
        >>> c = Corpus(path, csv_path=csvpath)
        >>> c.get_document_multiple_fields({"author": "Dickens, Charles", "author_gender": "male"})
        <Document (dickens_twocities)>
        >>> c.get_document_multiple_fields({"author": "Chopin, Kate", "title": "The Awakening"})
        <Document (chopin_awakening)>

        :param metadata_dict: dict
        :return: Document
        """

        for field in metadata_dict.keys():
            if field not in get_metadata_fields(self.name):
                raise AttributeError(f"Metadata field {field} invalid for this corpus")

        for document in self.documents:
            match = True
            for field, val in metadata_dict.items():
                if getattr(document, field, None) != val:
                    match = False
            if match:
                return document

        raise ValueError("Document not found")


def get_metadata_fields(name):
    """
    Gives a list of all metadata fields for corpus
    >>> from gender_analysis import corpus
    >>> corpus.get_metadata_fields('gutenberg')
    ['gutenberg_id', 'author', 'date', 'title', 'country_publication', 'author_gender', 'subject', 'corpus_name', 'notes']

    :param: name: str
    :return: list
    """
    return common.METADATA_LIST


if __name__ == '__main__':
    from dh_testers.testRunner import main_test
    main_test()
